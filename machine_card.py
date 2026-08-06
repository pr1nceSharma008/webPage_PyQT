"""
machine_card.py — reusable widget for ONE machine.

NEW CONCEPT: building your own custom widget class
------------------------------------------------------
Just like a React/JS component, you subclass QFrame, build its internal
layout ONCE in __init__, then expose an update_data(machine_dict) method
that mutates the existing widgets in place — same idea as your patchCard()
function, which edits the DOM instead of rebuilding it.
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

import theme
import utils


def glow(color_hex: str, blur: int = 32) -> QGraphicsDropShadowEffect:
    """box-shadow has no QSS equivalent — this Python object fakes it."""
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur)
    effect.setOffset(0, 4)
    color = QColor(color_hex)
    color.setAlpha(110)
    effect.setColor(color)
    return effect


class ShiftCell(QFrame):
    """One of the 3 small shift boxes (Shift 1 / 2 / 3)."""

    def __init__(self, label_text: str, compact: bool = False):
        super().__init__()
        sizes = theme.FONT_SIZES[compact]
        self.setObjectName("shiftCard")
        self.setStyleSheet(theme.SHIFT_CARD_QSS)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 26, 8, 26)

        self.label = QLabel(label_text.upper())
        self.label.setStyleSheet(f"background: transparent; color: {theme.COLORS['slate_300']}; letter-spacing: 2px;")
        self.label.setFont(QFont("Segoe UI", sizes["shift_label"], QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.oee_value = QLabel("NA")
        self.oee_value.setFont(QFont("Segoe UI", sizes["shift_oee"], QFont.Weight.Black))
        self.oee_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.downtime = QLabel("00:00:00")
        self.downtime.setStyleSheet(f"background: transparent; color: {theme.COLORS['slate_300']};")
        self.downtime.setFont(QFont("Consolas", sizes["shift_downtime"], QFont.Weight.Bold))
        self.downtime.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for w in (self.label, self.oee_value, self.downtime):
            layout.addWidget(w)

    def update_value(self, oee: float, downtime_sec: float, visible: bool):
        text = f"{oee:.1f}%" if visible else "NA"
        self.oee_value.setText(text)
        self.oee_value.setStyleSheet(f"background: transparent; color: {theme.shift_value_color(oee, visible)};")
        self.downtime.setText(utils.fmt(downtime_sec) if visible else "00:00:00")


class MachineCard(QFrame):
    def __init__(self, compact: bool = False):
        """compact=True is used when TWO machines are shown side by side
        (equivalent of the .two-machines font-size overrides in your CSS)."""
        super().__init__()
        self.compact = compact
        self.machine_id = None
        self._build_ui()

    def _build_ui(self):
        sizes = theme.FONT_SIZES[self.compact]
        box_min_height = 300 if not self.compact else 260

        outer = QVBoxLayout(self)
        outer.setSpacing(20)
        outer.setContentsMargins(20, 16, 20, 16)

        # ── Machine name ──
        self.name_label = QLabel("—")
        self.name_label.setStyleSheet(theme.MACHINE_NAME_QSS)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setFont(QFont("Segoe UI", sizes["machine_name"], QFont.Weight.Black))
        outer.addWidget(self.name_label)

        # ── Status box + OEE box row ──
        row = QHBoxLayout()
        row.setSpacing(20)

        self.status_box = QFrame()
        self.status_box.setObjectName("statusBox")
        self.status_box.setMinimumHeight(box_min_height)
        sb_layout = QVBoxLayout(self.status_box)
        sb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_text = QLabel("—")
        self.status_text.setFont(QFont("Segoe UI", sizes["status_text"], QFont.Weight.Black))
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stop_reason = QLabel("")
        self.stop_reason.setStyleSheet(f"background: transparent; color: {theme.COLORS['red_400']};")
        self.stop_reason.setFont(QFont("Segoe UI", sizes["stop_reason"], QFont.Weight.Bold))
        self.stop_reason.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stop_reason.setWordWrap(True)
        sb_layout.addWidget(self.status_text)
        sb_layout.addWidget(self.stop_reason)

        self.oee_box = QFrame()
        self.oee_box.setObjectName("oeeBox")
        self.oee_box.setMinimumHeight(box_min_height)
        ob_layout = QVBoxLayout(self.oee_box)
        ob_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        oee_label = QLabel("OEE")
        oee_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['slate_300']}; letter-spacing: 3px;")
        oee_label.setFont(QFont("Segoe UI", sizes["oee_label"], QFont.Weight.Bold))
        oee_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.oee_value = QLabel("0.0%")
        self.oee_value.setFont(QFont("Segoe UI", sizes["oee_value"], QFont.Weight.Black))
        self.oee_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_downtime = QLabel("00:00:00")
        self.total_downtime.setStyleSheet(f"background: transparent; color: {theme.COLORS['slate_200']};")
        self.total_downtime.setFont(QFont("Consolas", sizes["total_downtime"], QFont.Weight.Bold))
        self.total_downtime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for w in (oee_label, self.oee_value, self.total_downtime):
            ob_layout.addWidget(w)

        row.addWidget(self.status_box, 1)
        row.addWidget(self.oee_box, 1)
        outer.addLayout(row)

        # ── Shift row (grid-cols-3) ──
        shifts_row = QHBoxLayout()
        shifts_row.setSpacing(20)
        self.shift1 = ShiftCell("Shift 1", compact=self.compact)
        self.shift2 = ShiftCell("Shift 2", compact=self.compact)
        self.shift3 = ShiftCell("Shift 3", compact=self.compact)
        for cell in (self.shift1, self.shift2, self.shift3):
            shifts_row.addWidget(cell)
        outer.addLayout(shifts_row)

    def update_data(self, m: dict):
        """Equivalent of patchCard(): mutate existing widgets, don't rebuild."""
        self.machine_id = m.get("MachineId")
        self.name_label.setText(m.get("MachineName", "—"))

        running = m.get("Status") == 1
        self.status_box.setStyleSheet(theme.status_box_qss(running))
        self.status_box.setGraphicsEffect(
            glow(theme.COLORS["emerald_500"] if running else theme.COLORS["red_500"])
        )
        self.status_text.setText("Running" if running else "Stop")
        self.status_text.setStyleSheet(
            f"background: transparent; color: {theme.COLORS['green_400'] if running else theme.COLORS['red_400']};"
        )
        self.stop_reason.setText("" if running else (m.get("StoppedReason") or "Unknown"))
        self.stop_reason.setVisible(not running)

        total_downtime = m.get("TotalDowntime", 0)
        oee = utils.total_oee(total_downtime)
        self.oee_box.setStyleSheet(theme.oee_box_qss(oee))
        oee_color = theme.shift_value_color(oee, True)
        self.oee_box.setGraphicsEffect(glow(
            theme.COLORS["emerald_500"] if oee >= 85
            else theme.COLORS["yellow_500"] if oee >= 80
            else theme.COLORS["red_500"]
        ))
        self.oee_value.setText(f"{oee:.1f}%")
        self.oee_value.setStyleSheet(f"background: transparent; color: {oee_color};")
        self.total_downtime.setText(utils.fmt(total_downtime))

        vis = utils.get_shift_visibility()
        self.shift1.update_value(utils.shift_oee(m.get("Shift1_DownTime", 0)), m.get("Shift1_DownTime", 0), vis["s1"])
        self.shift2.update_value(utils.shift_oee(m.get("Shift2_DownTime", 0)), m.get("Shift2_DownTime", 0), vis["s2"])
        self.shift3.update_value(utils.shift_oee(m.get("Shift3_DownTime", 0)), m.get("Shift3_DownTime", 0), vis["s3"])