# """
# main.py — the entry point. Run this file to launch the app.

# NEW CONCEPT: QStackedWidget
# --------------------------------
# Like your JS which shows/hides #loadingOverlay with an opacity + display
# toggle, a QStackedWidget holds multiple "pages" and shows exactly one at a
# time. We add the LoadingScreen and MainWindow as two pages and just flip
# between them — cleaner than manually hiding/showing separate top-level
# windows.

# Behavior:
#   - Loading countdown starts immediately (20s), independent of API calls
#   - API polling ALSO starts immediately in the background
#   - If a successful fetch (non-empty machine data) arrives before the
#     countdown finishes, it's cached and rendered only once the 20s
#     window completes — same "cache, don't jump ahead" idea as before.
#   - If the 20s window ends with NO successful fetch yet (offline backend,
#     timeout, empty response, etc.), the countdown restarts from 20s and
#     keeps looping — the poller keeps trying in the background the whole
#     time. The main dashboard is NEVER shown without real fetched data.
# """
# import sys
# from PyQt6.QtWidgets import QApplication, QStackedWidget

# from loading_screen import LoadingScreen
# from main_window import MainWindow
# from api_worker import ApiWorker


# class App(QStackedWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Digital-Sync | Machine Monitoring")
#         self.resize(1600, 900)
#         self.setStyleSheet("background-color: #1e293b;")  # bg-slate-800

#         self._page_ready = False
#         self._pending_machines = None
#         self._got_data = False     # True the moment ANY successful fetch happens
#         self._retry_attempt = 0

#         self.loading_screen = LoadingScreen()
#         self.main_window = MainWindow()

#         self.addWidget(self.loading_screen)
#         self.addWidget(self.main_window)
#         self.setCurrentWidget(self.loading_screen)

#         self.loading_screen.finished.connect(self._on_loading_finished)

#         # Background API polling — starts immediately and keeps running
#         # for the lifetime of the app, success or failure.
#         self.worker = ApiWorker()
#         self.worker.machines_received.connect(self._on_machines)
#         self.worker.ip_received.connect(self.main_window.set_ip)
#         self.worker.online_status.connect(self._on_online_status)
#         self.worker.online_status.connect(self.main_window.set_online)
#         self.worker.start()

#         self.loading_screen.start()

#     def _on_online_status(self, online: bool):
#         # api_worker only emits online=True alongside real, non-empty data,
#         # so this is our single source of truth for "a fetch actually worked".
#         if online:
#             self._got_data = True

#     def _on_machines(self, machines: list):
#         self._pending_machines = machines
#         if self._page_ready:
#             self.main_window.render_machines(machines)

#     def _on_loading_finished(self):
#         if self._got_data and self._pending_machines:
#             # Success within this window -> show the dashboard now.
#             self._page_ready = True
#             self.setCurrentWidget(self.main_window)
#             self.main_window.render_machines(self._pending_machines)
#         else:
#             # No successful fetch yet -> loop the countdown and keep trying.
#             # The worker thread is untouched and keeps polling in the background.
#             self._retry_attempt += 1
#             self.loading_screen.start(retry_attempt=self._retry_attempt)

#     def closeEvent(self, event):
#         self.worker.stop()
#         super().closeEvent(event)


# def main():
#     app = QApplication(sys.argv)
#     window = App()
#     window.show()
#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()


"""
main.py — the entry point. Run this file to launch the app.

NEW CONCEPT: QStackedWidget
--------------------------------
Like your JS which shows/hides #loadingOverlay with an opacity + display
toggle, a QStackedWidget holds multiple "pages" and shows exactly one at a
time. We add the LoadingScreen and MainWindow as two pages and just flip
between them — cleaner than manually hiding/showing separate top-level
windows.

Behavior:
  - Loading countdown starts immediately (20s), independent of API calls
  - API polling ALSO starts immediately in the background
  - If a successful fetch (non-empty machine data) arrives before the
    countdown finishes, it's cached and rendered only once the 20s
    window completes — same "cache, don't jump ahead" idea as before.
  - If the 20s window ends with NO successful fetch yet (offline backend,
    timeout, empty response, etc.), the countdown restarts from 20s and
    keeps looping — the poller keeps trying in the background the whole
    time. The main dashboard is NEVER shown without real fetched data.
"""
import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget

