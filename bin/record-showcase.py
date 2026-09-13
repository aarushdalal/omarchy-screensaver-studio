#!/usr/bin/env python3
"""
==============================================================================
  OMARCHY SCREENSAVER STUDIO - DYNAMIC SHOWCASE RECORDER
==============================================================================
Showcase recording for each screensaver mode:
  1. Set visual mode dynamically in config
  2. Trigger ambient screensaver via Super + I (omarchy-screensaver-toggle)
  3. WAIT until screensaver surface is active & displayed
  4. Dismiss all notification toasts (omarchy-shell notifications dismissAll)
  5. START GPU hardware VAAPI recorder (60 FPS, H.264)
  6. Record 5-second pure, spotless screensaver sample
  7. STOP GPU recorder and finalize video file
  8. DISMISS screensaver via Super + I toggle (omarchy-screensaver-toggle)
  9. Settle desktop and advance to next mode
  10. Restore initial screensaver mode on completion or interruption

Features:
  - 100% Dynamic Discovery: Automatically finds all modes (all 10 modes).
  - Spotless Visual Recording: Only records when screensaver is displayed; zero toasts.
  - SIGHUP & SIGPIPE Immune: Continues running even if terminal is closed.
  - Symmetrical Super + I Toggling: Uses identical command path as user shortcut.
  - Hardware-Accelerated VAAPI: Zero dropped frames at 60 FPS via gpu-screen-recorder.
==============================================================================
"""

import os
import sys
import time
import json
import signal
import argparse
import subprocess
from pathlib import Path

# Paths
BIN_DIR = Path(__file__).resolve().parent
REPO_ROOT = BIN_DIR.parent
MODES_DIR = REPO_ROOT / "omarchy_screensaver" / "modes"
OUTPUT_DIR = REPO_ROOT / "assets" / "showcase"
LOG_PATH = OUTPUT_DIR / "execution.log"

# Ignore SIGHUP and SIGPIPE so terminal closure never interrupts execution
signal.signal(signal.SIGHUP, signal.SIG_IGN)
try:
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except Exception:
    pass

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

initial_mode = None

def log(msg, level="INFO"):
    colors = {
        "INFO": Colors.CYAN,
        "STEP": Colors.GREEN + Colors.BOLD,
        "WARN": Colors.YELLOW,
        "ERR": Colors.RED + Colors.BOLD
    }
    col = colors.get(level, Colors.CYAN)
    log_line = f"[{level}] {msg}"
    
    try:
        print(f"{col}{log_line}{Colors.RESET}", flush=True)
    except (BrokenPipeError, OSError):
        pass

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {log_line}\n")
            f.flush()
    except Exception:
        pass

def notify(title, msg, urgency="normal"):
    """Send a desktop notification."""
    for tool in ["omarchy-notification-send", "notify-send"]:
        try:
            if tool == "omarchy-notification-send":
                subprocess.run([tool, "-g", "󱄄", "-t", "3000", title, msg], capture_output=True, check=False)
                return
            else:
                subprocess.run([tool, "-a", "Omarchy Screensaver Showcase", "-t", "3000", title, msg], capture_output=True, check=False)
                return
        except Exception:
            continue

def run_cmd(cmd_list, check=False):
    try:
        return subprocess.run(cmd_list, check=check, capture_output=True, text=True)
    except Exception as e:
        log(f"Command failed {cmd_list}: {e}", "WARN")
        return None

def get_primary_monitor():
    """Dynamically get the active or primary monitor name."""
    try:
        res = run_cmd(["hyprctl", "monitors", "-j"])
        if res and res.stdout:
            monitors = json.loads(res.stdout)
            for m in monitors:
                if m.get("focused"):
                    return m.get("name", "eDP-1")
            if monitors:
                return monitors[0].get("name", "eDP-1")
    except Exception:
        pass
    return "eDP-1"

