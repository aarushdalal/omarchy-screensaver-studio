"""Mode 3: Terminal System Monitor.

Renders a futuristic terminal-like diagnostic monitor with authentic system telemetry,
subsystem status checks, periodic event logs, and a blinking cursor.
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
    """Futuristic terminal console screensaver mode."""

    PERIODIC_LOGS = [
        "[IDLE] Session idle threshold verified (150s). Compositor guarded.",
        "[DSP] Audiophile headroom verified (-8.0 dB). True-peak limiter active.",
        "[SYNC] Rclone backup engine heartbeat: GDrive target synchronized.",
        "[WAYLAND] Layer-shell surfaces synchronized with Hyprland 0.56.2.",
        "[THERMAL] AMD Cezanne Vega mobile IGP operating at nominal temperature.",
        "[THEME] Osaka Jade color palette bound to active layer 0 canvas.",
        "[NETWORK] Wireless link wlp1s0 RSSI stable. Zero dropped frames.",
        "[SECURITY] Wayland session lock ready. PAM authentication armed.",
        "[POWER] Dynamic frequency scaling: Ryzen 7 PRO 5850U balanced profile.",
        "[AUDIO] WirePlumber BlueZ session locked to high-bitrate A2DP AAC.",
    ]

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.metrics: Optional[SystemMetrics] = None
        self.log_entries: List[str] = [
            "[BOOT] Omarchy workstation diagnostic engine initialized.",
            "[INIT] Querying /proc and /sys kernel telemetry buffers...",
        ]
        self.last_log_time: float = 0.0
        self.next_log_idx: int = 0
        self.fade_in: float = 0.0
        self.target_fps: int = 10

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
        self.clear_background(cr, width, height)

        fade = self.fade_in

        # Box dimensions
        box_w = min(1000.0, width * 0.88)
        box_h = min(720.0, height * 0.86)
        bx = (width - box_w) * 0.5 + self.burn_x
        by = (height - box_h) * 0.5 + self.burn_y

        # Draw Terminal Container
        self.draw_rounded_rect(cr, bx, by, box_w, box_h, 10.0)
        cr.set_source_rgba(*with_alpha(self.theme.card_bg, 0.85 * fade))
        cr.fill_preserve()
        cr.set_source_rgba(*with_alpha(self.theme.primary, 0.35 * fade))
        cr.set_line_width(1.2)
        cr.stroke()

        # Title bar header
        title_h = 36.0
        self.draw_rounded_rect(cr, bx, by, box_w, title_h, 10.0)
        cr.set_source_rgba(*with_alpha(self.theme.surface, 0.95 * fade))
        cr.fill()

        # Terminal Dots
        dots = [self.theme.danger, self.theme.warning, self.theme.success]
        for i, dot_color in enumerate(dots):
            cr.set_source_rgba(*with_alpha(dot_color, 0.85 * fade))
            cr.arc(bx + 18.0 + i * 16.0, by + title_h * 0.5, 4.5, 0, math.pi * 2)
            cr.fill()

        # Title Text
        user = self.metrics.user if self.metrics else "daemon0"
        host = self.metrics.hostname if self.metrics else "Daemon0"
        title_str = f"{user}@{host}: ~/omarchy-screensaver   [SYSTEM_STATUS]"
        self.draw_text(
            cr, title_str, bx + box_w * 0.5, by + title_h * 0.5,
            self.FONT_MONO, 11.0, with_alpha(self.theme.muted, fade),
            align="center", weight=Pango.Weight.NORMAL
        )

        # Content Area
        pad_x = bx + 28.0
        cur_y = by + title_h + 22.0
        font_size = 11.5
        line_spacing = 21.0

        # Prompt
        self.draw_text(
            cr, f"{user}@{host}:~$ omarchy-screensaver --diagnostics",
            pad_x, cur_y, self.FONT_MONO, font_size,
            with_alpha(self.theme.accent, fade), align="left", weight=Pango.Weight.BOLD
        )
        cur_y += line_spacing * 1.3

        # Subsystem Checks
        kernel_str = self.metrics.kernel if self.metrics else "7.1.9-arch1-2"
        checks = [
            ("kernel", f"Linux {kernel_str} (x86_64)"),
            ("wayland", "Hyprland 0.56.2 [COMPOSITOR ONLINE]"),
            ("shell", "Quickshell 0.3.1 (omarchy-shell)"),
            ("audio", "PipeWire 1.6.8 + EasyEffects 8.2.8 [AUDIOPHILE DSP]"),
            ("storage", "/dev/mapper/omarchy_root mounted [RW]"),
            ("power", f"AC Online: {self.metrics.ac_online if self.metrics else True}"),
        ]

        for label, desc in checks:
            # [ OK ] tag
            self.draw_text(
                cr, "[", pad_x, cur_y, self.FONT_MONO, font_size,
                with_alpha(self.theme.muted, fade), align="left"
            )
            self.draw_text(
                cr, "  OK  ", pad_x + 8.0, cur_y, self.FONT_MONO, font_size,
                with_alpha(self.theme.success, fade), align="left", weight=Pango.Weight.BOLD
            )
            self.draw_text(
                cr, "]", pad_x + 58.0, cur_y, self.FONT_MONO, font_size,
                with_alpha(self.theme.muted, fade), align="left"
            )
            self.draw_text(
                cr, f"{label:<9} :: {desc}", pad_x + 75.0, cur_y, self.FONT_MONO, font_size,
                with_alpha(self.theme.foreground, fade * 0.9), align="left"
            )
            cur_y += line_spacing

        cur_y += 6.0

        # Section Header
        self.draw_text(
            cr, "SYSTEM TELEMETRY", pad_x, cur_y, self.FONT_MONO, font_size,
            with_alpha(self.theme.primary, fade), align="left", weight=Pango.Weight.BOLD
        )
        cur_y += 14.0

        # Divider line
        cr.set_source_rgba(*with_alpha(self.theme.primary, 0.25 * fade))
        cr.set_line_width(1.0)
        cr.move_to(pad_x, cur_y)
        cr.line_to(bx + box_w - 28.0, cur_y)
        cr.stroke()
        cur_y += 14.0

        # Telemetry lines
        if self.metrics:
            m = self.metrics

            # CPU Bar
            bar_len = 16
            filled = int((m.cpu_percent / 100.0) * bar_len)
            bar_str = "█" * filled + "░" * (bar_len - filled)

            rx_str = f"{m.net_rx_rate / (1024 * 1024):.1f} MB/s" if m.net_rx_rate >= 1024 * 1024 else f"{m.net_rx_rate / 1024:.0f} KB/s"
            tx_str = f"{m.net_tx_rate / (1024 * 1024):.1f} MB/s" if m.net_tx_rate >= 1024 * 1024 else f"{m.net_tx_rate / 1024:.0f} KB/s"

            stats = [
                ("CPU USAGE", f"{m.cpu_percent:04.1f}%   [{bar_str}]  {m.cpu_model}"),
                ("MEMORY", f"{m.mem_used_gib:.1f} / {m.mem_total_gib:.1f} GiB ({m.mem_percent:.1f}%)"),
                ("BATTERY", f"{m.battery_percent}% [{m.battery_status}, AC={'ONLINE' if m.ac_online else 'OFFLINE'}]"),
                ("STORAGE", f"{m.disk_used_gib:.1f} / {m.disk_total_gib:.1f} GiB ({m.disk_percent:.1f}% root)"),
                ("NETWORK", f"RX {rx_str}   │   TX {tx_str}   ({m.primary_net_iface})"),
                ("UPTIME", f"{m.uptime_str}"),
            ]

            for k, v in stats:
                self.draw_text(
                    cr, f"{k:<13} : ", pad_x, cur_y, self.FONT_MONO, font_size,
                    with_alpha(self.theme.muted, fade), align="left"
                )
                self.draw_text(
                    cr, v, pad_x + 125.0, cur_y, self.FONT_MONO, font_size,
                    with_alpha(self.theme.bright_foreground, fade), align="left"
                )
                cur_y += line_spacing

        cur_y += 8.0

        # Events stream
        self.draw_text(
            cr, "> monitoring system events...", pad_x, cur_y, self.FONT_MONO, font_size,
            with_alpha(self.theme.info, fade * 0.8), align="left"
        )
        cur_y += line_spacing

        for log in self.log_entries[-4:]:
            self.draw_text(
                cr, log, pad_x + 12.0, cur_y, self.FONT_MONO, font_size * 0.92,
                with_alpha(self.theme.foreground, fade * 0.75), align="left"
            )
            cur_y += line_spacing * 0.95

        # Blinking cursor
        cursor_visible = (int(self.time / self.config.terminal_cursor_blink_rate) % 2) == 0
        if cursor_visible:
            self.draw_text(
                cr, "▋", pad_x + 12.0, cur_y, self.FONT_MONO, font_size,
                with_alpha(self.theme.accent, fade), align="left"
            )
