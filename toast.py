"""
toast.py — bottom-right toast notifications, ported from your JS toast().

NEW CONCEPT: floating/overlay widgets with manual positioning
-------------------------------------------------------------------
CSS's `position: fixed; bottom: 1rem; right: 1rem;` has no QSS
equivalent — QSS only styles colors/borders/etc, it has no layout
positioning properties at all (see the lesson from Part 1: layout is
never QSS's job). An "overlay" in PyQt is just a normal child widget
whose (x, y) you set by hand with .move(), recalculated whenever the
parent resizes — that's what reposition() below does.
"""
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer

import theme

TOAST_DURATION_MS = 3000  # matches your JS setTimeout(() => el.remove(), 3000)


class Toast(QFrame):
    """One notification bubble — equivalent of your .toast div."""

    def __init__(self, message: str, on_removed, parent=None):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QFrame#toast {{
                background-color: rgba(255,255,255,0.35);
                border-left: 6px solid {theme.COLORS['sky_500']};
                border-radius: 24px;
            }}
        """)
        self.setMinimumWidth(250)
        self.setMaximumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        label = QLabel(message)
        label.setStyleSheet(f"background: transparent; color: {theme.COLORS['white']}; font-weight: 600;")
        label.setWordWrap(True)
        layout.addWidget(label)

        self._on_removed = on_removed
        QTimer.singleShot(TOAST_DURATION_MS, self._remove)

    def _remove(self):
        self._on_removed(self)
        self.setParent(None)
        self.deleteLater()


class ToastContainer(QWidget):
    """
    Sits as a transparent overlay child of the top-level window, pinned
    to the bottom-right corner, stacking Toast widgets vertically —
    equivalent of your #toastContainer div.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self.hide()

    def show_toast(self, message: str):
        toast = Toast(message, self._on_toast_removed, self)
        self._layout.addWidget(toast)
        self.show()
        self.raise_()
        self.reposition()

    def _on_toast_removed(self, toast_widget):
        # Reposition shortly after removal so the container shrinks
        # back down and stays anchored to the bottom-right corner.
        QTimer.singleShot(0, self.reposition)

    def reposition(self):
        parent = self.parentWidget()
        if not parent:
            return
        self.adjustSize()
        margin = 20
        x = parent.width() - self.width() - margin
        y = parent.height() - self.height() - margin
        self.move(max(0, x), max(0, y))
        self.raise_()
        if self._layout.count() == 0:
            self.hide()