def discover_modes():
    """Dynamically discover all available screensaver visual modes."""
    modes = []
    # 1. Try omarchy-screensaver-select list-modes
    res = run_cmd(["omarchy-screensaver-select", "list-modes"])
    if res and res.stdout.strip():
        for line in res.stdout.strip().splitlines():
            m = line.strip()
            if m and m not in modes:
                modes.append(m)
                
    # 2. Inspect modes directory in python package
    if MODES_DIR.exists():
        for f in MODES_DIR.glob("*.py"):
            name = f.stem
            if name and not name.startswith("_") and name not in ["base", "common"] and name not in modes:
                modes.append(name)
                
    # Fallback to known modes if empty
    if not modes:
        modes = ["aurora", "clock", "geometry", "matrix", "particles", "singularity", "system", "terminal", "visualizer", "warp"]
        
    return sorted(modes)

def get_current_mode():
    """Get currently active screensaver mode."""
    res = run_cmd(["omarchy-screensaver-select", "mode"])
    if res and res.stdout.strip():
        return res.stdout.strip()
    return "warp"

def set_mode(mode):
    """Set active screensaver mode in config."""
    # Write directly to config to avoid extra notifications during capture
    import re
    cfg_file = Path.home() / ".config" / "omarchy-screensaver" / "config.toml"
    if cfg_file.exists():
        try:
            content = cfg_file.read_text(encoding="utf-8")
            new_content = re.sub(r'mode\s*=\s*"[^"]+"', f'mode = "{mode}"', content)
            cfg_file.write_text(new_content, encoding="utf-8")
        except Exception:
            pass
    # Also inform select CLI
    res = run_cmd(["omarchy-screensaver-select", "mode", mode])
    return res and res.returncode == 0

def is_screensaver_running():
    res = run_cmd(["pgrep", "-f", "[o]rg.omarchy.screensaver"])
    return bool(res and res.stdout.strip())

def wait_for_screensaver_active(timeout=5.0):
    """Wait until screensaver window is mapped, visible, fullscreen and active."""
    start = time.time()
    while time.time() - start < timeout:
        res = run_cmd(["hyprctl", "clients", "-j"])
        if res and res.stdout:
            try:
                clients = json.loads(res.stdout)
                for c in clients:
                    initial_class = c.get("initialClass", "").lower()
                    cls = c.get("class", "").lower()
                    mapped = c.get("mapped", False)
                    hidden = c.get("hidden", False)
                    fullscreen = c.get("fullscreen", 0)
                    if ("screensaver" in initial_class or "screensaver" in cls) and mapped and not hidden and fullscreen >= 1:
                        return True
            except Exception:
                pass
        time.sleep(0.05)
    return False

def toggle_screensaver(mode=None):
    """Trigger Super + I screensaver toggle script."""
    toggle_script = Path.home() / ".local" / "bin" / "omarchy-screensaver-toggle"
    cmd = [str(toggle_script)] if toggle_script.exists() else ["omarchy-screensaver-toggle"]
    if mode:
        cmd.append(f"--mode={mode}")
    run_cmd(cmd)

def dismiss_all_toasts():
    """Dismiss any overlay toast notifications immediately."""
    run_cmd(["omarchy-shell", "notifications", "dismissAll"])

def force_stop_screensaver():
    """Ensure screensaver is fully stopped and clean state."""
    run_cmd(["omarchy-screensaver-stop"])
    run_cmd(["pkill", "-TERM", "-f", "[o]rg.omarchy.screensaver"])
    pid_file = Path.home() / ".config" / "omarchy-screensaver" / "screensaver.pid"
    if pid_file.exists():
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:
            pass
    time.sleep(0.4)

def cleanup():
    """Ensure screensaver is dismissed and original mode restored."""
    global initial_mode
    log("Cleaning up screensaver state...", "INFO")
    
    if is_screensaver_running():
        force_stop_screensaver()
    dismiss_all_toasts()
    
    if initial_mode:
        log(f"Restoring initial screensaver mode: {initial_mode}", "INFO")
        set_mode(initial_mode)

def sig_handler(sig, frame):
    log("Interrupted! Cleaning up safely...", "WARN")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

