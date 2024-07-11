import signal
import logging

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QTcpServer, QHostAddress

from .kiwoom_ocx import KiwoomOCX
from .client_handler import ClientHandler
from .server_handler import ServerHandler

class Proxy():

    def __init__(self):
        self._address = '127.0.0.1'
        self._port_number = 53939
        self._server = QTcpServer()
        self._socket = None
        self._client_handler = None
        self._server_handler = None       

    def set_port(self, port_number: int):
        self._port_number = port_number
    
    def set_address(self, address: str):
        self._address = address

    def initialize(self):
        app = QApplication([])

        # Ctrl + C로 프로그램을 강제 종료하기 위해 100ms마다 종료 신호를 감지합니다.
        quit = lambda signum, frame: QApplication.quit()
        signal.signal(signal.SIGINT, quit)
        timer = QTimer()
        timer.start(100)
        timer.timeout.connect(lambda: None)

        # level 매개변수에 따라 로그의 정도를 조절할 수 있습니다.
        logging.basicConfig(filename='log.txt', level=logging.INFO) 

        self._server.listen(QHostAddress(self._address), self._port_number)
        self._server.newConnection.connect(self._start_market)
        self._ocx = KiwoomOCX()
        app.exec_()
    
    def _start_market(self):
        self._socket = self._server.nextPendingConnection()
        self._client_handler = ClientHandler(self._ocx, self._socket)
        self._server_handler = ServerHandler(self._ocx, self._socket)