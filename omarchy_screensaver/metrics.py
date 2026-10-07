"""System metrics collector for Omarchy Screensaver.

Reads Linux /proc and /sys filesystems directly with zero subprocess overhead,
providing fast, lightweight, non-blocking telemetry including GPU, CPU, power draw,
and comprehensive hardware sensor streams.
"""

import collections
import glob
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

        # CPU Core Telemetry
        self.cpu_percent: float = 0.0
        self.cpu_cores: int = os.cpu_count() or 8
        self.cpu_model: str = self._detect_cpu_model()
        self.cpu_freq_avg_ghz: float = 0.0
        self.cpu_freq_max_ghz: float = 0.0
        self.cpu_temp_c: float = 40.0
        self.cpu_power_w: float = 0.0
        self.cpu_volt_v: float = 0.88
        self.cpu_current_a: float = 7.0
        self.cpu_governor: str = "amd-pstate"
        self.load_avg: str = "0.00 · 0.00 · 0.00"
        self.procs_str: str = "1 Run · 100 Tasks"

        # GPU Telemetry
        self.has_gpu: bool = False
        self.gpu_vendor: str = "AMD"
        self.gpu_name: str = "Radeon Graphics"
        self.gpu_percent: float = 0.0
        self.gpu_clock_mhz: float = 0.0
        self.gpu_temp_c: float = 40.0
        self.gpu_power_w: float = 0.0
        self.gpu_volt_v: float = 0.90
        self.gpu_current_a: float = 3.0
        self.gpu_vram_used_mib: float = 0.0
        self.gpu_vram_total_mib: float = 0.0
        self.gpu_vram_percent: float = 0.0
        self.gpu_gtt_used_gib: float = 0.0
        self.gpu_gtt_total_gib: float = 0.0

        # Power Draw & Electrical Telemetry
        self.soc_power_w: float = 0.0
        self.soc_volt_v: float = 0.83
        self.soc_current_a: float = 12.0
        self.bat_power_w: float = 0.0
        self.bat_volt_v: float = 12.0
        self.bat_current_a: float = 0.0
        self.battery_percent: int = 100
        self.battery_status: str = "Full"
        self.ac_online: bool = True
        self.has_battery: bool = False
        self.power_source_str: str = "AC POWERED"

        # Memory & Swap Telemetry
        self.mem_total_gib: float = 16.0
        self.mem_used_gib: float = 0.0
        self.mem_avail_gib: float = 0.0
        self.mem_percent: float = 0.0
        self.swap_total_gib: float = 0.0
        self.swap_used_gib: float = 0.0
        self.swap_percent: float = 0.0

        # Storage & NVMe Thermals
        self.disk_total_gib: float = 0.0
        self.disk_used_gib: float = 0.0
        self.disk_free_gib: float = 0.0
        self.disk_percent: float = 0.0
        self.nvme_temp_c: float = 35.0

        # Network Telemetry
        self.net_rx_rate: float = 0.0  # bytes/sec
        self.net_tx_rate: float = 0.0  # bytes/sec
        self.primary_net_iface: str = ""

        # OS Details
        self.uptime_seconds: float = 0.0
        self.uptime_str: str = "0m"
        self.kernel: str = os.uname().release
        self.hostname: str = os.uname().nodename
        self.user: str = os.environ.get("USER", "daemon0")

        # Rolling history buffers for charts and sparklines
        self.cpu_history: collections.deque = collections.deque(maxlen=history_len)
        self.gpu_history: collections.deque = collections.deque(maxlen=history_len)
        self.mem_history: collections.deque = collections.deque(maxlen=history_len)
        self.net_rx_history: collections.deque = collections.deque(maxlen=history_len)
        self.net_tx_history: collections.deque = collections.deque(maxlen=history_len)

        for _ in range(history_len):
            self.cpu_history.append(0.0)
            self.gpu_history.append(0.0)
            self.mem_history.append(0.0)
            self.net_rx_history.append(0.0)
            self.net_tx_history.append(0.0)

        # Initialize base values and discover hardware sysfs paths
        self._init_hardware_paths()
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

    def _init_hardware_paths(self):
        """Discover and cache sysfs file paths for fast zero-overhead updates."""
        # 1. CPU Frequencies
        self._cpu_freq_paths = sorted(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"))

        # 2. GPU Paths (AMD / Intel / generic DRM)
        self._gpu_busy_path = None
        self._gpu_vram_used_path = None
        self._gpu_vram_total_path = None
        self._gpu_gtt_used_path = None
        self._gpu_gtt_total_path = None
        self._gpu_power_path = None
        self._gpu_temp_path = None
        self._gpu_freq_path = None

        for card in sorted(glob.glob("/sys/class/drm/card[0-9]*/device")):
            busy_cand = os.path.join(card, "gpu_busy_percent")
            if os.path.exists(busy_cand):
                self.has_gpu = True
                self._gpu_busy_path = busy_cand
                self._gpu_vram_used_path = os.path.join(card, "mem_info_vram_used")
                self._gpu_vram_total_path = os.path.join(card, "mem_info_vram_total")
                self._gpu_gtt_used_path = os.path.join(card, "mem_info_gtt_used")
                self._gpu_gtt_total_path = os.path.join(card, "mem_info_gtt_total")

                # Detect GPU model / name
                dev_link = os.path.realpath(card)
                if "0000:04:00.0" in dev_link or "amdgpu" in dev_link:
                    self.gpu_vendor = "AMD"
                    self.gpu_name = "AMD Radeon Vega Graphics"
                elif "i915" in dev_link or "xe" in dev_link:
                    self.gpu_vendor = "Intel"
                    self.gpu_name = "Intel Iris/Arc Graphics"

                # Check hwmon inside card
                for hw in glob.glob(os.path.join(card, "hwmon/hwmon*")):
                    pw = os.path.join(hw, "power1_input")
                    if os.path.exists(pw):
                        self._gpu_power_path = pw
                    tmp = os.path.join(hw, "temp1_input")
                    if os.path.exists(tmp):
                        self._gpu_temp_path = tmp
                    frq = os.path.join(hw, "freq1_input")
                    if os.path.exists(frq):
                        self._gpu_freq_path = frq
                    v0 = os.path.join(hw, "in0_input")
                    if os.path.exists(v0):
                        self._gpu_volt_path = v0
                    v1 = os.path.join(hw, "in1_input")
                    if os.path.exists(v1):
                        self._soc_volt_path = v1
                break

        # 3. CPU Temperature, Voltage & NVMe Sensors
        self._cpu_temp_path = None
        self._cpu_volt_path = None
        self._nvme_temp_path = None
        for hw in glob.glob("/sys/class/hwmon/hwmon*"):
            try:
                name_file = os.path.join(hw, "name")
                if os.path.exists(name_file):
                    with open(name_file, "r", encoding="utf-8") as nf:
                        nm = nf.read().strip()
                    if nm in ("k10temp", "coretemp", "zenpower"):
                        t_cand = os.path.join(hw, "temp1_input")
                        if os.path.exists(t_cand):
                            self._cpu_temp_path = t_cand
                        v_cand = os.path.join(hw, "in0_input")
                        if os.path.exists(v_cand):
                            self._cpu_volt_path = v_cand
                    elif nm == "nvme":
                        t_cand = os.path.join(hw, "temp1_input")
                        if os.path.exists(t_cand):
                            self._nvme_temp_path = t_cand
            except Exception:
                pass

        # 4. CPU Governor / Driver
        self._cpu_drv_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        self._cpu_gov_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"

        # 5. Battery directory
        self._bat_dir = None
        try:
            for name in os.listdir("/sys/class/power_supply"):
                if name.startswith("BAT"):
                    self._bat_dir = os.path.join("/sys/class/power_supply", name)
                    break
        except Exception:
            pass

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
        """Update metrics if at least 0.4s has elapsed since last update."""
        now = time.time()
        if not force and (now - self._last_update_time < 0.4):
            return

        dt = now - self._last_update_time if self._last_update_time > 0 else 1.0
        self._last_update_time = now

        # 1. CPU Usage
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

        # 2. CPU Frequencies
        if self._cpu_freq_paths:
            freqs = []
            for fp in self._cpu_freq_paths:
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        freqs.append(int(f.read().strip()))
                except Exception:
                    pass
            if freqs:
                self.cpu_freq_avg_ghz = (sum(freqs) / len(freqs)) / 1e6
                self.cpu_freq_max_ghz = max(freqs) / 1e6

        # 3. CPU Temperature
        if self._cpu_temp_path and os.path.exists(self._cpu_temp_path):
            try:
                with open(self._cpu_temp_path, "r", encoding="utf-8") as f:
                    self.cpu_temp_c = float(f.read().strip()) / 1000.0
            except Exception:
                pass
        else:
            # Fallback to thermal zones
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

        # 4. Memory & Swap
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

            # Swap
            sw_total_kb = mem.get("SwapTotal", 0)
            sw_free_kb = mem.get("SwapFree", 0)
            sw_used_kb = sw_total_kb - sw_free_kb
            self.swap_total_gib = sw_total_kb / (1024.0 * 1024.0)
            self.swap_used_gib = sw_used_kb / (1024.0 * 1024.0)
            self.swap_percent = (sw_used_kb / sw_total_kb) * 100.0 if sw_total_kb > 0 else 0.0
        except Exception:
            pass

        # 5. GPU Telemetry
        if self._gpu_busy_path and os.path.exists(self._gpu_busy_path):
            try:
                with open(self._gpu_busy_path, "r", encoding="utf-8") as f:
                    self.gpu_percent = max(0.0, min(100.0, float(f.read().strip())))
            except Exception:
                pass
        self.gpu_history.append(self.gpu_percent)

        if self._gpu_vram_used_path and os.path.exists(self._gpu_vram_used_path):
            try:
                with open(self._gpu_vram_used_path, "r", encoding="utf-8") as f:
                    self.gpu_vram_used_mib = int(f.read().strip()) / (1024.0 * 1024.0)
                with open(self._gpu_vram_total_path, "r", encoding="utf-8") as f:
                    self.gpu_vram_total_mib = int(f.read().strip()) / (1024.0 * 1024.0)
                if self.gpu_vram_total_mib > 0:
                    self.gpu_vram_percent = (self.gpu_vram_used_mib / self.gpu_vram_total_mib) * 100.0
            except Exception:
                pass

        if self._gpu_gtt_used_path and os.path.exists(self._gpu_gtt_used_path):
            try:
                with open(self._gpu_gtt_used_path, "r", encoding="utf-8") as f:
                    self.gpu_gtt_used_gib = int(f.read().strip()) / (1024.0 ** 3)
                with open(self._gpu_gtt_total_path, "r", encoding="utf-8") as f:
                    self.gpu_gtt_total_gib = int(f.read().strip()) / (1024.0 ** 3)
            except Exception:
                pass

        if self._gpu_freq_path and os.path.exists(self._gpu_freq_path):
            try:
                with open(self._gpu_freq_path, "r", encoding="utf-8") as f:
                    self.gpu_clock_mhz = float(f.read().strip()) / 1e6
            except Exception:
                pass

        if self._gpu_temp_path and os.path.exists(self._gpu_temp_path):
            try:
                with open(self._gpu_temp_path, "r", encoding="utf-8") as f:
                    self.gpu_temp_c = float(f.read().strip()) / 1000.0
            except Exception:
                pass

        # 6. Power Draw Breakdown & Electrical Telemetry (Voltage & Current Amps)
        soc_p = 0.0
        if self._gpu_power_path and os.path.exists(self._gpu_power_path):
            try:
                with open(self._gpu_power_path, "r", encoding="utf-8") as f:
                    soc_p = float(f.read().strip()) / 1e6
            except Exception:
                pass
        self.soc_power_w = max(0.0, soc_p)

        if self.soc_power_w > 0:
            # Dynamic power division between compute cores and GPU units
            w_gpu = max(0.2, self.gpu_percent) * 1.15
            w_cpu = max(0.2, self.cpu_percent)
            ratio = w_gpu / (w_gpu + w_cpu)
            self.gpu_power_w = round(self.soc_power_w * ratio, 1)
            self.cpu_power_w = round(max(0.0, self.soc_power_w - self.gpu_power_w), 1)
        else:
            # Physics-based dynamic estimation
            self.cpu_power_w = round(4.0 + 15.0 * (self.cpu_percent / 100.0), 1)
            self.gpu_power_w = round(2.5 + 12.0 * (self.gpu_percent / 100.0), 1)
            self.soc_power_w = round(self.cpu_power_w + self.gpu_power_w, 1)

        # GPU Graphics Voltage (vddgfx) and Current Amperage
        if self._gpu_volt_path and os.path.exists(self._gpu_volt_path):
            try:
                with open(self._gpu_volt_path, "r", encoding="utf-8") as vf:
                    val = float(vf.read().strip())
                    self.gpu_volt_v = round(val / 1000.0 if val > 200 else val, 2)
            except Exception:
                pass
        else:
            self.gpu_volt_v = round(0.70 + 0.35 * (self.gpu_percent / 100.0), 2)

        self.gpu_current_a = round(self.gpu_power_w / max(0.4, self.gpu_volt_v), 1)

        # SoC Northbridge Voltage (vddnb) and Current Amperage
        if self._soc_volt_path and os.path.exists(self._soc_volt_path):
            try:
                with open(self._soc_volt_path, "r", encoding="utf-8") as vf:
                    val = float(vf.read().strip())
                    self.soc_volt_v = round(val / 1000.0 if val > 200 else val, 2)
            except Exception:
                pass
        else:
            self.soc_volt_v = 0.83

        self.soc_current_a = round(self.soc_power_w / max(0.4, self.soc_volt_v), 1)

        # CPU Core Voltage (Vcore) and Current Amperage
        if self._cpu_volt_path and os.path.exists(self._cpu_volt_path):
            try:
                with open(self._cpu_volt_path, "r", encoding="utf-8") as vf:
                    val = float(vf.read().strip())
                    self.cpu_volt_v = round(val / 1000.0 if val > 200 else val, 2)
            except Exception:
                pass
        else:
            # AMD Zen / Intel dynamic VF curve model based on frequency and utilization
            v_base = 0.72
            f_ratio = max(0.0, min(1.0, (self.cpu_freq_avg_ghz - 1.4) / (max(2.4, self.cpu_freq_max_ghz) - 1.4)))
            l_ratio = self.cpu_percent / 100.0
            self.cpu_volt_v = round(v_base + 0.46 * f_ratio + 0.12 * l_ratio, 2)

        self.cpu_current_a = round(self.cpu_power_w / max(0.4, self.cpu_volt_v), 1)

        # 7. Battery & AC Power
        try:
            ac_path = "/sys/class/power_supply/AC/online"
            if os.path.exists(ac_path):
                with open(ac_path, "r", encoding="utf-8") as f:
                    self.ac_online = f.read().strip() == "1"
            else:
                self.ac_online = True

            if self._bat_dir and os.path.exists(self._bat_dir):
                self.has_battery = True
                cap_file = os.path.join(self._bat_dir, "capacity")
                if os.path.exists(cap_file):
                    with open(cap_file, "r", encoding="utf-8") as f:
                        self.battery_percent = int(f.read().strip())
                stat_file = os.path.join(self._bat_dir, "status")
                if os.path.exists(stat_file):
                    with open(stat_file, "r", encoding="utf-8") as f:
                        self.battery_status = f.read().strip()

                self.power_source_str = f"AC [{self.battery_status}]" if self.ac_online else "BATTERY"

                c_now = os.path.join(self._bat_dir, "current_now")
                v_now = os.path.join(self._bat_dir, "voltage_now")
                cur = 0.0
                volt = 12.0
                if os.path.exists(v_now):
                    with open(v_now, "r", encoding="utf-8") as vf:
                        volt = float(vf.read().strip()) / 1e6
                        self.bat_volt_v = round(volt, 2)
                if os.path.exists(c_now):
                    with open(c_now, "r", encoding="utf-8") as cf:
                        cur = float(cf.read().strip()) / 1e6
                if cur > 0:
                    self.bat_current_a = round(cur, 2)
                    self.bat_power_w = round(cur * volt, 1)
                elif self.bat_power_w > 0:
                    self.bat_current_a = round(self.bat_power_w / max(1.0, self.bat_volt_v), 2)
                else:
                    self.bat_current_a = 0.0
            else:
                self.has_battery = False
                self.battery_percent = 100
                self.battery_status = "AC"
                self.power_source_str = "AC POWERED"
                self.bat_power_w = 0.0
        except Exception:
            pass

        # 8. NVMe Storage Thermal
        if self._nvme_temp_path and os.path.exists(self._nvme_temp_path):
            try:
                with open(self._nvme_temp_path, "r", encoding="utf-8") as f:
                    self.nvme_temp_c = float(f.read().strip()) / 1000.0
            except Exception:
                pass

        # 9. Network rates
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

        # 10. Disk Usage
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

        # 11. Uptime
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

        # 12. CPU Governor & Driver
        try:
            drv = ""
            gov = ""
            if os.path.exists(self._cpu_drv_path):
                with open(self._cpu_drv_path, "r", encoding="utf-8") as f:
                    drv = f.read().strip()
            if os.path.exists(self._cpu_gov_path):
                with open(self._cpu_gov_path, "r", encoding="utf-8") as f:
                    gov = f.read().strip()
            if drv and gov:
                self.cpu_governor = f"{drv} [{gov}]"
            elif drv or gov:
                self.cpu_governor = drv or gov
        except Exception:
            pass

        # 13. System Load Averages & Active Tasks
        try:
            with open("/proc/loadavg", "r", encoding="utf-8") as f:
                parts = f.read().strip().split()
                if len(parts) >= 4:
                    self.load_avg = f"{parts[0]} · {parts[1]} · {parts[2]}"
                    run_proc = parts[3].split("/")
                    if len(run_proc) == 2:
                        self.procs_str = f"{run_proc[0]} Run · {run_proc[1]} Tasks"
        except Exception:
            pass

