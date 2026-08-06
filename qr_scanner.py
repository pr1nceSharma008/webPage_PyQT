from PyQt6.QtCore import QObject, QEvent, QTimer, pyqtSignal
import time

DEBOUNCE_MS = 200          # Wait after last key before considering scan complete
DUPLICATE_DELAY_MS = 10    # Ignore identical key within 10ms


class QRScanner(QObject):
    scanned = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._buffer = ""

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(DEBOUNCE_MS)
        self._timer.timeout.connect(self._flush)

        # Duplicate key protection
        self._last_key = None
        self._last_time = 0

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.KeyPress:
            return False

        # Ignore auto-repeat keys
        if event.isAutoRepeat():
            return False

        text = event.text()

        if not text or not text.isprintable():
            return False

        now = time.monotonic() * 1000  # milliseconds

        # Ignore duplicate key generated immediately
        if (
            text == self._last_key
            and (now - self._last_time) < DUPLICATE_DELAY_MS
        ):
            return False

        self._last_key = text
        self._last_time = now

        self._buffer += text

        # Restart debounce timer
        self._timer.start()

        return False

    def _flush(self):
        code = self._buffer.strip()

        # Reset state
        self._buffer = ""
        self._last_key = None
        self._last_time = 0

        if code:
            print(f"QR Scanned: {code}")  # Debug
            self.scanned.emit(code)