from loading_screen import LoadingScreen
from main_window import MainWindow
from api_worker import ApiWorker, QRSendWorker
from qr_scanner import QRScanner
from toast import ToastContainer


class App(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital-Sync | Machine Monitoring")
        self.resize(1600, 900)
        self.setStyleSheet("background-color: #1e293b;")  # bg-slate-800

        self._page_ready = False
        self._pending_machines = None
        self._got_data = False     # True the moment ANY successful fetch happens
        self._retry_attempt = 0

        self.loading_screen = LoadingScreen()
        self.main_window = MainWindow()

        self.addWidget(self.loading_screen)
        self.addWidget(self.main_window)
        self.setCurrentWidget(self.loading_screen)

        self.loading_screen.finished.connect(self._on_loading_finished)

        # Background API polling — starts immediately and keeps running
        # for the lifetime of the app, success or failure.
        self.worker = ApiWorker()
        self.worker.machines_received.connect(self._on_machines)
        self.worker.ip_received.connect(self.main_window.set_ip)
        self.worker.online_status.connect(self._on_online_status)
        self.worker.online_status.connect(self.main_window.set_online)
        self.worker.start()

        # QR scanner: an app-wide event filter catches keystrokes no matter
        # what has focus, same as your always-focused hidden <input>.
        self._qr_send_workers = []  # keep references alive until each POST finishes
        self.qr_scanner = QRScanner(self)
        QApplication.instance().installEventFilter(self.qr_scanner)
        self.qr_scanner.scanned.connect(self._on_qr_scanned)

        # Toast overlay: floats above whichever page (loading/dashboard) is
        # currently shown, pinned to the bottom-right corner.
        self.toast_container = ToastContainer(self)

        self.loading_screen.start()

    def _on_online_status(self, online: bool):
        # api_worker only emits online=True alongside real, non-empty data,
        # so this is our single source of truth for "a fetch actually worked".
        if online:
            self._got_data = True

    def _on_machines(self, machines: list):
        self._pending_machines = machines
        if self._page_ready:
            self.main_window.render_machines(machines)

    def _on_loading_finished(self):
        if self._got_data and self._pending_machines:
            # Success within this window -> show the dashboard now.
            self._page_ready = True
            self.setCurrentWidget(self.main_window)
            self.main_window.render_machines(self._pending_machines)
        else:
            # No successful fetch yet -> loop the countdown and keep trying.
            # The worker thread is untouched and keeps polling in the background.
            self._retry_attempt += 1
            self.loading_screen.start(retry_attempt=self._retry_attempt)

    def _on_qr_scanned(self, code: str):
        """Equivalent of your inp.addEventListener('input', ...) debounce
        callback: show the toast immediately, send the POST in the background."""
        self.toast_container.show_toast(f"QR Scanned: {code}")

        worker = QRSendWorker(code, self)
        worker.finished_ok.connect(self._on_qr_sent)
        self._qr_send_workers.append(worker)
        worker.start()

    def _on_qr_sent(self, ok: bool, code: str):
        sender = self.sender()
        if sender in self._qr_send_workers:
            self._qr_send_workers.remove(sender)
        sender.deleteLater()
        if not ok:
            print(f"[QR] Failed to send breakdown reason for code: {code}")
        # Matches your JS `if (r.ok) fetchStatus();` — the next scheduled
        # poll (within 2s) will naturally pick up the change; if you want
        # it truly instant, ApiWorker could expose a poll_now() trigger.

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast_container.reposition()

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