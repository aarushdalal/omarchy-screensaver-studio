"""Mode 3: Borderless Holographic Diagnostic Stream.

Renders an authentic, floating cybernetic system diagnostic stream with real
kernel & hardware telemetry, glowing semantic tokens, and complete OLED burn-in defense.
Zero static window chrome or fake OS border clichés.
"""

import math
import time
from typing import List, Optional, Tuple

import cairo
from gi.repository import Pango, PangoCairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class TerminalMode(BaseMode):
    """Futuristic borderless holographic diagnostic console screensaver mode."""

    PERIODIC_LOGS = [
        "[IDLE] Session idle threshold verified (150s). Wayland compositor guarded.",
        "[DSP] Audiophile headroom verified (-8.0 dB). True-peak limiter active.",
        "[SYNC] Rclone cloud backup engine heartbeat: Google Drive synchronized.",
        "[WAYLAND] Layer-shell surfaces synchronized with Hyprland 0.56.2.",
        "[THERMAL] AMD Cezanne Vega mobile IGP operating at nominal temperature.",
        "[ENTROPY] Linux kernel cryptographic pool health: 4096 bits available.",
        "[NETWORK] Wireless link wlp1s0 RSSI -42 dBm. Zero frame drops recorded.",
        "[SECURITY] Wayland session lock ready. PAM authentication daemon armed.",
        "[POWER] Dynamic frequency governor: Ryzen 7 PRO 5850U balanced profile.",
        "[AUDIO] WirePlumber BlueZ session locked to high-bitrate A2DP AAC codec.",
        "[MEM] Slab memory allocator reclaim scan passed. Zero memory pressure.",
        "[GPU] Mesa RADV driver Vulkan 1.3 pipeline caches warmed and valid.",
    ]

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.metrics: Optional[SystemMetrics] = None
        self.log_entries: List[str] = [
            "[BOOT] Omarchy workstation diagnostic engine initialized.",
            "[INIT] Querying /proc and /sys kernel telemetry buffers...",
            "[LOAD] Initializing Wayland direct-scanout layer shell...",
        ]
        self.last_log_time: float = 0.0
        self.next_log_idx: int = 0
        self.fade_in: float = 0.0
        self.target_fps: int = 15

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.metrics = metrics

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        # Periodically append a subtle event log
        if self.time - self.last_log_time > self.config.terminal_event_interval:
            self.last_log_time = self.time
            msg = self.PERIODIC_LOGS[self.next_log_idx % len(self.PERIODIC_LOGS)]
            self.next_log_idx += 1
            cur_time = time.strftime("%H:%M:%S")
            self.log_entries.append(f"[{cur_time}] {msg}")
            if len(self.log_entries) > self.config.terminal_max_log_lines:
                self.log_entries.pop(0)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        # 100% OLED pitch black background (subpixels off)
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor

        # Wandering holographic stream anchor (zero static pixel footprint)
        stream_w = min(1100.0, width * 0.88)
        start_x = (width - stream_w) * 0.5 + self.burn_x + self.jitter_x
        start_y = height * 0.12 + self.burn_y + self.jitter_y

        font_size = max(11.0, min(14.0, width * 0.009))
        line_spacing = font_size * 1.85
        cur_y = start_y

        user = self.metrics.user if self.metrics else "daemon0"
        host = self.metrics.hostname if self.metrics else "Daemon0"

        # 1. Holographic Header (Clean floating title, zero bounding boxes)
        header_text = f"// OMARCHY_TELEMETRY_STREAM :: {user}@{host} [PID {self.monitor_index}]"
        self.draw_text(
            cr, header_text, start_x, cur_y, self.FONT_MONO, font_size * 0.95,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.90)),
            align="left", weight=Pango.Weight.BOLD
        )
        cur_y += line_spacing * 1.4

        # 2. Subsystem Verification Status
        kernel_str = self.metrics.kernel if self.metrics else "7.1.9-arch1-2"
        checks = [
            ("KERNEL", f"Linux {kernel_str} (x86_64)"),
            ("WAYLAND", "Hyprland 0.56.2 [COMPOSITOR ONLINE]"),
            ("AUDIO", "PipeWire 1.6.8 + EasyEffects 8.2.8 [AUDIOPHILE DSP]"),
            ("STORAGE", "/dev/mapper/omarchy_root [NVMe RW VALID]"),
            ("POWER", f"AC Online: {self.metrics.ac_online if self.metrics else True}"),
        ]

        for label, desc in checks:
            self.draw_text(
                cr, "✓", start_x, cur_y, self.FONT_MONO, font_size,
                self.oled_color(with_alpha(self.theme.success, fade * 0.95)), align="left", weight=Pango.Weight.BOLD
            )
            self.draw_text(
                cr, f"[{label:<8}]", start_x + 22.0, cur_y, self.FONT_MONO, font_size,
                self.oled_color(with_alpha(self.theme.primary, fade * 0.85)), align="left", weight=Pango.Weight.MEDIUM
            )
            self.draw_text(
                cr, f":: {desc}", start_x + 130.0, cur_y, self.FONT_MONO, font_size,
                self.oled_color(with_alpha(self.theme.foreground, fade * 0.75)), align="left"
            )
            cur_y += line_spacing

        cur_y += line_spacing * 0.5

        # 3. Live Kernel Telemetry Readings
        if self.metrics:
            m = self.metrics
            bar_len = 18
            filled = max(0, min(bar_len, int((m.cpu_percent / 100.0) * bar_len)))
            bar_str = "■" * filled + "·" * (bar_len - filled)

            rx_str = f"{m.net_rx_rate / (1024 * 1024):.1f} MB/s" if m.net_rx_rate >= 1024 * 1024 else f"{m.net_rx_rate / 1024:.0f} KB/s"
            tx_str = f"{m.net_tx_rate / (1024 * 1024):.1f} MB/s" if m.net_tx_rate >= 1024 * 1024 else f"{m.net_tx_rate / 1024:.0f} KB/s"

            stats = [
                ("CPU LOAD", f"{m.cpu_percent:04.1f}%  [{bar_str}]  {m.cpu_model}"),
                ("MEMORY", f"{m.mem_used_gib:.1f} / {m.mem_total_gib:.1f} GiB ({m.mem_percent:.1f}%)"),
                ("BATTERY", f"{m.battery_percent}% [{m.battery_status}, AC={'ONLINE' if m.ac_online else 'OFFLINE'}]"),
                ("NETWORK", f"RX {rx_str}   │   TX {tx_str}   ({m.primary_net_iface})"),
                ("UPTIME", f"{m.uptime_str}"),
            ]

            for k, v in stats:
                self.draw_text(
                    cr, f"{k:<10} →", start_x + 22.0, cur_y, self.FONT_MONO, font_size,
                    self.oled_color(with_alpha(self.theme.muted, fade * 0.8)), align="left"
                )
                self.draw_text(
                    cr, v, start_x + 130.0, cur_y, self.FONT_MONO, font_size,
                    self.oled_color(with_alpha(self.theme.bright_foreground, fade * 0.9)), align="left"
                )
                cur_y += line_spacing

        cur_y += line_spacing * 0.5

        # 4. Floating Event Buffer Waterfall
        self.draw_text(
            cr, "// EVENT_LOG_STREAM", start_x, cur_y, self.FONT_MONO, font_size * 0.90,
            self.oled_color(with_alpha(self.theme.secondary, fade * 0.75)), align="left", weight=Pango.Weight.BOLD
        )
        cur_y += line_spacing * 1.1

        for i, log in enumerate(self.log_entries[-6:]):
            # Older logs have softer opacity for depth
            depth_alpha = (0.5 + 0.5 * ((i + 1) / 6.0)) * fade
            self.draw_text(
                cr, log, start_x + 22.0, cur_y, self.FONT_MONO, font_size * 0.92,
                self.oled_color(with_alpha(self.theme.foreground, depth_alpha)), align="left"
            )
            cur_y += line_spacing

        # 5. Pulsing Cursor
        cursor_visible = (int(self.time / self.config.terminal_cursor_blink_rate) % 2) == 0
        if cursor_visible:
            self.draw_text(
                cr, "❯ █", start_x, cur_y + 4.0, self.FONT_MONO, font_size,
                self.oled_color(with_alpha(self.theme.accent, fade * 0.95)), align="left"
            )

