"""
loading_screen.py — the 30-second startup countdown overlay.

NEW CONCEPT: QPainter + paintEvent()
----------------------------------------
Your SVG <circle> progress ring has no direct PyQt widget. So we override
paintEvent(), which Qt calls automatically anytime the widget needs to
redraw itself, and use QPainter (Qt's drawing API — think of it like
<canvas> 2D context) to draw the ring by hand every frame.

NEW CONCEPT: QTimer for animation/countdown
------------------------------------------------
setInterval(fn, 1000) in JS becomes QTimer with .timeout.connect(fn) and
.start(1000) in PyQt. Same idea, same signal/slot pattern again.
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QConicalGradient

import theme

LOADING_DURATION = 30  # seconds — matches your JS LOADING_DURATION

LOAD_MESSAGES = [
    "Connecting to machine data…",
    "Fetching live OEE metrics…",
    "Loading shift performance…",
    "Syncing machine states…",
    "Almost ready…",
]


class CountdownRing(QWidget):
    """The circular progress ring, hand-drawn with QPainter."""

    def __init__(self, size=220):
        super().__init__()
        self.setFixedSize(size, size)
        self._fraction = 0.0  # 0 = just started, 1 = complete

    def set_fraction(self, fraction: float):
        self._fraction = max(0.0, min(1.0, fraction))
        self.update()  # schedules a repaint — like calling setState() in React

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(10, 10, self.width() - 20, self.height() - 20)

        # Track (background circle) — like your faint SVG track circle
        track_pen = QPen(QColor(56, 189, 248, 25))
        track_pen.setWidth(6)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(rect)

        # Progress arc — gradient from sky-400 to indigo-400, like your SVG linearGradient
        gradient = QConicalGradient(rect.center(), 90)
        gradient.setColorAt(0.0, QColor(theme.COLORS["sky_400"]))
        gradient.setColorAt(1.0, QColor(theme.COLORS["indigo_400"]))
        arc_pen = QPen(QColor(theme.COLORS["sky_400"]))
        arc_pen.setBrush(gradient)
        arc_pen.setWidth(6)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)

        span_degrees = int(360 * self._fraction)
        # Qt angles: start at 90° (top), go clockwise (negative direction)
        painter.drawArc(rect, 90 * 16, -span_degrees * 16)


class LoadingScreen(QWidget):
    finished = pyqtSignal()  # emitted when the 30s countdown completes

    def __init__(self):
        super().__init__()
        self._remaining = LOADING_DURATION
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def _build_ui(self):
        self.setObjectName("pageRoot")
        self.setStyleSheet(theme.PAGE_BG_QSS)
        # Plain QWidget subclasses don't paint QSS backgrounds by default —
        # QFrame does, but QWidget needs this attribute switched on explicitly.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setSpacing(28)

        title = QLabel("Digital-Sync | Machine Monitoring")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Black))
        title.setStyleSheet(f"background: transparent; color: {theme.COLORS['white']};")

        subtitle = QLabel("INITIALIZING SYSTEM")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        subtitle.setStyleSheet(f"background: transparent; color: {theme.COLORS['slate_600']}; letter-spacing: 4px;")

        # Ring + centered number, stacked using a plain QWidget with two children
        ring_wrap = QWidget()
        ring_wrap.setFixedSize(220, 220)
        self.ring = CountdownRing(220)
        self.ring.setParent(ring_wrap)
        self.ring.move(0, 0)

        self.number_label = QLabel(str(LOADING_DURATION), ring_wrap)
        self.number_label.setFont(QFont("Segoe UI", 48, QFont.Weight.Black))
        self.number_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['white']};")
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number_label.setGeometry(0, 70, 220, 60)

        seconds_label = QLabel("SECONDS", ring_wrap)
        seconds_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['slate_600']}; letter-spacing: 2px;")
        seconds_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        seconds_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seconds_label.setGeometry(0, 130, 220, 20)

        self.msg_label = QLabel(LOAD_MESSAGES[0])
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_label.setStyleSheet(f"background: transparent; color: {theme.COLORS['slate_400_txt']}; font-weight: 600;")

        outer.addWidget(title)
        outer.addWidget(subtitle)
        outer.addWidget(ring_wrap, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.msg_label)

    def start(self):
        self._remaining = LOADING_DURATION
        self._timer.start(1000)  # 1000ms = 1s, like setInterval(fn, 1000)

    def _tick(self):
        self._remaining -= 1
        self.number_label.setText(str(max(0, self._remaining)))

        elapsed_fraction = (LOADING_DURATION - self._remaining) / LOADING_DURATION
        self.ring.set_fraction(elapsed_fraction)

        msg_idx = min(
            int(elapsed_fraction * len(LOAD_MESSAGES)),
            len(LOAD_MESSAGES) - 1,
        )
        self.msg_label.setText(LOAD_MESSAGES[msg_idx])

        if self._remaining <= 0:
            self._timer.stop()
            self.finished.emit()