def record_mode_showcase(mode, monitor, duration=5.0, gen_gif=False, dry_run=False, audio_path=None):
    """Record pure sample for a single screensaver mode only when displayed."""
    output_video = OUTPUT_DIR / f"showcase_screensaver_{mode}.mp4"
    output_gif = OUTPUT_DIR / f"showcase_screensaver_{mode}.gif"

    log(f"▶ [{mode.upper()}] Preparing screensaver showcase capture ({duration}s)...", "STEP")
    
    # 1. Select mode in config
    set_mode(mode)
    time.sleep(0.3)
    
    # 2. Make sure screensaver is not already running
    if is_screensaver_running():
        force_stop_screensaver()
        time.sleep(0.5)

    if dry_run:
        log(f"  [Dry Run] Would record to {output_video.name}", "INFO")
        return output_video

    audio_proc = None
    # Strictly play audio ONLY for visualizer mode!
    if mode == "visualizer":
        song_candidate = audio_path
        if not song_candidate or not Path(song_candidate).exists():
            default_song = Path.home() / "Music" / "music" / "09 - Baggh-E SMG, Farmaan SMG & BIG KAY SMG - C.R.E.A.M POSSE.flac"
            if default_song.exists():
                song_candidate = str(default_song)
                
        if song_candidate and Path(song_candidate).exists():
            log(f"  Starting audio playback for visualizer: {Path(song_candidate).name}...", "INFO")
            audio_proc = subprocess.Popen(
                ["mpv", "--no-video", "--really-quiet", "--volume=85", str(song_candidate)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(1.2) # Allow PipeWire buffer & MPRIS metadata registration
        else:
            log("  ✗ Audio visualizer requires an active song! Pass --audio <path> to specify the track.", "WARN")
            return output_video

    # 3. TRIGGER SCREENSAVER FIRST (Super + I shortcut command)
    log(f"  Triggering ambient screensaver via Super + I: mode={mode}...", "INFO")
    toggle_screensaver(mode=mode)
    
    # 4. WAIT UNTIL SCREENSAVER IS DISPLAYED AND VISIBLE ON SCREEN
    log(f"  Waiting for screensaver surface to be displayed...", "INFO")
    if not wait_for_screensaver_active(timeout=6.0):
        log(f"  ✗ Screensaver surface not detected on screen for mode: {mode}! Skipping.", "ERR")
        if audio_proc:
            audio_proc.terminate()
            audio_proc.wait()
        return output_video
    time.sleep(0.5) # Allow GTK4 Cairo surface to render and begin animation loop
    
    # 5. Dismiss any notification toasts so the recording is 100% spotless!
    dismiss_all_toasts()
    time.sleep(0.3)

    # 6. START GPU SCREEN RECORDER ONLY ONCE DISPLAYED & SPOTLESS!
    log(f"  Screensaver is active on screen! Recording {duration}s sample...", "INFO")
    rec_cmd = [
        "gpu-screen-recorder",
        "-w", monitor,
        "-f", "60",
        "-k", "h264",
        "-q", "very_high",
        "-fallback-cpu-encoding", "yes",
        "-o", str(output_video)
    ]
    recorder = subprocess.Popen(rec_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.6) # Allow GSR to connect KMS socket and lock frame buffer

    try:
        # Capture exactly the duration of the screensaver running
        time.sleep(duration)
    finally:
        # 7. STOP RECORDER FIRST AND ENSURE FULLY CLOSED BEFORE TOUCHING SCREENSAVER!
        recorder.send_signal(signal.SIGINT)
        try:
            recorder.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            recorder.kill()
            recorder.wait()

        # Stop audio playback immediately when visualizer recording finishes!
        if audio_proc:
            audio_proc.terminate()
            try:
                audio_proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                audio_proc.kill()
                audio_proc.wait()
            log("  Audio playback terminated.", "INFO")

    # Settle cleanly so recording file descriptor is flushed and closed
    time.sleep(0.5)

    # 8. DISMISS SCREENSAVER VIA SUPER + I TOGGLE AFTER RECORDING HAS STOPPED
    log(f"  Recording complete! Dismissing screensaver via Super + I toggle...", "INFO")
    toggle_screensaver()
    time.sleep(0.6)
    
    if is_screensaver_running():
        force_stop_screensaver()
        time.sleep(0.3)

    if output_video.exists() and output_video.stat().st_size > 0:
        log(f"  ✓ Saved: {output_video.name} ({output_video.stat().st_size // 1024} KB)", "STEP")
        if gen_gif:
            log(f"  Generating GIF: {output_gif.name}...", "INFO")
            gif_cmd = [
                "ffmpeg", "-y", "-i", str(output_video),
                "-vf", "fps=15,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                str(output_gif)
            ]
            run_cmd(gif_cmd)
            if output_gif.exists():
                log(f"  ✓ GIF Generated: {output_gif.name}", "STEP")
    else:
        log(f"  ✗ Failed to record screensaver mode: {mode}", "ERR")

    return output_video

def main():
    global initial_mode
    
    parser = argparse.ArgumentParser(description="Omarchy Screensaver Studio Automated Showcase Recorder")
    parser.add_argument("--all", action="store_true", help="Record showcase for all discovered modes")
    parser.add_argument("--only", nargs="+", help="Record showcase only for specified mode(s)")
    parser.add_argument("--duration", type=float, default=5.0, help="Recording duration per screensaver mode (seconds, default 5s)")
    parser.add_argument("--countdown", type=int, default=5, help="Grace period countdown before start (seconds)")
    parser.add_argument("--no-countdown", action="store_true", help="Skip countdown grace period")
    parser.add_argument("--gif", action="store_true", help="Also generate optimized GIF versions")
    parser.add_argument("--list", action="store_true", help="List all dynamically discovered modes and exit")
    parser.add_argument("--dry-run", action="store_true", help="Simulate sequence without recording")
    parser.add_argument("--audio", type=str, default="", help="Audio file path to play during visualizer mode recording")
    args = parser.parse_args()

    # Discover modes dynamically
    all_modes = discover_modes()
    
    if args.list:
        print(f"\n{Colors.BOLD}Dynamically Discovered Screensaver Modes ({len(all_modes)} total):{Colors.RESET}")
        for m in all_modes:
            print(f"  • {m}")
        sys.exit(0)

    # Determine target modes: defaults to ALL modes unless --only is given
    if args.only:
        targets = [m for m in args.only if m in all_modes]
        if not targets:
            log(f"None of specified modes {args.only} found. Available: {all_modes}", "ERR")
            sys.exit(1)
    else:
        targets = all_modes

    # Record initial state
    initial_mode = get_current_mode()
    monitor = get_primary_monitor()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 70, "INFO")
    log("  🎬 OMARCHY SCREENSAVER STUDIO SHOWCASE RECORDER (DYNAMIC)", "INFO")
    log(f"  Monitor: {monitor} | Total Modes to Record: {len(targets)}", "INFO")
    log(f"  Modes: {', '.join(targets)}", "INFO")
    if "visualizer" in targets and args.audio:
        log(f"  Visualizer Audio Track: {Path(args.audio).name}", "INFO")
    log(f"  Output Directory: {OUTPUT_DIR}", "INFO")
    log(f"  Initial Mode: {initial_mode} (Will be restored automatically)", "INFO")
    log("=" * 70, "INFO")

    # Countdown grace period
    countdown = 0 if args.no_countdown else args.countdown
    if countdown > 0:
        log(f"⏳ Grace period: {countdown}s to close or minimize terminal windows...", "WARN")
        notify("Omarchy Screensaver Showcase", f"Recording starts in {countdown}s for {len(targets)} modes. You can close your terminal now!")
        for c in range(countdown, 0, -1):
            try:
                print(f"\r  🕒 Starting in {c} seconds... (Close this terminal anytime)\r", end="", flush=True)
            except Exception:
                pass
            time.sleep(1.0)
        try:
            print("\n")
        except Exception:
            pass

    # Main recording loop across ALL modes
    successful = 0
    try:
        for idx, mode in enumerate(targets, 1):
            log(f"[{idx}/{len(targets)}] Processing mode: {mode}...", "INFO")
            out = record_mode_showcase(
                mode,
                monitor=monitor,
                duration=args.duration,
                gen_gif=args.gif,
                dry_run=args.dry_run,
                audio_path=args.audio
            )
            if out.exists() or args.dry_run:
                successful += 1
            time.sleep(1.0) # Settle desktop cleanly between modes
    finally:
        cleanup()

    log("=" * 70, "INFO")
    log(f"✨ Finished recording! {successful}/{len(targets)} modes successfully recorded.", "STEP")
    log(f"All files saved to: {OUTPUT_DIR}", "INFO")
    notify("Omarchy Screensaver Showcase", f"Completed! {successful}/{len(targets)} modes recorded.")

if __name__ == "__main__":
    main()
