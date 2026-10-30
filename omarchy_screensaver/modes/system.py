"""System Cockpit: animated instruments, headroom, activity and measured pressure."""
import math
import os
import time
from gi.repository import Pango
import cairo
from .base import BaseMode
from .studio import smooth_path
from ..theme import with_alpha


class SystemDashboardMode(BaseMode):
    """Seven instruments with a stable hierarchy and theme-derived colours."""
    target_fps = 30
    CANVAS = (1600, 1000)

    def __init__(self, theme, config, monitor_index=0):
        super().__init__(theme, config, monitor_index)
        try:
            self.startup_delay = max(0, min(5, float(os.environ.get('OMARCHY_SCREENSAVER_STARTUP_DELAY', '0'))))
        except ValueError:
            self.startup_delay = 0
        self.metrics = None
        self.fade_in = 0.0
        self.values = {key: 0.0 for key in ('cpu', 'gpu', 'mem', 'temp', 'disk', 'load', 'battery')}
        self.peaks = {key: [0.0, 0.0] for key in ('cpu', 'gpu', 'mem')}
        self.cores = []
        self._cached_sec = -1
        self._clock = self._date = ''

    def update(self, dt, metrics, media_info):
        super().update(dt, metrics, media_info)
        self.metrics = metrics
        self.fade_in = min(1.0, self.fade_in + max(0, dt) * 1.2)
        if metrics is None:
            return
        targets = {'cpu': metrics.cpu_percent, 'gpu': metrics.gpu_percent,
                   'mem': metrics.mem_percent, 'temp': metrics.cpu_temp_c,
                   'disk': metrics.disk_percent, 'load': metrics.load_1m_percent,
                   'battery': metrics.battery_percent}
        blend = 1 - math.exp(-max(0, dt) * 5.0)
        for key, value in targets.items():
            value = float(value)
            value = max(0, value) if math.isfinite(value) else 0
            self.values[key] += (value - self.values[key]) * blend
        for key, peak in self.peaks.items():
            value = min(100, self.values[key])
            if value >= peak[0]:
                peak[:] = value, 3.0
            else:
                peak[1] = max(0, peak[1] - dt)
                if not peak[1]:
                    peak[0] = max(value, peak[0] - max(0, dt) * 8)
        core_values = getattr(metrics, 'cpu_per_core', [])
        if len(self.cores) != len(core_values):
            self.cores = list(core_values)
        else:
            for i, value in enumerate(core_values):
                self.cores[i] += (value - self.cores[i]) * blend

    def instrument_value(self, actual):
        """A clearly labelled startup sweep, then a smooth handover to real data."""
        t = max(0, self.time - self.startup_delay)
        ease = lambda x: x * x * (3 - 2 * x)
        if t < .9:
            return 100 * ease(t / .9)
        if t < 1.15:
            return 100.0
        if t < 2.05:
            return 100 * (1 - ease((t - 1.15) / .9))
        if t < 2.35:
            return 0.0
        if t < 3.15:
            return actual * ease((t - 2.35) / .8)
        return actual

    @staticmethod
    def _bytes(value):
        if value is None:
            return 'Unavailable'
        for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'):
            if value < 1024 or unit == 'PiB':
                return f'{value:.2f} {unit}'
            value /= 1024

    def _text(self, cr, text, x, y, size=12, role='body', align='left', width=None):
        colors = {'body': self.theme.foreground, 'muted': self.theme.dark_foreground,
                  'accent': self.theme.accent, 'secondary': self.theme.secondary}
        alpha = self.fade_in * self.luminance_factor
        if role == 'muted':
            alpha *= 0.80
        return self.draw_text(cr, text, x, y, self.FONT_MONO, size,
                              with_alpha(colors[role], alpha), align=align,
                              weight=Pango.Weight.BOLD if role == 'accent' else Pango.Weight.NORMAL,
                              max_width=width)

    def _card(self, cr, x, y, w, h):
        self.draw_rounded_rect(cr, x, y, w, h, 16)
        cr.set_source_rgba(*with_alpha(self.theme.surface, 0.24 * self.fade_in))
        cr.fill_preserve()
        cr.set_source_rgba(*with_alpha(self.theme.accent, 0.15 * self.fade_in))
        cr.set_line_width(0.9)
        cr.stroke()

    def _section(self, cr, number, title, y, hint=''):
        self._text(cr, number, 64, y, 11.5, 'accent')
        self._text(cr, title, 98, y, 11.5, 'muted')
        if hint:
            self._text(cr, hint, 1536, y, 10, 'muted', 'right')

    def _ring(self, cr, cx, cy, radius, value, color, peak=None, lively=True):
        start, span = math.pi * 0.75, math.pi * 1.5
        end = start + span * min(100, max(0, value)) / 100
        fade = self.fade_in * self.luminance_factor
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.new_path(); cr.arc(cx, cy, radius, start, start + span)
        cr.set_source_rgba(*with_alpha(self.theme.accent, 0.15 * fade))
        cr.set_line_width(5); cr.stroke()
        for tick in range(21):
            angle = start + span * tick / 20
            inner = radius - (9 if tick % 5 == 0 else 5)
            cr.move_to(cx + math.cos(angle) * inner, cy + math.sin(angle) * inner)
            cr.line_to(cx + math.cos(angle) * (radius - 2), cy + math.sin(angle) * (radius - 2))
        cr.set_source_rgba(*with_alpha(self.theme.foreground, 0.18 * fade))
        cr.set_line_width(1); cr.stroke()
        if value > 0.1:
            cr.new_path(); cr.arc(cx, cy, radius, start, end)
            cr.set_source_rgba(*with_alpha(color, 0.12 * fade)); cr.set_line_width(12); cr.stroke()
            cr.new_path(); cr.arc(cx, cy, radius, start, end)
            cr.set_source_rgba(*with_alpha(color, 0.88 * fade)); cr.set_line_width(4.3); cr.stroke()
            # A short needle rides the true value; it never sweeps over the numerals.
            cr.move_to(cx + math.cos(end) * (radius - 13), cy + math.sin(end) * (radius - 13))
            cr.line_to(cx + math.cos(end) * (radius + 5), cy + math.sin(end) * (radius + 5))
            cr.set_source_rgba(*with_alpha(self.theme.foreground, fade))
            cr.set_line_width(2); cr.stroke()
        if peak is not None:
            angle = start + span * min(100, peak) / 100
            cr.move_to(cx + math.cos(angle) * (radius + 10), cy + math.sin(angle) * (radius + 10))
            cr.line_to(cx + math.cos(angle) * (radius + 17), cy + math.sin(angle) * (radius + 17))
            cr.set_source_rgba(*with_alpha(color, 0.45 * fade)); cr.set_line_width(2); cr.stroke()
        if lively:
            # Quiet rotating rim glint, visually distinct from the measurement needle.
            angle = self.time * 0.22 + self.monitor_index
            cr.new_path(); cr.arc(cx, cy, radius * 0.78, angle, angle + 0.3)
            cr.set_source_rgba(*with_alpha(color, 0.18 * fade)); cr.set_line_width(1); cr.stroke()

    def _bar(self, cr, x, y, w, value, color):
        cr.set_line_width(4); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(x, y); cr.line_to(x + w, y)
        cr.set_source_rgba(*with_alpha(self.theme.accent, 0.12 * self.fade_in)); cr.stroke()
        amount = min(1, max(0, value / 100))
        if amount:
            cr.move_to(x, y); cr.line_to(x + w * amount, y)
            cr.set_source_rgba(*with_alpha(color, 0.65 * self.fade_in)); cr.stroke()

    @staticmethod
    def _rate(value):
        value = max(0, value)
        for unit in ('B/s', 'KB/s', 'MB/s', 'GB/s'):
            if value < 1024 or unit == 'GB/s':
                return f'{value:.1f} {unit}'
            value /= 1024

    def _plot(self, cr, x, y, w, h, series, maximum):
        cr.save(); cr.rectangle(x - 2, y - 6, w + 4, h + 12); cr.clip()
        for fraction in (0, .5, 1):
            cr.move_to(x, y + fraction * h); cr.line_to(x + w, y + fraction * h)
        cr.set_source_rgba(*with_alpha(self.theme.accent, .10 * self.fade_in))
        cr.set_line_width(.8); cr.stroke()
        for index, (data, color) in enumerate(series):
            data = list(data)[-120:] or [0, 0]
            if len(data) == 1:
                data = data * 2
            points = [(x + i * w / (len(data) - 1), y + h * (1 - min(1, max(0, v / max(1, maximum)))))
                      for i, v in enumerate(data)]
            smooth_path(cr, points)
            cr.set_source_rgba(*with_alpha(color, .75 * self.fade_in))
            cr.set_line_width(1.8 if index == 0 else 1.3)
            cr.set_dash([] if index == 0 else [5, 4]); cr.stroke(); cr.set_dash([])
            px, py = points[-1]
            cr.new_path(); cr.arc(px, py, 3.5 + math.sin(self.time * 1.5) * .5, 0, math.tau)
            cr.set_source_rgba(*with_alpha(color, .5 * self.fade_in)); cr.fill()
        scan = x + (self.time * .045 % 1) * w
        cr.move_to(scan, y); cr.line_to(scan, y + h)
        cr.set_source_rgba(*with_alpha(self.theme.accent, .09 * self.fade_in))
        cr.set_line_width(1); cr.stroke()
        cr.restore()

    def _detail_card(self, cr, x, title, rows):
        self._card(cr, x, 746, 464, 218)
        self._text(cr, title, x + 18, 768, 11.5, 'accent')
        for i, (label, value) in enumerate(rows):
            self._text(cr, label, x + 18, 792 + i * 17, 10, 'muted', width=108)
            self._text(cr, value, x + 142, 792 + i * 17, 10, width=304)

    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        s = min(width / 1600, height / 1000)
        if s <= 0:
            return
        cr.save()
        cr.translate((width - 1600 * s) / 2 + (self.burn_x + self.jitter_x) * .12 * s,
                     (height - 1000 * s) / 2 + (self.burn_y + self.jitter_y) * .12 * s)
        cr.scale(s, s)
        sec = int(time.time())
        if sec != self._cached_sec:
            self._cached_sec = sec
            self._clock = time.strftime('%H:%M:%S' if self.config.clock_format_24h else '%I:%M:%S %p')
            self._date = time.strftime('%A · %d %B %Y').upper()
        self._text(cr, 'SYSTEM COCKPIT', 64, 55, 24, 'accent')
        self._text(cr, 'INSTRUMENT CHECK  /  NEEDLE SWEEP' if self.time < self.startup_delay + 3.15 else 'LIVE TELEMETRY  /  MEASURED UTILIZATION', 64, 92, 10, 'muted')
        self._text(cr, self._clock, 1536, 51, 26, align='right')
        self._text(cr, self._date, 1536, 89, 10, 'muted', 'right')
        m = self.metrics
        if m is None:
            self._text(cr, 'Waiting for the first system sample…', 800, 480, 14, 'muted', 'center')
            cr.restore(); return
        accent, secondary = self.theme.accent, self.theme.secondary
        self._section(cr, '01', 'CORE LOAD', 137, 'NEEDLE = CURRENT  ·  OUTER MARK = RECENT PEAK')
        for i, (key, label, sub) in enumerate([
            ('cpu', 'CPU', f'{m.cpu_freq_avg_ghz:.2f} GHz · {m.cpu_temp_c:.0f}°C' if getattr(m, 'cpu_temp_valid', False) else f'{m.cpu_freq_avg_ghz:.2f} GHz'),
            ('gpu', 'GPU', f'{m.gpu_clock_mhz:.0f} MHz · {m.gpu_temp_c:.0f}°C' if m.has_gpu else 'No supported GPU sensor'),
            ('mem', 'MEMORY', f'{m.mem_used_gib:.1f} / {m.mem_total_gib:.1f} GB'),
        ]):
            x = 64 + i * 504
            self._card(cr, x, 158, 464, 245)
            color = secondary if key == 'gpu' else accent
            value = self.instrument_value(self.values[key])
            available = key != 'gpu' or m.has_gpu
            self._ring(cr, x + 232, 252, 74, value if available or self.time < self.startup_delay + 3.15 else 0, color, self.instrument_value(self.peaks[key][0]))
            self._text(cr, label, x + 232, 222, 12, 'muted', 'center')
            self._text(cr, f'{value:.1f}%' if available else 'N/A', x + 232, 257, 30, align='center')
            self._text(cr, sub, x + 232, 325, 11, 'secondary', 'center', width=300)
            if key == 'cpu':
                self._text(cr, f'CORE ACTIVITY  ·  {m.cpu_cores} THREADS', x + 22, 353, 10, 'muted')
                # Group very large workstations so bars stay inside the instrument.
                stride = max(1, math.ceil(len(self.cores) / 32))
                bars = [sum(self.cores[j:j + stride]) / len(self.cores[j:j + stride])
                        for j in range(0, len(self.cores), stride)]
                count = len(bars)
                if count:
                    gap, total = 3, 420
                    bar_w = max(.5, (total - gap * (count - 1)) / count)
                    for c, load in enumerate(bars):
                        bx = x + 22 + c * (bar_w + gap)
                        h = max(2, min(100, self.instrument_value(load)) * .22)
                        cr.rectangle(bx, 383 - h, bar_w, h)
                        cr.set_source_rgba(*with_alpha(accent, (.25 + min(100, load) * .006) * self.fade_in)); cr.fill()
            elif key == 'gpu':
                self._text(cr, f'VRAM  {m.gpu_vram_used_mib:.0f} / {m.gpu_vram_total_mib:.0f} MB', x + 22, 353, 10, 'muted')
                self._bar(cr, x + 22, 380, 420, self.instrument_value(m.gpu_vram_percent), secondary)
            else:
                self._text(cr, f'FREE {m.mem_avail_gib:.1f} GB  ·  SWAP {m.swap_used_gib:.1f} / {m.swap_total_gib:.1f} GB', x + 22, 353, 10, 'muted')
                self._bar(cr, x + 22, 380, 420, self.instrument_value(m.swap_percent), accent)
        self._section(cr, '02', 'CAPACITY & THERMALS', 430)
        temperature_ok = getattr(m, 'cpu_temp_valid', False)
        support = [
            ('CPU TEMPERATURE', f'{self.instrument_value(self.values["temp"]):.0f}°C' if temperature_ok else 'N/A', '0–100°C display scale' if temperature_ok else 'Sensor unavailable', self.values['temp'] if temperature_ok else 0),
            ('ROOT STORAGE', f'{self.instrument_value(self.values["disk"]):.0f}%', f'{m.disk_free_gib:.1f} GB available', self.values['disk']),
            ('LOAD / CAPACITY', f'{self.instrument_value(self.values["load"]):.0f}%', f'1m load / {m.cpu_cores} threads', self.values['load']),
            ('BATTERY' if m.has_battery else 'POWER SOURCE', f'{self.instrument_value(self.values["battery"]):.0f}%' if m.has_battery else 'AC', m.battery_status if m.has_battery else 'No battery installed', self.values['battery'] if m.has_battery else 0),
        ]
        for i, (label, value, detail, percent) in enumerate(support):
            x = 64 + i * 378
            self._card(cr, x, 451, 338, 108)
            self._ring(cr, x + 61, 505, 30, self.instrument_value(percent), accent, lively=False)
            self._text(cr, label, x + 113, 474, 10, 'muted')
            self._text(cr, value, x + 113, 504, 24)
            self._text(cr, detail, x + 113, 541, 9.5, 'muted', width=210)
        self._section(cr, '03', 'ACTIVITY', 588, 'SOLID = CPU / RECEIVE  ·  DASHED = GPU / SEND')
        for x, w, title in [(64, 716, 'PROCESSOR HISTORY'), (820, 716, 'NETWORK THROUGHPUT')]:
            self._card(cr, x, 609, w, 110)
            self._text(cr, title, x + 18, 630, 10, 'accent')
        self._text(cr, f'CPU {self.values["cpu"]:.0f}%   GPU {self.values["gpu"]:.0f}%', 760, 630, 10, 'muted', 'right')
        self._plot(cr, 84, 652, 676, 47, [(m.cpu_history, accent), (m.gpu_history, secondary)], 100)
        self._text(cr, f'↓ {self._rate(m.net_rx_rate)}   ↑ {self._rate(m.net_tx_rate)}', 1516, 630, 10, 'muted', 'right')
        net_max = max([1024, *m.net_rx_history, *m.net_tx_history]) * 1.15
        self._plot(cr, 840, 652, 676, 47, [(m.net_rx_history, accent), (m.net_tx_history, secondary)], net_max)
        self._text(cr, 'LAST MINUTE', 84, 708, 8.5, 'muted')
        self._text(cr, f'AUTO SCALE  {self._rate(net_max)}', 1516, 708, 8.5, 'muted', 'right')
        pressure = []
        for key in ('cpu', 'memory', 'io'):
            p = getattr(m, 'pressure_' + key, None)
            pressure.append('—' if p is None else f'{p:.1f}%')
        measured = getattr(m, 'power_sensor_valid', False)
        self._detail_card(cr, 64, 'POWER & ELECTRICAL', [
            ('CPU est.', f'{m.cpu_power_w:.1f} W  · {m.cpu_volt_v:.2f} V · {m.cpu_current_a:.1f} A'),
            ('GPU est.', f'{m.gpu_power_w:.1f} W  · {m.gpu_volt_v:.2f} V · {m.gpu_current_a:.1f} A'),
            ('POWER SENSOR' if measured else 'TOTAL est.', f'{m.soc_power_w:.1f} W (sensor)' if measured else f'{m.soc_power_w:.1f} W · {m.soc_volt_v:.2f} V · {m.soc_current_a:.1f} A'),
            ('DRAM est.', f'{m.ram_power_w:.1f} W  · {m.ram_volt_v:.2f} V · {m.ram_current_a:.1f} A'),
            ('BATTERY', f'{m.bat_volt_v:.1f} V · {m.bat_current_a:.2f} A · {m.bat_power_w:.1f} W' if m.has_battery else 'Not installed'),
            ('AC INPUT', 'Connected' if m.ac_online else 'Disconnected'),
        ])
        smart = getattr(m, 'ssd_smart', {})
        today_flag = ' *' if getattr(m, 'disk_today_partial', True) else ''
        commands = smart.get('read_commands')
        write_commands = smart.get('write_commands')
        io_count = f'{commands + write_commands:,} (R+W)' + (' · snapshot' if smart.get('updated_at') else '') if commands is not None and write_commands is not None else 'Not exposed · refresh SMART'
        health = smart.get('health_percent')
        health_text = f'{health}% endurance · wear {smart.get("wear_used_percent", 0)}%' if health is not None else 'SMART unavailable'
        self._detail_card(cr, 568, 'STORAGE & MEMORY I/O', [
            ('ROOT / TEMP', f'{m.disk_used_gib:.0f}/{m.disk_total_gib:.0f} GB · {m.nvme_temp_c:.0f}°C' if getattr(m, 'nvme_temp_valid', False) else f'{m.disk_used_gib:.0f}/{m.disk_total_gib:.0f} GB'),
            ('TODAY READ', self._bytes(getattr(m, 'disk_today_read_bytes', None)) + today_flag),
            ('TODAY WRITE', self._bytes(getattr(m, 'disk_today_write_bytes', None)) + today_flag),
            ('READ NOW', f'{m.disk_read_mb_s:.1f} MB/s · {m.disk_read_iops:.0f} IOPS'),
            ('WRITE NOW', f'{m.disk_write_mb_s:.1f} MB/s · {m.disk_write_iops:.0f} IOPS'),
            ('SSD LIFE R', self._bytes(smart.get('read_bytes'))),
            ('SSD LIFE W', self._bytes(smart.get('write_bytes'))),
            ('SSD LIFE IOs', io_count),
            ('SSD HEALTH', health_text),
            ('MEM / VM', f'{m.mem_avail_gib:.1f}G free · {m.ram_speed_gbs:.2f}G/s pages'),
        ])
        self._detail_card(cr, 1072, 'RUNTIME & RESOURCE PRESSURE', [
            ('KERNEL', m.kernel),
            ('LOAD 1/5/15m', m.load_avg),
            ('TASKS', m.procs_str),
            ('PRESSURE 10s', 'CPU ' + pressure[0] + ' · MEM ' + pressure[1] + ' · IO ' + pressure[2]),
            ('GOVERNOR', m.cpu_governor),
            ('UPTIME', m.uptime_str),
        ])
        self._text(cr, 'DAILY * = TRACKED TODAY', 850, 981, 9, 'muted', 'center', width=400)
        self._text(cr, m.cpu_model.replace(' with Radeon Graphics', ''), 64, 981, 9.5, 'muted', width=750)
        self._text(cr, f'{m.user}@{m.hostname}  ·  {m.primary_net_iface}', 1536, 981, 9.5, 'muted', 'right', width=700)
        cr.restore()


SystemMode = SystemDashboardMode
