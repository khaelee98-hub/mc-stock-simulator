"""
Font/display configuration persistence (V2).

Manages user preferences for font family, monospace font, and font scale.
Persists to config.json in the script directory.
"""

import json
import os
import platform
import tkinter as tk

# ── Paths ──
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ── Base font sizes (scale=100%) ──
BASE_FONT_SIZES = {
    "FONT_TITLE":   18,
    "FONT_SECTION": 14,
    "FONT_BODY":    13,
    "FONT_INPUT":   13,
    "FONT_SMALL":   11,
    "FONT_MONO":    10,
    "FONT_STATUS":  12,
}

# ── Font candidates ──
FONT_CANDIDATES = [
    "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo",
    "Noto Sans KR", "NanumGothic", "나눔고딕",
    "Segoe UI", "Arial", "Helvetica", "Verdana", "Tahoma", "Roboto",
]

MONO_FONT_CANDIDATES = [
    "Consolas", "Cascadia Code", "JetBrains Mono", "D2Coding",
    "Courier New", "Menlo", "Monaco", "Source Code Pro", "Fira Code",
]


def _default_font_family():
    """Return platform-specific default Korean font."""
    system = platform.system()
    if system == "Windows":
        return "Malgun Gothic"
    elif system == "Darwin":
        return "Apple SD Gothic Neo"
    else:
        return "Noto Sans KR"


def _default_config():
    """Return default configuration dict."""
    return {
        "font_family": _default_font_family(),
        "mono_font": "Consolas",
        "font_scale": 100,
    }


def _get_available_fonts():
    """Return set of available font families on this system."""
    try:
        root = tk._default_root
        if root is None:
            root = tk.Tk()
            root.withdraw()
            families = set(tk.font.families())
            root.destroy()
        else:
            families = set(tk.font.families())
        return families
    except Exception:
        return set()


def get_available_font_candidates():
    """Return list of font candidates available on this system."""
    available = _get_available_fonts()
    if not available:
        return FONT_CANDIDATES[:1]
    return [f for f in FONT_CANDIDATES if f in available] or FONT_CANDIDATES[:1]


def get_available_mono_candidates():
    """Return list of mono font candidates available on this system."""
    available = _get_available_fonts()
    if not available:
        return MONO_FONT_CANDIDATES[:1]
    return [f for f in MONO_FONT_CANDIDATES if f in available] or MONO_FONT_CANDIDATES[:1]


def load_config():
    """Load config from config.json. Returns default if file missing or invalid."""
    default = _default_config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults for missing keys
        for key, val in default.items():
            if key not in data:
                data[key] = val
        # Clamp font_scale
        data["font_scale"] = max(80, min(150, int(data["font_scale"])))
        return data
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return default


def save_config(config):
    """Save config dict to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def compute_fonts(config):
    """Compute 7 font tuples + family names from config.

    Returns:
        dict with keys: FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_INPUT,
                        FONT_SMALL, FONT_MONO, FONT_STATUS,
                        font_family, mono_font
    """
    family = config.get("font_family", _default_font_family())
    mono = config.get("mono_font", "Consolas")
    scale = config.get("font_scale", 100)

    def scaled(base):
        return max(8, round(base * scale / 100))

    return {
        "FONT_TITLE":   (family, scaled(BASE_FONT_SIZES["FONT_TITLE"]), "bold"),
        "FONT_SECTION": (family, scaled(BASE_FONT_SIZES["FONT_SECTION"]), "bold"),
        "FONT_BODY":    (family, scaled(BASE_FONT_SIZES["FONT_BODY"])),
        "FONT_INPUT":   (family, scaled(BASE_FONT_SIZES["FONT_INPUT"])),
        "FONT_SMALL":   (family, scaled(BASE_FONT_SIZES["FONT_SMALL"])),
        "FONT_MONO":    (mono,   scaled(BASE_FONT_SIZES["FONT_MONO"])),
        "FONT_STATUS":  (family, scaled(BASE_FONT_SIZES["FONT_STATUS"])),
        "font_family":  family,
        "mono_font":    mono,
    }
