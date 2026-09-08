"""System metrics collector for Omarchy Screensaver.

Reads Linux /proc and /sys filesystems directly with zero subprocess overhead,
providing fast, lightweight, non-blocking telemetry.
"""

import collections
import os
import time
from typing import Dict, List, Optional, Tuple


class SystemMetrics:
    """Collects and caches live Linux system metrics."""

    def __init__(self, history_len: int = 60):
        self.history_len = history_len
        self._last_update_time = 0.0
        self._last_cpu_idle = 0.0
        self._last_cpu_total = 0.0
        self._last_net_rx = 0
        self._last_net_tx = 0
        self._last_net_time = 0.0

        # Current metrics
        self.cpu_percent: float = 0.0
        self.cpu_cores: int = os.cpu_count() or 8
        self.cpu_model: str = self._detect_cpu_model()

        self.mem_total_gib: float = 16.0
        self.mem_used_gib: float = 0.0
        self.mem_avail_gib: float = 0.0
        self.mem_percent: float = 0.0

        self.battery_percent: int = 100
        self.battery_status: str = "Full"
        self.ac_online: bool = True
        self.has_battery: bool = False

        self.net_rx_rate: float = 0.0  # bytes/sec
        self.net_tx_rate: float = 0.0  # bytes/sec
        self.primary_net_iface: str = ""

        self.disk_total_gib: float = 0.0
        self.disk_used_gib: float = 0.0
        self.disk_free_gib: float = 0.0
        self.disk_percent: float = 0.0

        self.cpu_temp_c: float = 40.0
        self.uptime_seconds: float = 0.0
        self.uptime_str: str = "0m"

        self.kernel: str = os.uname().release
        self.hostname: str = os.uname().nodename
        self.user: str = os.environ.get("USER", "daemon0")

        # Rolling history buffers for charts
        self.cpu_history: collections.deque = collections.deque(maxlen=history_len)
        self.mem_history: collections.deque = collections.deque(maxlen=history_len)
        self.net_rx_history: collections.deque = collections.deque(maxlen=history_len)
        self.net_tx_history: collections.deque = collections.deque(maxlen=history_len)

        for _ in range(history_len):
            self.cpu_history.append(0.0)
            self.mem_history.append(0.0)
            self.net_rx_history.append(0.0)
            self.net_tx_history.append(0.0)

        # Initialize base values
        self._init_cpu()
        self._init_net()
        self.update(force=True)

    def _detect_cpu_model(self) -> str:
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("model name"):
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        except Exception:
            pass
        return "AMD Ryzen 7 PRO 5850U"

    def _init_cpu(self):
        try:
            with open("/proc/stat", "r", encoding="utf-8") as f:
                fields = [float(x) for x in f.readline().strip().split()[1:8]]
                self._last_cpu_idle = fields[3] + fields[4]
                self._last_cpu_total = sum(fields)
        except Exception:
            pass

    def _init_net(self):
        try:
            self._last_net_time = time.time()
            rx, tx, iface = self._read_net_bytes()
            self._last_net_rx = rx
            self._last_net_tx = tx
            self.primary_net_iface = iface
        except Exception:
            pass

    def _read_net_bytes(self) -> Tuple[int, int, str]:
        total_rx = 0
        total_tx = 0
        best_iface = ""
        max_bytes = -1

        try:
            with open("/proc/net/dev", "r", encoding="utf-8") as f:
                lines = f.readlines()[2:]
                for line in lines:
                    parts = line.split(":")
                    if len(parts) == 2:
                        iface = parts[0].strip()
                        if iface == "lo":
                            continue
                        stats = parts[1].split()
                        rx = int(stats[0])
                        tx = int(stats[8])
                        total_rx += rx
                        total_tx += tx
                        if rx + tx > max_bytes:
                            max_bytes = rx + tx
                            best_iface = iface
        except Exception:
            pass

        return total_rx, total_tx, best_iface

    def update(self, force: bool = False):
        """Update metrics if at least 0.5s has elapsed since last update."""
        now = time.time()
        if not force and (now - self._last_update_time < 0.5):
            return

        dt = now - self._last_update_time if self._last_update_time > 0 else 1.0
        self._last_update_time = now

        # 1. CPU
        try:
            with open("/proc/stat", "r", encoding="utf-8") as f:
                fields = [float(x) for x in f.readline().strip().split()[1:8]]
                idle = fields[3] + fields[4]
                total = sum(fields)
                d_idle = idle - self._last_cpu_idle
                d_total = total - self._last_cpu_total
                if d_total > 0:
                    self.cpu_percent = max(0.0, min(100.0, (1.0 - d_idle / d_total) * 100.0))
                self._last_cpu_idle = idle
                self._last_cpu_total = total
                self.cpu_history.append(self.cpu_percent)
        except Exception:
            pass

        # 2. Memory
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                mem = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].split()[0])
            total_kb = mem.get("MemTotal", 16000000)
            avail_kb = mem.get("MemAvailable", total_kb // 2)
            used_kb = total_kb - avail_kb

            self.mem_total_gib = total_kb / (1024.0 * 1024.0)
            self.mem_avail_gib = avail_kb / (1024.0 * 1024.0)
            self.mem_used_gib = used_kb / (1024.0 * 1024.0)
            self.mem_percent = (used_kb / total_kb) * 100.0 if total_kb > 0 else 0.0
            self.mem_history.append(self.mem_percent)
        except Exception:
            pass

        # 3. Battery & AC
        try:
            # Check AC
            ac_path = "/sys/class/power_supply/AC/online"
            if os.path.exists(ac_path):
                with open(ac_path, "r", encoding="utf-8") as f:
                    self.ac_online = f.read().strip() == "1"
            else:
                self.ac_online = True

            # Check Battery
            bat_dir = None
            for name in os.listdir("/sys/class/power_supply"):
                if name.startswith("BAT"):
                    bat_dir = os.path.join("/sys/class/power_supply", name)
                    break

            if bat_dir and os.path.exists(bat_dir):
                self.has_battery = True
                cap_file = os.path.join(bat_dir, "capacity")
                if os.path.exists(cap_file):
                    with open(cap_file, "r", encoding="utf-8") as f:
                        self.battery_percent = int(f.read().strip())
                stat_file = os.path.join(bat_dir, "status")
                if os.path.exists(stat_file):
                    with open(stat_file, "r", encoding="utf-8") as f:
                        self.battery_status = f.read().strip()
            else:
                self.has_battery = False
                self.battery_percent = 100
                self.battery_status = "AC"
        except Exception:
            pass

        # 4. Network rates
        try:
            rx, tx, iface = self._read_net_bytes()
            net_dt = now - self._last_net_time if self._last_net_time > 0 else 1.0
            if net_dt > 0 and self._last_net_rx > 0:
                self.net_rx_rate = max(0.0, (rx - self._last_net_rx) / net_dt)
                self.net_tx_rate = max(0.0, (tx - self._last_net_tx) / net_dt)
            self._last_net_rx = rx
            self._last_net_tx = tx
            self._last_net_time = now
            self.primary_net_iface = iface
            self.net_rx_history.append(self.net_rx_rate)
            self.net_tx_history.append(self.net_tx_rate)
        except Exception:
            pass

        # 5. Disk Usage
        try:
            st = os.statvfs("/")
            total_b = st.f_blocks * st.f_frsize
            free_b = st.f_bavail * st.f_frsize
            used_b = total_b - free_b
            self.disk_total_gib = total_b / (1024.0 ** 3)
            self.disk_used_gib = used_b / (1024.0 ** 3)
            self.disk_free_gib = free_b / (1024.0 ** 3)
            self.disk_percent = (used_b / total_b) * 100.0 if total_b > 0 else 0.0
        except Exception:
            pass

        # 6. Thermal
        try:
            temp_candidates = []
            thermal_dir = "/sys/class/thermal"
            if os.path.exists(thermal_dir):
                for name in os.listdir(thermal_dir):
                    if name.startswith("thermal_zone"):
                        path = os.path.join(thermal_dir, name, "temp")
                        if os.path.exists(path):
                            with open(path, "r", encoding="utf-8") as f:
                                val = float(f.read().strip())
                                if val > 1000:
                                    val /= 1000.0
                                if 15.0 <= val <= 105.0:
                                    temp_candidates.append(val)
            if temp_candidates:
                self.cpu_temp_c = max(temp_candidates)
        except Exception:
            pass

        # 7. Uptime
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as f:
                self.uptime_seconds = float(f.readline().split()[0])
            days = int(self.uptime_seconds // 86400)
            hours = int((self.uptime_seconds % 86400) // 3600)
            mins = int((self.uptime_seconds % 3600) // 60)
            if days > 0:
                self.uptime_str = f"{days}d {hours}h {mins}m"
            elif hours > 0:
                self.uptime_str = f"{hours}h {mins}m"
            else:
                self.uptime_str = f"{mins}m"
        except Exception:
            pass
