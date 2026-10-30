# System Cockpit — what it shows

The live telemetry refresh is about **0.5 seconds**, with smoothly eased needles between samples. SMART lifetime data updates separately in the background; lifetime I/O-command totals are an explicitly refreshed snapshot.

The cockpit is arranged from broad system load at the top to detailed storage and runtime readings at the bottom. All colours follow your selected desktop palette, and the larger text scales with the whole layout.

## Startup: the car-style instrument check

Whenever the system screensaver opens, all seven round instruments sweep from zero to 100, return to zero, then ease into their real readings. The heading says **INSTRUMENT CHECK** while this happens and switches to **LIVE TELEMETRY** afterward. The sweep is an animation, not a temporary hardware reading. It runs in ordinary screensaver and ambient study mode.

## 1. Core load — three main gauges

| Instrument | Meaning | Supporting display |
|---|---|---|
| CPU | Combined processor utilization | Clock frequency, temperature and a bar for each logical CPU; large CPU counts are grouped to fit. |
| GPU | Graphics-engine utilization, when a supported sensor is available | Graphics clock, temperature and VRAM allocation bar. |
| Memory | Physical RAM in use | Used/total RAM, available RAM and swap allocation. |

The needle is the smoothed current value. The small outer marker holds a recent peak for three seconds before it decays toward the current value. The moving rim glint is decorative and is separate from the measurement.

## 2. Capacity and thermals — four smaller gauges

- **CPU temperature:** current sensor reading on a labelled 0–100°C display scale. This is a display scale, not a device-specific critical-temperature limit.
- **Root storage:** used space on the root filesystem, with available space beneath it.
- **Load / capacity:** one-minute Linux load average divided by the logical CPU count. This differs from CPU utilization and can exceed 100%; the arc stops at its maximum while the text preserves the value.
- **Battery / power source:** battery charge and charge state, or an AC/no-battery indication when no battery is installed.

Unavailable sensors say N/A rather than showing invented measurements.

## 3. Activity — processor and network histories

The left chart shows CPU as a solid line and GPU as a dashed line. The right chart shows received traffic as a solid line and sent traffic as a dashed line. This distinction also works with monochrome palettes. The network graph uses an explicitly labelled automatic scale, not a claimed percentage of your connection speed. Rates aggregate non-loopback interfaces.

The charts show approximately the preceding minute, with a subtle scan line and pulsing current endpoints. The display targets 30 FPS while system samples arrive about twice a second; actual rendering performance depends on the machine and resolution.

## 4. Detailed readings

### Power & electrical

CPU/GPU allocation and DRAM calculations are labelled **est.** These are models rather than independent rail measurements. A readable hardware power sensor is shown separately. Battery voltage/current/power and AC connection state complete this panel.

### Storage & memory I/O

| Row | Meaning |
|---|---|
| ROOT / TEMP | Root-filesystem capacity and available drive-temperature sensor. |
| TODAY READ | Bytes read during the tracked portion of the current local calendar day. |
| TODAY WRITE | Bytes written during the tracked portion of the current local calendar day. |
| READ NOW | Current read throughput and read operations per second. |
| WRITE NOW | Current write throughput and write operations per second. |
| SSD LIFE R | The NVMe controller's lifetime host data-read counter from SMART. |
| SSD LIFE W | The NVMe controller's lifetime host data-written counter from SMART. |
| SSD LIFE IOs | Lifetime host read commands plus host write commands from the explicit SMART snapshot. This is a command count, not a byte count or the Linux counter since boot. |
| SSD HEALTH | Estimated endurance remaining: `max(0, 100 − percentage used)` from the drive's wear indicator. It is an endurance estimate, not a prediction of the failure date or a substitute for the drive's critical-warning state. |
| MEM / VM | Available RAM and virtual-memory page-allocation/free activity. Page activity is not a physical memory-bus bandwidth benchmark. |

Sizes use binary units (KiB, MiB, GiB, TiB). Daily totals are kept separately from lifetime SMART totals. They persist across launches and handle counter resets and reboot boundaries. **An asterisk marks partial daily coverage:** on first use the tracker can recover the current boot's counters only when that boot started today; if tracking begins after an unobserved midnight, it starts a new baseline instead of assigning earlier days' traffic to today. It cannot reconstruct missing history. State is retained in `~/.config/omarchy-screensaver/daily-io.json`.

Lifetime byte/wear readings are refreshed through UDisks in the background. The normal screensaver never prompts for administrator credentials. UDisks does not expose lifetime host-command counts on every version; refresh that optional snapshot explicitly with:

```bash
omarchy-screensaver-smart-refresh
```

This installs the official `smartmontools` package if needed, then asks the system for a read-only SMART report. The system may request authentication. Only the device name, refresh time and read/write command counters are cached in `~/.config/omarchy-screensaver/smart-cache.json`; the row is marked as a snapshot. No drive contents or identifying SMART fields are saved. Do not reuse these two runtime-state files after moving the configuration to a different physical SSD; start fresh baselines instead.

The SMART field meanings follow the [UDisks NVMe controller reference](https://storaged.org/udisks/docs/gdbus-org.freedesktop.UDisks2.NVMe.Controller.html).

### Runtime & resource pressure

Kernel version, load averages, runnable/total tasks, governor and uptime sit in the right-hand panel.

**PRESSURE 10s** is the clearer label for **PSI 10s %**. PSI means *Pressure Stall Information*. Each CPU/MEM/I/O percentage is the recent ten-second trend for time when at least one task was stalled on that resource (`some avg10`). It measures waiting, not utilization. For example, CPU utilization can be high while memory pressure remains near zero. See the [Linux kernel PSI reference](https://docs.kernel.org/accounting/psi.html).

## Controls

Open `omarchy-menu-screensaver`, type **System Cockpit**, then press Enter. Selection applies directly, including to a running display. **Preview Screensavers** provides a temporary preview without selecting a mode. **Follow Desktop Colours** enables automatic palette following. Your existing ambient-study and visualizer shortcuts are retained.
