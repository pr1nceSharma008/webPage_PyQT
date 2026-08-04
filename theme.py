"""
theme.py — the PyQt equivalent of your tailwind.config + <style> block.

Instead of "text-sky-400" you'll write COLORS["sky_400"].
Instead of a CSS class like ".st-running" you'll call a function like
status_box_qss(running=True) that RETURNS a QSS string.

This is the pattern real PyQt apps use to avoid copy-pasting color hex
codes everywhere — one source of truth, same as a Tailwind config.
"""

COLORS = {
    "slate_900": "#0f172a",
    "slate_800": "#1e293b",
    "slate_700": "#334155",
    "slate_600": "#475569",
    "slate_300": "#cbd5e1",
    "slate_200": "#e2e8f0",
    "slate_400_txt": "#c5cdd8",   # used for inactive shift text (soee-na)
    "gray_100": "#f3f4f6",
    "gray_200": "#e5e7eb",
    "gray_500": "#6b7280",
    "sky_400": "#38bdf8",
    "sky_500": "#0ea5e9",
    "indigo_400": "#818cf8",
    "emerald_500": "#10b981",
    "green_400": "#4ade80",
    "green_600": "#16a34a",
    "red_500": "#ef4444",
    "red_400": "#f87171",
    "red_700": "#b91c1c",
    "yellow_500": "#eab308",
    "yellow_400": "#facc15",
    "white": "#ffffff",
    "black": "#000000",
}

# ── Page background: solid bg-slate-800 ──
PAGE_BG_QSS = f"""
QWidget#pageRoot {{
    background-color: {COLORS['slate_800']};
}}
"""

# ── Navbar: bg-gradient-to-r from-gray-100 to-gray-200, border-b-4 border-gray-500 ──
NAVBAR_QSS = f"""
QFrame#navbar {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['gray_100']}, stop:1 {COLORS['gray_200']}
    );
    border-bottom: 4px solid {COLORS['gray_500']};
}}
"""


def status_box_qss(running: bool) -> str:
    """Equivalent of .st-running / .st-stopped classes."""
    color = COLORS["emerald_500"] if running else COLORS["red_500"]
    return f"""
        QFrame#statusBox {{
            background-color: rgba(30, 41, 59, 0.9);
            border: 3px solid {color};
            border-radius: 16px;
        }}
    """


def oee_box_qss(value: float) -> str:
    """Equivalent of .oee-good / .oee-med / .oee-bad based on OEE %."""
    if value >= 85:
        color = COLORS["emerald_500"]
    elif value >= 80:
        color = COLORS["yellow_500"]
    else:
        color = COLORS["red_500"]
    return f"""
        QFrame#oeeBox {{
            background-color: rgba(30, 41, 59, 0.9);
            border: 3px solid {color};
            border-radius: 16px;
        }}
    """


def shift_value_color(value: float, visible: bool) -> str:
    """Equivalent of .soee-good/.soee-med/.soee-bad/.soee-na — text color only."""
    if not visible:
        return COLORS["slate_400_txt"]
    if value >= 85:
        return COLORS["green_400"]
    if value >= 80:
        return COLORS["yellow_400"]
    return COLORS["red_400"]


SHIFT_CARD_QSS = f"""
QFrame#shiftCard {{
    background-color: rgba(30, 41, 59, 0.9);
    border: 2px solid rgba(71, 85, 105, 0.6);
    border-radius: 12px;
}}
"""

MACHINE_NAME_QSS = f"background: transparent; color: {COLORS['sky_400']}; font-weight: 800;"