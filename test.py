import signal
import platform

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread
from PyQt5.QAxContainer import QAxWidget

class Market(QAxWidget):
    def __init__(self):
        super().__init__()
        print(platform.architecture())
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1')
        print('wow')

class MyThread(QThread):
    def run(self):
        pass


signal.signal(signal.SIGINT, signal.SIG_DFL)

app = QApplication([])
my_widget = Market()
thread = MyThread()
thread.start()
thread.wait()
app.exec_()