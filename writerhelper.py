import time
import sys

import os
import subprocess


# ========================================================================================
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, QObject, Signal, Slot

from time import strftime, localtime
import backend as bak


# ========================================================================================
# Define our backend object, which we pass to QML.
backend = None


# ========================================================================================
def run_ui():
    #sys.argv += ['--style', 'Fusion']
    app = QApplication(sys.argv)
    backend = bak.Backend()

    engine = QQmlApplicationEngine("ui/qml/main.qml")
    engine.quit.connect(backend.quit)

    engine.rootObjects()[0].setProperty('backend', backend)
    app.exec()




# ========================================================================================
def main():
    try:
        run_ui()
    except KeyboardInterrupt as e:
        print("[INFO] Received keyboard interrupt %s" % str(e))
        QApplication.instance().quit()
    except Exception as e:
        print("[ERROR] Exception received %s" % str(e))
        QApplication.instance().quit()
        raise


# ========================================================================================
if __name__ == '__main__':
    main()
