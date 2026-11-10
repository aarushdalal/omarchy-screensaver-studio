"""Collection settings backend for DAEMON Satisfying studio.

Manages persistent preferences, ordered playlists, favorites, quality profiles,
and parameter updates with atomic validation and preset import/export.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import sys
from typing import Any, Dict, List, Optional, Sequence, Union

from .settings import SPEC, atomic_json, validate, validate_preset

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "omarchy-screensaver" / "satisfying.json"


def default_preset() -> Dict[str, Any]:
    """Generate default v1 preset structure."""
    return {
        "version": 1,
        "quality": "balanced",
        "seed": 1,
        "favorites": [],
        "disabled": [],
        "playlist": [],
        "effects": {},
    }


def load_preferences(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load and validate preset from file path, or return defaults if not found.

    Preserves unrelated metadata keys from existing files.
    """
    target = Path(path) if path else DEFAULT_CONFIG_PATH
    if not target.exists():
        return default_preset()

    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate schema integrity; raises ValueError if malformed
    validate_preset(data)
    return data


def save_preferences(data: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """Atomically validate and save preferences to path.

    Raises ValueError and does NOT touch disk if data fails validation.
    """
    target = Path(path) if path else DEFAULT_CONFIG_PATH
    # Ensure validation occurs before any write
    validated = validate_preset(data)
    atomic_json(target, validated)


class Preferences:
    """Stateful preferences controller supporting atomic mutations and queries."""

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        self.path = Path(path) if path else DEFAULT_CONFIG_PATH
        self.data: Dict[str, Any] = default_preset()
        self.load()

    def load(self) -> None:
        """Reload preferences from path."""
        self.data = load_preferences(self.path)

    def save(self) -> None:
        """Atomically persist current preferences to path."""
        save_preferences(self.data, self.path)

    def toggle_favorite(self, effect: str) -> bool:
        """Toggle an effect in favorites. Returns True if now favorite, False if removed."""
        if effect not in SPEC:
            raise ValueError(f"Unknown effect: {effect}")
        favs = self.data.setdefault("favorites", [])
        if effect in favs:
            favs.remove(effect)
            is_fav = False
        else:
            favs.append(effect)
            is_fav = True
        return is_fav

    def is_favorite(self, effect: str) -> bool:
        return effect in self.data.get("favorites", [])

    def set_enabled(self, effect: str, enabled: bool) -> None:
        """Explicitly enable or disable an effect."""
        if effect not in SPEC:
            raise ValueError(f"Unknown effect: {effect}")
        disabled = self.data.setdefault("disabled", [])
        if enabled and effect in disabled:
            disabled.remove(effect)
        elif not enabled and effect not in disabled:
            disabled.append(effect)

    def toggle_enabled(self, effect: str) -> bool:
        """Toggle effect enabled state. Returns True if now enabled, False if disabled."""
        if effect not in SPEC:
            raise ValueError(f"Unknown effect: {effect}")
        disabled = self.data.setdefault("disabled", [])
        if effect in disabled:
            disabled.remove(effect)
            return True
        else:
            disabled.append(effect)
            return False

    def is_enabled(self, effect: str) -> bool:
        return effect not in self.data.get("disabled", [])

    def set_playlist(self, playlist: Sequence[str]) -> None:
        """Set custom ordered playlist of effect IDs."""
        for eff in playlist:
            if eff not in SPEC:
                raise ValueError(f"Unknown effect in playlist: {eff}")
        self.data["playlist"] = list(playlist)

    def get_playlist(self) -> List[str]:
        return list(self.data.get("playlist", []))

    def get_random_choice(self, seed: Optional[int] = None) -> str:
        """Select a random effect from enabled set, excluding disabled.

        Supports deterministic choice via provided seed or preset seed.
        """
        disabled = set(self.data.get("disabled", []))
        candidates = [eff for eff in sorted(SPEC.keys()) if eff not in disabled]
        if not candidates:
            raise ValueError("No enabled effects available to select")

        choice_seed = seed if seed is not None else self.data.get("seed", 1)
        rng = random.Random(choice_seed)
        return rng.choice(candidates)

    def set_quality(self, quality: str) -> None:
        if quality not in ["eco", "balanced", "quality"]:
            raise ValueError(f"Unknown quality: {quality}")
        self.data["quality"] = quality

    def set_seed(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**24:
            raise ValueError(f"Invalid seed: {seed}")
        self.data["seed"] = seed

    def set_effect_param(self, effect: str, key: str, value: Any) -> None:
        """Set a single parameter for an effect with schema validation."""
        if effect not in SPEC:
            raise ValueError(f"Unknown effect: {effect}")
        effects = self.data.setdefault("effects", {})
        current_params = dict(effects.get(effect, {}))
        current_params[key] = value

        # Validate against schema before applying
        validated = validate(effect, current_params)
        effects[effect] = validated

    def reset_effect(self, effect: str) -> None:
        """Reset custom parameters for a single effect to defaults."""
        if effect not in SPEC:
            raise ValueError(f"Unknown effect: {effect}")
        effects = self.data.get("effects", {})
        if effect in effects:
            del effects[effect]
        # Remove from disabled if present
        disabled = self.data.get("disabled", [])
        if effect in disabled:
            disabled.remove(effect)

    def reset_all(self) -> None:
        """Reset all collection settings while preserving unrelated metadata."""
        defaults = default_preset()
        for k in ["quality", "seed", "favorites", "disabled", "playlist", "effects"]:
            self.data[k] = defaults[k]

    def import_preset(self, source_path: Union[str, Path]) -> None:
        """Import preset from source path.

        Atomic: If incoming data is invalid, raises ValueError and preserves current state.
        """
        with open(source_path, "r", encoding="utf-8") as f:
            incoming = json.load(f)

        validated = validate_preset(incoming)
        # Preserve existing unrelated top-level keys
        unrelated = {
            k: v for k, v in self.data.items()
            if k not in ["version", "quality", "seed", "favorites", "disabled", "playlist", "effects"]
        }
        self.data = {**unrelated, **validated}
        self.save()

    def export_preset(self, dest_path: Union[str, Path]) -> None:
        """Export current validated preset to target destination path."""
        validate_preset(self.data)
        atomic_json(Path(dest_path), self.data)


def _parse_val(raw: str) -> Any:
    """Parse string value into json-compatible Python types."""
    try:
        return json.loads(raw)
    except Exception:
        low = raw.lower()
        if low in ("true", "yes"):
            return True
        if low in ("false", "no"):
            return False
        return raw


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="daemon-satisfying-preferences",
        description="Collection settings backend for DAEMON Satisfying studio.",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Path to preferences JSON file (default: ~/.config/omarchy-screensaver/satisfying.json)",
    )
    parser.add_argument(
        "--toggle-favorite",
        metavar="EFFECT",
        type=str,
        help="Toggle effect in favorites list",
    )
    parser.add_argument(
        "--enable",
        metavar="EFFECT",
        type=str,
        help="Enable a previously disabled effect",
    )
    parser.add_argument(
        "--disable",
        metavar="EFFECT",
        type=str,
        help="Disable an effect from rotation and random selection",
    )
    parser.add_argument(
        "--playlist",
        type=str,
        help="Comma-separated ordered list of effect IDs for custom playlist",
    )
    parser.add_argument(
        "--random-choice",
        action="store_true",
        help="Print a random enabled effect name (excluding disabled)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for deterministic random choice or state seed setting",
    )
    parser.add_argument(
        "--quality",
        choices=["eco", "balanced", "quality"],
        help="Set global quality profile",
    )
    parser.add_argument(
        "--set-param",
        action="append",
        nargs="+",
        metavar="ARG",
        help="Set effect parameter: EFFECT KEY=VALUE or EFFECT:KEY=VALUE",
    )
    parser.add_argument(
        "--reset",
        metavar="EFFECT",
        type=str,
        help="Reset parameters and disabled state for a specific effect",
    )
    parser.add_argument(
        "--reset-all",
        action="store_true",
        help="Reset all effects, favorites, playlist, and quality to defaults",
    )
    parser.add_argument(
        "--import",
        dest="import_path",
        metavar="PATH",
        type=str,
        help="Import and validate preset from file path",
    )
    parser.add_argument(
        "--export",
        dest="export_path",
        metavar="PATH",
        type=str,
        help="Export current validated preferences to file path",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print current preferences JSON to stdout",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    pref = Preferences(args.state)
    modified = False

    try:
        if args.import_path:
            pref.import_preset(args.import_path)
            modified = False  # import_preset already saves

        if args.toggle_favorite:
            state = pref.toggle_favorite(args.toggle_favorite)
            print(f"Favorite {args.toggle_favorite}: {'added' if state else 'removed'}")
            modified = True

        if args.enable:
            pref.set_enabled(args.enable, True)
            print(f"Enabled {args.enable}")
            modified = True

        if args.disable:
            pref.set_enabled(args.disable, False)
            print(f"Disabled {args.disable}")
            modified = True

        if args.playlist is not None:
            items = [item.strip() for item in args.playlist.split(",") if item.strip()]
            pref.set_playlist(items)
            print(f"Playlist set ({len(items)} items)")
            modified = True

        if args.quality:
            pref.set_quality(args.quality)
            print(f"Quality set: {args.quality}")
            modified = True

        if args.seed is not None and not args.random_choice:
            pref.set_seed(args.seed)
            print(f"Seed set: {args.seed}")
            modified = True

        if args.set_param:
            for item in args.set_param:
                if len(item) == 2:
                    eff, kv = item[0], item[1]
                elif len(item) == 1 and ":" in item[0]:
                    eff, kv = item[0].split(":", 1)
                elif len(item) == 1 and "=" in item[0]:
                    # Format: EFFECT.KEY=VALUE
                    part1, val = item[0].split("=", 1)
                    eff, key = part1.split(".", 1) if "." in part1 else (part1, "")
                    kv = f"{key}={val}"
                else:
                    raise ValueError(f"Malformed set-param argument: {' '.join(item)}")

                if "=" not in kv:
                    raise ValueError(f"Expected KEY=VALUE, got {kv}")
                key, val_str = kv.split("=", 1)
                pref.set_effect_param(eff, key, _parse_val(val_str))
                print(f"Set parameter for {eff}: {key}={val_str}")
            modified = True

        if args.reset:
            pref.reset_effect(args.reset)
            print(f"Reset {args.reset} to defaults")
            modified = True

        if args.reset_all:
            pref.reset_all()
            print("Reset all settings to defaults")
            modified = True

        if args.export_path:
            pref.export_preset(args.export_path)
            print(f"Exported preset to {args.export_path}")

        if modified:
            pref.save()

        if args.random_choice:
            choice = pref.get_random_choice(args.seed)
            print(choice)

        if args.show or (len(sys.argv) == 1 if argv is None else len(argv) == 0):
            print(json.dumps(pref.data, indent=2))

        return 0

    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
