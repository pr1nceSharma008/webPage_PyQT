# """
# api_worker.py — polls your .NET backend on a background thread.

# NEW CONCEPT: QThread + custom pyqtSignal
# ------------------------------------------
# A QThread runs a `run()` method on its own thread, separate from the UI thread.
# It can never touch widgets directly (that would crash the app). Instead, it
# `.emit()`s signals, and the main window `.connect()`s to them — same
# signal/slot pattern as `button.clicked.connect(...)`, but the signal is one
# YOU define with pyqtSignal(), carrying whatever data type you want (here: a
# Python list/dict, exactly like JSON.parse() gives you in JS).
# """
# import time
# import requests
# from PyQt6.QtCore import QThread, pyqtSignal

# BASE = "http://localhost:5147"
# API_STATUS = f"{BASE}/api/Backend/GetMachineStatus"
# API_IP = f"{BASE}/api/Backend/GetIPAddress"

# POLL_SECONDS = 2          # same as JS POLL_MS = 2000
# IP_POLL_EVERY_N_TICKS = 15  # 15 * 2s = 30s, same as JS IP_POLL_MS = 30000


# class ApiWorker(QThread):
#     # Signals are declared at class level. Think of them as event types
#     # you're inventing — similar to defining a custom DOM CustomEvent.
#     machines_received = pyqtSignal(list)   # emits parsed machine list
#     ip_received = pyqtSignal(str)          # emits IP string
#     connection_lost = pyqtSignal(str)      # emits an error message
#     online_status = pyqtSignal(bool)       # emits True/False (live indicator)

#     def __init__(self):
#         super().__init__()
#         self._running = True

#     def run(self):
#         """This method executes on the background thread when .start() is called."""
#         tick = 0
#         while self._running:
#             self._poll_status()
#             if tick % IP_POLL_EVERY_N_TICKS == 0:
#                 self._poll_ip()
#             tick += 1
#             time.sleep(POLL_SECONDS)

#     def _poll_status(self):
#         try:
#             r = requests.get(API_STATUS, timeout=5)
#             r.raise_for_status()
#             data = r.json()
#             if data:
#                 self.online_status.emit(True)
#                 self.machines_received.emit(data)
#             else:
#                 self.online_status.emit(False)
#                 self.machines_received.emit([])
#         except Exception as e:
#             self.online_status.emit(False)
#             self.connection_lost.emit(str(e))

#     def _poll_ip(self):
#         try:
#             r = requests.get(API_IP, timeout=5)
#             r.raise_for_status()
#             ip = r.json().get("ipAddress", "N/A")
#             self.ip_received.emit(ip)
#         except Exception:
#             self.ip_received.emit("N/A")

#     def stop(self):
#         """Call this on app close so the thread doesn't loop forever."""
#         self._running = False
#         self.wait(3000)



"""
api_worker.py — polls your .NET backend on a background thread.

NEW CONCEPT: QThread + custom pyqtSignal
------------------------------------------
A QThread runs a `run()` method on its own thread, separate from the UI thread.
It can never touch widgets directly (that would crash the app). Instead, it
`.emit()`s signals, and the main window `.connect()`s to them — same
signal/slot pattern as `button.clicked.connect(...)`, but the signal is one
YOU define with pyqtSignal(), carrying whatever data type you want (here: a
Python list/dict, exactly like JSON.parse() gives you in JS).
"""
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal

BASE = "http://localhost:5147"
API_STATUS = f"{BASE}/api/Backend/GetMachineStatus"
API_IP = f"{BASE}/api/Backend/GetIPAddress"
API_BREAKDOWN = f"{BASE}/api/Backend/UpdateBreakdownReason"

POLL_SECONDS = 2          # same as JS POLL_MS = 2000
IP_POLL_EVERY_N_TICKS = 15  # 15 * 2s = 30s, same as JS IP_POLL_MS = 30000


class ApiWorker(QThread):
    # Signals are declared at class level. Think of them as event types
    # you're inventing — similar to defining a custom DOM CustomEvent.
    machines_received = pyqtSignal(list)   # emits parsed machine list
    ip_received = pyqtSignal(str)          # emits IP string
    connection_lost = pyqtSignal(str)      # emits an error message
    online_status = pyqtSignal(bool)       # emits True/False (live indicator)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        """This method executes on the background thread when .start() is called."""
        tick = 0
        while self._running:
            self._poll_status()
            if tick % IP_POLL_EVERY_N_TICKS == 0:
                self._poll_ip()
            tick += 1
            time.sleep(POLL_SECONDS)

    def _poll_status(self):
        try:
            r = requests.get(API_STATUS, timeout=5)
            r.raise_for_status()
            data = r.json()
            if data:
                self.online_status.emit(True)
                self.machines_received.emit(data)
            else:
                self.online_status.emit(False)
                self.machines_received.emit([])
        except Exception as e:
            self.online_status.emit(False)
            self.connection_lost.emit(str(e))

    def _poll_ip(self):
        try:
            r = requests.get(API_IP, timeout=5)
            r.raise_for_status()
            ip = r.json().get("ipAddress", "N/A")
            self.ip_received.emit(ip)
        except Exception:
            self.ip_received.emit("N/A")

    def stop(self):
        """Call this on app close so the thread doesn't loop forever."""
        self._running = False
        self.wait(3000)


class QRSendWorker(QThread):
    """
    One-shot background thread for a single QR POST — equivalent of your
    async sendQR(code). A fresh instance is created per scan; QThread
    isn't reusable once it finishes, same as a fresh fetch() promise
    each time in JS.
    """
    finished_ok = pyqtSignal(bool, str)  # (success, code)

    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self.code = code

    def run(self):
        try:
            r = requests.post(
                f"{API_BREAKDOWN}/{self.code}",
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            self.finished_ok.emit(r.ok, self.code)
        except Exception as e:
            print("QR send error:", e)
            self.finished_ok.emit(False, self.code)