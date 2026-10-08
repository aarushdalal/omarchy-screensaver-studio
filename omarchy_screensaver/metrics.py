"""System metrics collector for Omarchy Screensaver.

Reads Linux /proc and /sys filesystems directly with zero subprocess overhead,
providing fast, lightweight, non-blocking telemetry including GPU, CPU, power draw,
and comprehensive hardware sensor streams.
"""

import collections
import glob
import os
import threading
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
        self._last_disk_time = 0.0
        self._nvme_reading = False

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

        # Storage I/O rates and totals
        self.disk_read_mb_s: float = 0.0
        self.disk_write_mb_s: float = 0.0
        self.disk_read_iops: float = 0.0
        self.disk_write_iops: float = 0.0
        self.disk_total_read_gib: float = 0.0
        self.disk_total_write_gib: float = 0.0
        self.disk_total_ops_m: float = 0.0
        self._last_diskstats_time: float = 0.0
        self._last_disk_reads: int = 0
        self._last_disk_writes: int = 0
        self._last_disk_read_sectors: int = 0
        self._last_disk_write_sectors: int = 0
        self._primary_disk_dev: bytes = b"nvme0n1"

        # Memory bus transfer rates & DRAM power
        self.ram_power_w: float = 1.8
        self.ram_volt_v: float = 1.20
        self.ram_current_a: float = 1.5
        self.ram_speed_gbs: float = 0.0
        self.ram_mops: float = 0.0
        self._last_vm_time: float = 0.0
        self._last_pgalloc: int = 0
        self._last_pgfree: int = 0

        # Load capacity
        self.load_1m_percent: float = 0.0
        self.load_queue_str: str = ""

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
        cand_drv = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        cand_gov = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        self._cpu_drv_path = cand_drv if os.path.exists(cand_drv) else None
        self._cpu_gov_path = cand_gov if os.path.exists(cand_gov) else None

        # 5. AC Online
        ac_cand = "/sys/class/power_supply/AC/online"
        self._ac_path = ac_cand if os.path.exists(ac_cand) else None

        # 6. Battery paths
        self._bat_dir = None
        self._bat_cap_path = None
        self._bat_stat_path = None
        self._bat_volt_path = None
        self._bat_cur_path = None
        try:
            for name in os.listdir("/sys/class/power_supply"):
                if name.startswith("BAT"):
                    b_dir = os.path.join("/sys/class/power_supply", name)
                    self._bat_dir = b_dir
                    p_cap = os.path.join(b_dir, "capacity")
                    p_stat = os.path.join(b_dir, "status")
                    p_volt = os.path.join(b_dir, "voltage_now")
                    p_cur = os.path.join(b_dir, "current_now")
                    self._bat_cap_path = p_cap if os.path.exists(p_cap) else None
                    self._bat_stat_path = p_stat if os.path.exists(p_stat) else None
                    self._bat_volt_path = p_volt if os.path.exists(p_volt) else None
                    self._bat_cur_path = p_cur if os.path.exists(p_cur) else None
                    break
        except Exception:
            pass

        # 7. Primary Storage Device for diskstats
        self._primary_disk_dev = b"nvme0n1"
        try:
            with open("/proc/diskstats", "rb") as df:
                for line in df:
                    parts = line.split()
                    if len(parts) >= 14:
                        dev = parts[2]
                        if dev.startswith(b"nvme") and dev.endswith(b"n1"):
                            self._primary_disk_dev = dev
                            break
                        elif dev.startswith(b"sd") and len(dev) == 3:
                            self._primary_disk_dev = dev
                            break
                        elif dev.startswith(b"vd") and len(dev) == 3:
                            self._primary_disk_dev = dev
                            break
        except Exception:
            pass

    def _trigger_nvme_read(self):
        """Asynchronously query NVMe drive temperature without stalling main thread on PCIe SMART bus."""
        if self._nvme_reading or not self._nvme_temp_path:
            return
        self._nvme_reading = True

        def _worker():
            try:
                with open(self._nvme_temp_path, "r", encoding="utf-8") as f:
                    self.nvme_temp_c = float(f.read().strip()) / 1000.0
            except Exception:
                pass
            finally:
                self._nvme_reading = False

        threading.Thread(target=_worker, daemon=True).start()

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
                f.readline()
                f.readline()
                for line in f:
                    parts = line.split(":", 1)
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

        # 1. CPU Usage (Binary read)
        try:
            with open("/proc/stat", "rb") as f:
                fields = [float(x) for x in f.readline().split()[1:8]]
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

        # 2. CPU Frequencies (Direct binary reads)
        if self._cpu_freq_paths:
            freqs = []
            for fp in self._cpu_freq_paths:
                try:
                    with open(fp, "rb") as f:
                        freqs.append(int(f.read()))
                except Exception:
                    pass
            if freqs:
                self.cpu_freq_avg_ghz = (sum(freqs) / len(freqs)) / 1e6
                self.cpu_freq_max_ghz = max(freqs) / 1e6

        # 3. CPU Temperature
        if self._cpu_temp_path:
            try:
                with open(self._cpu_temp_path, "r") as f:
                    self.cpu_temp_c = float(f.read().strip()) / 1000.0
            except Exception:
                pass

        # 4. Memory & Swap (Binary early-exit parser)
        try:
            total_kb = 0
            avail_kb = 0
            sw_total_kb = 0
            sw_free_kb = 0
            found = 0
            with open("/proc/meminfo", "rb") as f:
                for line in f:
                    if line.startswith(b"MemTotal:"):
                        total_kb = int(line.split()[1])
                        found += 1
                    elif line.startswith(b"MemAvailable:"):
                        avail_kb = int(line.split()[1])
                        found += 1
                    elif line.startswith(b"SwapTotal:"):
                        sw_total_kb = int(line.split()[1])
                        found += 1
                    elif line.startswith(b"SwapFree:"):
                        sw_free_kb = int(line.split()[1])
                        found += 1
                        if found >= 4:
                            break
            if total_kb > 0:
                used_kb = total_kb - avail_kb
                self.mem_total_gib = total_kb / (1024.0 * 1024.0)
                self.mem_avail_gib = avail_kb / (1024.0 * 1024.0)
                self.mem_used_gib = used_kb / (1024.0 * 1024.0)
                self.mem_percent = (used_kb / total_kb) * 100.0
                self.mem_history.append(self.mem_percent)
                sw_used_kb = sw_total_kb - sw_free_kb
                self.swap_total_gib = sw_total_kb / (1024.0 * 1024.0)
                self.swap_used_gib = sw_used_kb / (1024.0 * 1024.0)
                self.swap_percent = (sw_used_kb / sw_total_kb) * 100.0 if sw_total_kb > 0 else 0.0
        except Exception:
            pass

        # 5. GPU Telemetry (Direct open without redundant exists)
        if self._gpu_busy_path:
            try:
                with open(self._gpu_busy_path, "r") as f:
                    self.gpu_percent = max(0.0, min(100.0, float(f.read().strip())))
            except Exception:
                pass
        self.gpu_history.append(self.gpu_percent)

        if self._gpu_vram_used_path and self._gpu_vram_total_path:
            try:
                with open(self._gpu_vram_used_path, "r") as f:
                    self.gpu_vram_used_mib = int(f.read().strip()) / (1024.0 * 1024.0)
                with open(self._gpu_vram_total_path, "r") as f:
                    self.gpu_vram_total_mib = int(f.read().strip()) / (1024.0 * 1024.0)
                if self.gpu_vram_total_mib > 0:
                    self.gpu_vram_percent = (self.gpu_vram_used_mib / self.gpu_vram_total_mib) * 100.0
            except Exception:
                pass

        if self._gpu_gtt_used_path and self._gpu_gtt_total_path:
            try:
                with open(self._gpu_gtt_used_path, "r") as f:
                    self.gpu_gtt_used_gib = int(f.read().strip()) / (1024.0 ** 3)
                with open(self._gpu_gtt_total_path, "r") as f:
                    self.gpu_gtt_total_gib = int(f.read().strip()) / (1024.0 ** 3)
            except Exception:
                pass

        if self._gpu_freq_path:
            try:
                with open(self._gpu_freq_path, "r") as f:
                    self.gpu_clock_mhz = float(f.read().strip()) / 1e6
            except Exception:
                pass

        if self._gpu_temp_path:
            try:
                with open(self._gpu_temp_path, "r") as f:
                    self.gpu_temp_c = float(f.read().strip()) / 1000.0
            except Exception:
                pass

        # 6. Power Draw Breakdown & Electrical Telemetry (Voltage & Current Amps)
        soc_p = 0.0
        if self._gpu_power_path:
            try:
                with open(self._gpu_power_path, "r") as f:
                    soc_p = float(f.read().strip()) / 1e6
            except Exception:
                pass
        self.soc_power_w = max(0.0, soc_p)

        if self.soc_power_w > 0:
            w_gpu = max(0.2, self.gpu_percent) * 1.15
            w_cpu = max(0.2, self.cpu_percent)
            ratio = w_gpu / (w_gpu + w_cpu)
            self.gpu_power_w = round(self.soc_power_w * ratio, 1)
            self.cpu_power_w = round(max(0.0, self.soc_power_w - self.gpu_power_w), 1)
        else:
            self.cpu_power_w = round(4.0 + 15.0 * (self.cpu_percent / 100.0), 1)
            self.gpu_power_w = round(2.5 + 12.0 * (self.gpu_percent / 100.0), 1)
            self.soc_power_w = round(self.cpu_power_w + self.gpu_power_w, 1)

        # GPU Graphics Voltage (vddgfx) and Current Amperage
        if self._gpu_volt_path:
            try:
                with open(self._gpu_volt_path, "r") as vf:
                    val = float(vf.read().strip())
                    self.gpu_volt_v = round(val / 1000.0 if val > 200 else val, 2)
            except Exception:
                pass
        else:
            self.gpu_volt_v = round(0.70 + 0.35 * (self.gpu_percent / 100.0), 2)

        self.gpu_current_a = round(self.gpu_power_w / max(0.4, self.gpu_volt_v), 1)

        # SoC Northbridge Voltage (vddnb) and Current Amperage
        if self._soc_volt_path:
            try:
                with open(self._soc_volt_path, "r") as vf:
                    val = float(vf.read().strip())
                    self.soc_volt_v = round(val / 1000.0 if val > 200 else val, 2)
            except Exception:
                pass
        else:
            self.soc_volt_v = 0.83

        self.soc_current_a = round(self.soc_power_w / max(0.4, self.soc_volt_v), 1)

        # CPU Core Voltage (Vcore) and Current Amperage
        if self._cpu_volt_path:
            try:
                with open(self._cpu_volt_path, "r") as vf:
                    val = float(vf.read().strip())
                    self.cpu_volt_v = round(val / 1000.0 if val > 200 else val, 2)
            except Exception:
                pass
        else:
            v_base = 0.72
            f_ratio = max(0.0, min(1.0, (self.cpu_freq_avg_ghz - 1.4) / (max(2.4, self.cpu_freq_max_ghz) - 1.4)))
            l_ratio = self.cpu_percent / 100.0
            self.cpu_volt_v = round(v_base + 0.46 * f_ratio + 0.12 * l_ratio, 2)

        self.cpu_current_a = round(self.cpu_power_w / max(0.4, self.cpu_volt_v), 1)

        # 7. Battery & AC Power (Direct cached reads)
        try:
            if self._ac_path:
                try:
                    with open(self._ac_path, "r") as f:
                        self.ac_online = f.read().strip() == "1"
                except Exception:
                    self.ac_online = True
            else:
                self.ac_online = True

            if self._bat_dir:
                self.has_battery = True
                if self._bat_cap_path:
                    try:
                        with open(self._bat_cap_path, "r") as f:
                            self.battery_percent = int(f.read().strip())
                    except Exception:
                        pass
                if self._bat_stat_path:
                    try:
                        with open(self._bat_stat_path, "r") as f:
                            self.battery_status = f.read().strip()
                    except Exception:
                        pass

                self.power_source_str = f"AC [{self.battery_status}]" if self.ac_online else "BATTERY"

                volt = 12.0
                cur = 0.0
                if self._bat_volt_path:
                    try:
                        with open(self._bat_volt_path, "r") as vf:
                            volt = float(vf.read().strip()) / 1e6
                            self.bat_volt_v = round(volt, 2)
                    except Exception:
                        pass
                if self._bat_cur_path:
                    try:
                        with open(self._bat_cur_path, "r") as cf:
                            cur = float(cf.read().strip()) / 1e6
                    except Exception:
                        pass
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

        # 8. NVMe Storage Thermal (Non-blocking async worker)
        self._trigger_nvme_read()

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

        # 10. SSD / Disk I/O Rates & Operations (Binary read from diskstats)
        try:
            with open("/proc/diskstats", "rb") as df:
                for line in df:
                    parts = line.split()
                    if len(parts) >= 14 and parts[2] == self._primary_disk_dev:
                        reads = int(parts[3])
                        read_sec = int(parts[5])
                        writes = int(parts[7])
                        write_sec = int(parts[9])

                        if self._last_diskstats_time > 0 and dt > 0:
                            self.disk_read_mb_s = max(0.0, ((read_sec - self._last_disk_read_sectors) * 512 / (1024 * 1024)) / dt)
                            self.disk_write_mb_s = max(0.0, ((write_sec - self._last_disk_write_sectors) * 512 / (1024 * 1024)) / dt)
                            self.disk_read_iops = max(0.0, (reads - self._last_disk_reads) / dt)
                            self.disk_write_iops = max(0.0, (writes - self._last_disk_writes) / dt)

                        self.disk_total_read_gib = (read_sec * 512) / (1024.0 ** 3)
                        self.disk_total_write_gib = (write_sec * 512) / (1024.0 ** 3)
                        self.disk_total_ops_m = (reads + writes) / 1e6

                        self._last_disk_reads = reads
                        self._last_disk_writes = writes
                        self._last_disk_read_sectors = read_sec
                        self._last_disk_write_sectors = write_sec
                        self._last_diskstats_time = now
                        break
        except Exception:
            pass

        # 11. Memory Bus Transfer Rates & DRAM Power (Binary read from vmstat)
        try:
            pgalloc = 0
            pgfree = 0
            with open("/proc/vmstat", "rb") as vf:
                for line in vf:
                    if line.startswith(b"pgalloc_normal ") or line.startswith(b"pgalloc_dma32 "):
                        pgalloc += int(line.split()[1])
                    elif line.startswith(b"pgfree "):
                        pgfree += int(line.split()[1])

            if self._last_vm_time > 0 and dt > 0:
                dp = max(0, pgalloc - self._last_pgalloc)
                df = max(0, pgfree - self._last_pgfree)
                # 4KB per page
                speed_mb = ((dp + df) * 4096 / 2) / (1024 * 1024) / dt
                self.ram_speed_gbs = speed_mb / 1024.0
                self.ram_mops = ((dp + df) / dt) / 1e6

                # Physical model for laptop DDR4/LPDDR4 memory power:
                # Base ~0.85W idle + utilization scaling + dynamic bandwidth scaling
                self.ram_power_w = round(0.85 + 1.20 * (self.mem_percent / 100.0) + 0.90 * min(1.0, self.ram_speed_gbs / 10.0), 1)
                self.ram_current_a = round(self.ram_power_w / max(0.5, self.ram_volt_v), 1)

            self._last_pgalloc = pgalloc
            self._last_pgfree = pgfree
            self._last_vm_time = now
        except Exception:
            pass

        # 12. Disk Usage (sampled every 5 seconds to reduce filesystem metadata query overhead)
        if (now - self._last_disk_time >= 5.0) or force:
            self._last_disk_time = now
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

        # 11. Uptime (Binary read)
        try:
            with open("/proc/uptime", "rb") as f:
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
            if self._cpu_drv_path:
                try:
                    with open(self._cpu_drv_path, "r") as f:
                        drv = f.read().strip()
                except Exception:
                    pass
            if self._cpu_gov_path:
                try:
                    with open(self._cpu_gov_path, "r") as f:
                        gov = f.read().strip()
                except Exception:
                    pass
            if drv and gov:
                self.cpu_governor = f"{drv} [{gov}]"
            elif drv or gov:
                self.cpu_governor = drv or gov
        except Exception:
            pass

        # 15. System Load Averages, Active Tasks & Load Queue Capacity (Binary read)
        try:
            with open("/proc/loadavg", "rb") as f:
                parts = f.read().split()
                if len(parts) >= 4:
                    self.load_avg = f"{parts[0].decode()} · {parts[1].decode()} · {parts[2].decode()}"
                    load_1m = float(parts[0])
                    self.load_1m_percent = (load_1m / max(1, self.cpu_cores)) * 100.0
                    run_proc = parts[3].decode().split("/")
                    if len(run_proc) == 2:
                        self.procs_str = f"{run_proc[0]} Run · {run_proc[1]} Tasks"
                        self.load_queue_str = f"QUEUE: {load_1m:3.1f} RUNNABLE / {self.cpu_cores}C ({self.load_1m_percent:2.0f}%)"
        except Exception:
            pass

