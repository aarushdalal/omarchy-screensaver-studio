/*
 * Omarchy Screensaver - Ultra Low-Latency Real-Time Audio Spectrum Analyzer
 *
 * Connects directly to PipeWire / PulseAudio via libpulse-simple.
 * Computes 36 logarithmically-spaced Goertzel frequency filters at ~60 FPS
 * with sub-10ms beat reactivity, dynamic AGC, and peak hold physics.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <pthread.h>
#include <pulse/simple.h>
#include <pulse/error.h>

#define CHUNK_SIZE 368
#define SAMPLE_RATE 22050
#define MAX_BANDS 64

typedef struct {
    double coeff;
    double cos_w;
    double sin_w;
    double eq_boost;
} Filter;

static int g_num_bands = 36;
static Filter g_filters[MAX_BANDS];
static float g_smooth[MAX_BANDS];
static float g_peaks[MAX_BANDS];
static float g_peak_speeds[MAX_BANDS];
static double g_rolling_max = 50.0;

static volatile int g_running = 0;
static volatile int g_has_signal = 0;
static pthread_t g_thread;
static pthread_mutex_t g_mutex = PTHREAD_MUTEX_INITIALIZER;
static float g_latest_bands[MAX_BANDS];
static float g_latest_peaks[MAX_BANDS];

static void init_filters(int num_bands) {
    g_num_bands = (num_bands > MAX_BANDS) ? MAX_BANDS : (num_bands < 8 ? 8 : num_bands);
    double f_min = 40.0;
    double f_max = 12500.0;
    double factor = pow(f_max / f_min, 1.0 / (g_num_bands - 1));

    for (int b = 0; b < g_num_bands; b++) {
        double freq = f_min * pow(factor, b);
        int k = (int)(0.5 + (CHUNK_SIZE * freq / SAMPLE_RATE));
        if (k < 1) k = 1;
        if (k > CHUNK_SIZE / 2) k = CHUNK_SIZE / 2;
        double omega = (2.0 * M_PI * k) / CHUNK_SIZE;
        g_filters[b].coeff = 2.0 * cos(omega);
        g_filters[b].cos_w = cos(omega);
        g_filters[b].sin_w = sin(omega);
        
        // Equalization weighting across spectrum
        g_filters[b].eq_boost = 1.0 + (b * 0.045);
        if (b < 10) {
            // Punchy bass boost for kick drums and 808s
            g_filters[b].eq_boost += (10 - b) * 0.075;
        }
        g_smooth[b] = 0.0f;
        g_peaks[b] = 0.0f;
        g_peak_speeds[b] = 0.0f;
        g_latest_bands[b] = 0.0f;
        g_latest_peaks[b] = 0.0f;
    }
}

static void detect_target(char *dest, size_t maxlen) {
    strncpy(dest, "easyeffects_sink.monitor", maxlen - 1);
    dest[maxlen - 1] = '\0';
    FILE *fp = popen("pactl list short sinks 2>/dev/null", "r");
    if (fp) {
        char line[256];
        int found_ee = 0;
        while (fgets(line, sizeof(line), fp)) {
            if (strstr(line, "easyeffects_sink")) {
                found_ee = 1;
                break;
            }
        }
        pclose(fp);
        if (!found_ee) {
            strncpy(dest, "@DEFAULT_MONITOR@", maxlen - 1);
        }
    }
}

static void *audio_worker(void *arg) {
    (void)arg;
    static const pa_sample_spec ss = {
        .format = PA_SAMPLE_S16LE,
        .rate = SAMPLE_RATE,
        .channels = 1
    };
    static const pa_buffer_attr ba = {
        .maxlength = (uint32_t) -1,
        .tlength = (uint32_t) -1,
        .prebuf = (uint32_t) -1,
        .minreq = (uint32_t) -1,
        .fragsize = CHUNK_SIZE * sizeof(int16_t)
    };

    char target[128];
    detect_target(target, sizeof(target));

    int error = 0;
    pa_simple *s = pa_simple_new(
        NULL,
        "OmarchyVisualizerEngine",
        PA_STREAM_RECORD,
        target,
        "Screensaver Spectrum",
        &ss,
        NULL,
        &ba,
        &error
    );

    if (!s && strcmp(target, "@DEFAULT_MONITOR@") != 0) {
        s = pa_simple_new(
            NULL,
            "OmarchyVisualizerEngine",
            PA_STREAM_RECORD,
            "@DEFAULT_MONITOR@",
            "Screensaver Spectrum",
            &ss,
            NULL,
            &ba,
            &error
        );
    }

    if (!s) {
        fprintf(stderr, "[omarchy-audio] Failed to connect to pulse monitor: %s\n", pa_strerror(error));
        return NULL;
    }

    int16_t samples[CHUNK_SIZE];
    double mags[MAX_BANDS];

    while (g_running) {
        if (pa_simple_read(s, samples, sizeof(samples), &error) < 0) {
            usleep(15000);
            continue;
        }

        int max_amp = 0;
        for (int i = 0; i < CHUNK_SIZE; i++) {
            int a = abs(samples[i]);
            if (a > max_amp) max_amp = a;
        }

        // Noise gate: silence when lower than background floor
        if (max_amp < 12) {
            pthread_mutex_lock(&g_mutex);
            g_has_signal = 0;
            for (int b = 0; b < g_num_bands; b++) {
                g_smooth[b] *= 0.65f;
                if (g_smooth[b] < 0.005f) g_smooth[b] = 0.0f;
                g_latest_bands[b] = g_smooth[b];
                
                // Peak gravity decay
                g_peak_speeds[b] += 0.035f;
                g_peaks[b] = fmaxf(0.0f, g_peaks[b] - g_peak_speeds[b]);
                g_latest_peaks[b] = g_peaks[b];
            }
            pthread_mutex_unlock(&g_mutex);
            continue;
        }

        double frame_max = 1.0;
        for (int b = 0; b < g_num_bands; b++) {
            double q0 = 0.0, q1 = 0.0, q2 = 0.0;
            double coeff = g_filters[b].coeff;
            for (int i = 0; i < CHUNK_SIZE; i++) {
                q0 = coeff * q1 - q2 + samples[i];
                q2 = q1;
                q1 = q0;
            }
            double real = q1 - q2 * g_filters[b].cos_w;
            double imag = q2 * g_filters[b].sin_w;
            double mag = (sqrt(real * real + imag * imag) / CHUNK_SIZE) * g_filters[b].eq_boost;
            mags[b] = mag;
            if (mag > frame_max) frame_max = mag;
        }

        // Automatic Gain Control with fast rise and smooth fall
        if (frame_max > g_rolling_max) {
            g_rolling_max = g_rolling_max * 0.45 + frame_max * 0.55;
        } else {
            g_rolling_max = fmax(15.0, g_rolling_max * 0.985);
        }

        pthread_mutex_lock(&g_mutex);
        g_has_signal = 1;
        for (int b = 0; b < g_num_bands; b++) {
            double ratio = fmin(1.0, fmax(0.0, mags[b] / fmax(10.0, g_rolling_max)));
            float val = (float)pow(ratio, 0.72);

            // Instant attack on beat spikes, natural exponential release
            if (val > g_smooth[b]) {
                g_smooth[b] = val;
            } else {
                g_smooth[b] = g_smooth[b] * 0.65f + val * 0.35f;
            }
            g_latest_bands[b] = g_smooth[b];

            // Peak tracking with gravity physics
            if (g_smooth[b] > g_peaks[b]) {
                g_peaks[b] = g_smooth[b];
                g_peak_speeds[b] = 0.0f;
            } else {
                g_peak_speeds[b] += 0.024f;
                g_peaks[b] = fmaxf(0.0f, g_peaks[b] - g_peak_speeds[b]);
            }
            g_latest_peaks[b] = g_peaks[b];
        }
        pthread_mutex_unlock(&g_mutex);
    }

    pa_simple_free(s);
    return NULL;
}

int audio_spectrum_start(int num_bands) {
    if (g_running) return 1;
    init_filters(num_bands);
    g_running = 1;
    if (pthread_create(&g_thread, NULL, audio_worker, NULL) != 0) {
        g_running = 0;
        return 0;
    }
    return 1;
}

void audio_spectrum_stop(void) {
    if (!g_running) return;
    g_running = 0;
    pthread_join(g_thread, NULL);
}

int audio_spectrum_get(float *out_bands, float *out_peaks, int count) {
    pthread_mutex_lock(&g_mutex);
    int n = (count < g_num_bands) ? count : g_num_bands;
    for (int i = 0; i < n; i++) {
        if (out_bands) out_bands[i] = g_latest_bands[i];
        if (out_peaks) out_peaks[i] = g_latest_peaks[i];
    }
    int sig = g_has_signal;
    pthread_mutex_unlock(&g_mutex);
    return sig;
}
