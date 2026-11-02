import os
import time
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE = os.path.dirname(os.path.abspath(__file__))

ALERT_FILE = os.path.join(BASE, "alerts.json")

MODULE1 = os.path.join(BASE, "module1.ps1")


# ==========================================
# ALERT HANDLER
# ==========================================

class AlertHandler(FileSystemEventHandler):

    def on_modified(self, event):

        if event.src_path.endswith("alerts.json"):

            print("\n New alerts detected")

            subprocess.run([
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                MODULE1
            ])


# ==========================================
# START MONITORING
# ==========================================

print(" Monitoring alerts.json for changes...")

event_handler = AlertHandler()

observer = Observer()

observer.schedule(
    event_handler,
    path=BASE,
    recursive=False
)

observer.start()


try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    observer.stop()

observer.join()