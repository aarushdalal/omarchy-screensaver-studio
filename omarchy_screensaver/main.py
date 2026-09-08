"""Command-line interface and entry point for Omarchy Screensaver.
"""

import argparse
import atexit
import os
import signal
import sys

if __package__ is None or __package__ == "":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from omarchy_screensaver.app import ScreensaverApp
    from omarchy_screensaver.config import Config
    from omarchy_screensaver.modes import AVAILABLE_MODES
    from omarchy_screensaver.theme import ThemeManager
else:
    from .app import ScreensaverApp
    from .config import Config
    from .modes import AVAILABLE_MODES
    from .theme import ThemeManager


def get_running_pid() -> int | None:
    pid_file = Config.PID_FILE
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            # Check if process is still alive
            os.kill(pid, 0)
            return pid
        except (OSError, ValueError):
            try:
                os.remove(pid_file)
            except Exception:
                pass
    return None


def cleanup_stay_awake():
    """Remove stay-awake state indicator if set by ambient screensaver mode."""
    marker = os.path.expanduser("~/.local/state/omarchy/indicators/stay-awake-screensaver")
    stay_awake = os.path.expanduser("~/.local/state/omarchy/indicators/stay-awake")
    if os.path.exists(marker):
        try:
            os.remove(marker)
        except Exception:
            pass
        try:
            if os.path.exists(stay_awake):
                os.remove(stay_awake)
        except Exception:
            pass


atexit.register(cleanup_stay_awake)


def cmd_stop():
    pid = get_running_pid()
    if pid:
        print(f"Stopping Omarchy Screensaver (PID {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            print("Screensaver stopped successfully.")
        except Exception as e:
            print(f"Error stopping screensaver: {e}")
    else:
        print("Omarchy Screensaver is not currently running.")

    cleanup_stay_awake()


def cmd_status():
    pid = get_running_pid()
    cfg = Config.load()
    tm = ThemeManager(cfg.theme, cfg.THEMES_DIR)
    print("Omarchy Screensaver Status")
    print("──────────────────────────────────────────")
    if pid:
        print(f"State         : RUNNING (PID {pid})")
    else:
        print("State         : IDLE (Not running)")
    print(f"Configured Mode: {cfg.mode}")
    print(f"Rotation      : {'Enabled' if cfg.rotation else 'Disabled'} ({cfg.rotation_interval}s)")
    print(f"Active Theme  : {tm.palette.name} ({cfg.theme})")
    print(f"Config File   : {Config.CONFIG_FILE}")
    print(f"Framerate     : {cfg.fps} FPS (AC) / {cfg.battery_fps} FPS (Battery)")
    print(f"Multi-Monitor : {cfg.multi_monitor}")


def cmd_show_config():
    cfg = Config.load()
    print(f"# Location: {Config.CONFIG_FILE}\n")
    if os.path.exists(Config.CONFIG_FILE):
        with open(Config.CONFIG_FILE, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("Default configuration (not yet written to disk).")


def main():
    parser = argparse.ArgumentParser(
        prog="omarchy-screensaver",
        description="A polished, lightweight, highly customizable screensaver for Omarchy Linux.",
    )
    parser.add_argument(
        "-p", "--preview",
        action="store_true",
        help="Launch screensaver in preview mode (press any key or ESC to exit).",
    )
    parser.add_argument(
        "-m", "--mode",
        type=str,
        choices=AVAILABLE_MODES,
        help=f"Force a specific visual mode: {', '.join(AVAILABLE_MODES)}",
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Display real-time diagnostics HUD (FPS, CPU, RAM, theme, monitor).",
    )
    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="Show screensaver running status and active settings.",
    )
    parser.add_argument(
        "-k", "--stop",
        action="store_true",
        help="Stop any currently running screensaver instances.",
    )
    parser.add_argument(
        "-c", "--config",
        action="store_true",
        help="Display current configuration file path and contents.",
    )
    parser.add_argument(
        "-a", "--ambient",
        action="store_true",
        help="Launch screensaver in ambient desk/study mode (inhibits idle sleep and lock; optimized dismissal).",
    )
    parser.add_argument(
        "--class",
        dest="app_class",
        default="org.omarchy.screensaver",
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    if args.stop:
        cmd_stop()
        return

    if args.status:
        cmd_status()
        return

    if args.config:
        cmd_show_config()
        return

    # Check if already running unless in preview mode
    running_pid = get_running_pid()
    if running_pid and not args.preview:
        print(f"[omarchy-screensaver] Already running with PID {running_pid}. Exiting.")
        sys.exit(0)

    config = Config.load()

    # Create and run application
    app = ScreensaverApp(
        config=config,
        forced_mode=args.mode,
        is_preview=args.preview,
        is_debug=args.debug,
        is_ambient=args.ambient,
    )

    sys.exit(app.run(None))


if __name__ == "__main__":
    main()
