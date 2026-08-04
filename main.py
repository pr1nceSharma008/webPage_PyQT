"""
main.py — the entry point. Run this file to launch the app.

NEW CONCEPT: QStackedWidget
--------------------------------
Like your JS which shows/hides #loadingOverlay with an opacity + display
toggle, a QStackedWidget holds multiple "pages" and shows exactly one at a
time. We add the LoadingScreen and MainWindow as two pages and just flip
between them — cleaner than manually hiding/showing separate top-level
windows.

Behavior matched from your JS:
  - Loading countdown starts immediately (30s), independent of API calls
  - API polling ALSO starts immediately in the background
  - If data arrives before the countdown finishes, it's cached
    (self._pending_machines) and rendered only once loading finishes
    -- this mirrors your `pendingMachines` variable exactly.
"""
import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget

from loading_screen import LoadingScreen
from main_window import MainWindow
from api_worker import ApiWorker


class App(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital-Sync | Machine Monitoring")
        self.resize(1600, 900)
        self.setStyleSheet("background-color: #1e293b;")  # bg-slate-800

        self._page_ready = False
        self._pending_machines = None

        self.loading_screen = LoadingScreen()
        self.main_window = MainWindow()

        self.addWidget(self.loading_screen)
        self.addWidget(self.main_window)
        self.setCurrentWidget(self.loading_screen)

        self.loading_screen.finished.connect(self._on_loading_finished)

        # Background API polling — starts immediately, same as your JS
        self.worker = ApiWorker()
        self.worker.machines_received.connect(self._on_machines)
        self.worker.ip_received.connect(self.main_window.set_ip)
        self.worker.online_status.connect(self.main_window.set_online)
        self.worker.start()

        self.loading_screen.start()

    def _on_machines(self, machines: list):
        if self._page_ready:
            self.main_window.render_machines(machines)
        else:
            self._pending_machines = machines  # cache, like JS pendingMachines

    def _on_loading_finished(self):
        self._page_ready = True
        self.setCurrentWidget(self.main_window)
        if self._pending_machines is not None:
            self.main_window.render_machines(self._pending_machines)
            self._pending_machines = None

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()