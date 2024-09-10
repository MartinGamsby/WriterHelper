import time
import sys

import os
import subprocess


from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, QObject, Signal, Slot

from time import strftime, localtime
from threading import Thread


data = ""


# --------------- Backend of the UI --------------
class Backend(QObject):
    updated = Signal(str, arguments=['time'])

    def __init__(self):
        super().__init__()

        # Define timer.
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_string)
        self.timer.start()

    @Slot(str, result=bool)
    def run(self, arg):
        args = arg.split()

        args = [os.path.expandvars(i) for i in args]
        print(args)
        subprocess.run(args)
        return True

    @Slot()
    def quit(self):
        print("quitting")

    @Slot(str, result=bool)
    def set_title(self, text):
        #print("set_title", text)
        
        global data
        data = text
        self.update_string()
        
    @Slot(int, result=bool)
    def set_int_select(self, idx):
        print("set_int_select", idx)

    @Slot(bool, result=bool)
    def set_bool(self, enabled):
        print("set_bool", enabled)

    def get_time(self):
        return strftime("%H:%M:%S", localtime())

    def update_string(self):
        # Pass the last string to QML
        global data
        self.updated.emit(data)


# Define our backend object, which we pass to QML.
backend = None

def run_ui():
    sys.argv += ['--style', 'Fusion']
    app = QApplication(sys.argv)
    backend = Backend()

    engine = QQmlApplicationEngine("ui/qml/main.qml")
    engine.quit.connect(backend.quit)

    engine.rootObjects()[0].setProperty('backend', backend)
    # Initial call to trigger first update. Must be after the setProperty to connect signals.
    backend.update_string()

    #thread = Thread(target=run_demo)
    #thread.start()

    app.exec()




def main():
    p = None
    try:
        run_ui()
    except KeyboardInterrupt as e:
        print("[INFO] Received keyboard interrupt %s" % str(e))
        QApplication.instance().quit()
    except Exception as e:
        print("[ERROR] Exception received %s" % str(e))
        QApplication.instance().quit()
        raise
    finally:
        if p:
            p.terminate()


if __name__ == '__main__':
    main()
