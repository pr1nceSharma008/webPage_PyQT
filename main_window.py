"""
main_window.py — navbar + the container that shows 1 or 2 MachineCards.

NEW CONCEPT: rebuilding a layout at runtime
------------------------------------------------
Your JS checks `existing !== list.length` to decide full rebuild vs patch.
We do the same: if the number of machine cards changes, we clear the
container layout and rebuild; otherwise we just call update_data() on the
cards already there (cheap, no flicker) — same "patch, don't rebuild"
philosophy as your patchCard().
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation

import theme
from machine_card import MachineCard


class LiveIndicator(QWidget):
    """The pulsing green/red dot + Online/Offline text."""

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.dot = QLabel()
        self.dot.setFixedSize(12, 12)
        self.text = QLabel("Online")
        self.text.setStyleSheet(f"background: transparent; color: {theme.COLORS['black']}; font-weight: 600;")

        layout.addWidget(self.dot)
        layout.addWidget(self.text)

        # Pulse animation — the PyQt version of Tailwind's animate-pulse-dot
        self._opacity_effect = QGraphicsOpacityEffect(self.dot)
        self.dot.setGraphicsEffect(self._opacity_effect)
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._anim.setDuration(1000)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.4)
        self._anim.setLoopCount(-1)  # infinite, like CSS "infinite"

        self.set_online(True)

    def set_online(self, online: bool):
        color = theme.COLORS["green_600"] if online else theme.COLORS["red_700"]
        self.dot.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
        self.text.setText("Online" if online else "Offline")
        if online:
            self._anim.setDirection(QPropertyAnimation.Direction.Forward)
            self._anim.start()
        else:
            self._anim.stop()
            self._opacity_effect.setOpacity(1.0)


class Navbar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("navbar")
        self.setStyleSheet(theme.NAVBAR_QSS)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)

        self.logo_label = QLabel("Höganäs")
        self.logo_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['sky_500']}; font-weight: 900; font-size: 18px;")

        title = QLabel("Digital-Sync | Machine Monitoring")
        title.setStyleSheet(f"background: transparent; color: {theme.COLORS['black']}; font-weight: 800; font-size: 22px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.live = LiveIndicator()

        right_box = QVBoxLayout()
        right_box.setSpacing(0)
        time_row = QHBoxLayout()
        self.clock_label = QLabel("")
        self.clock_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['black']}; font-weight: 700; font-family: Consolas;")
        self.date_label = QLabel("")
        self.date_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['black']}; font-weight: 600;")
        time_row.addWidget(self.clock_label)
        time_row.addWidget(self.date_label)
        self.ip_label = QLabel("IP: —")
        self.ip_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['black']}; font-size: 10px;")
        self.ip_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_box.addLayout(time_row)
        right_box.addWidget(self.ip_label)

        right_wrap = QHBoxLayout()
        right_wrap.setSpacing(20)
        right_wrap.addWidget(self.live)
        right_wrap.addLayout(right_box)

        layout.addWidget(self.logo_label)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addLayout(right_wrap)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S "))
        self.date_label.setText(now.strftime("%b %d, %Y"))

    def set_ip(self, ip: str):
        self.ip_label.setText(f"IP: {ip}")


class DividerLine(QFrame):
    """Equivalent of your .divider-v gradient line between two machine cards."""

    def __init__(self):
        super().__init__()
        self.setFixedWidth(3)
        self.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 transparent,
                stop:0.5 rgba(255,255,255,0.35),
                stop:1 transparent);
        """)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageRoot")
        self.setStyleSheet(theme.PAGE_BG_QSS)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.cards = {}  # machine_id -> MachineCard

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.navbar = Navbar()
        outer.addWidget(self.navbar)

        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(20, 20, 20, 20)
        self.container_layout.setSpacing(0)
        outer.addWidget(self.container, 1)

        self.empty_label = QLabel("No machine data available")
        self.empty_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['white']}; font-size: 24px; font-weight: bold;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_ip(self, ip: str):
        self.navbar.set_ip(ip)

    def set_online(self, online: bool):
        self.navbar.live.set_online(online)

    def render_machines(self, machines: list):
        """Equivalent of renderMachines(): filters enabled, keeps max 2,
        rebuilds layout only if the machine COUNT changed."""
        enabled = [m for m in machines if m.get("IsEnabled")][:2]

        if not enabled:
            self._clear_container()
            self.container_layout.addWidget(self.empty_label)
            self.cards = {}
            return

        current_ids = list(self.cards.keys())
        new_ids = [m.get("MachineId") for m in enabled]

        if len(current_ids) != len(enabled):
            # Full rebuild — machine count changed (1 <-> 2)
            self._clear_container()
            self.cards = {}
            compact = len(enabled) == 2
            for i, m in enumerate(enabled):
                card = MachineCard(compact=compact)
                card.update_data(m)
                self.cards[m.get("MachineId")] = card
                self.container_layout.addWidget(card, 1)
                if compact and i == 0:
                    self.container_layout.addWidget(DividerLine())
        else:
            # Patch existing cards in place — no rebuild, no flicker
            for m in enabled:
                mid = m.get("MachineId")
                if mid in self.cards:
                    self.cards[mid].update_data(m)

    def _clear_container(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()