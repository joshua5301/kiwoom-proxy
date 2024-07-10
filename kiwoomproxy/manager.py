import signal
import logging

from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QTcpServer, QHostAddress

from .kiwoom_ocx import KiwoomOCX
from .client_handler import ClientHandler
from .server_handler import ServerHandler

class Manager():

    def __init__(self):
        self.address = '127.0.0.1'
        self.port_number = 53939
        self.server = QTcpServer()
        self.socket = None
        self.client_handler = None
        self.server_handler = None
        
        # level 매개변수에 따라 로그의 정도를 조절할 수 있습니다.
        logging.basicConfig(filename='log.txt', level=logging.INFO)
        # Ctrl + C로 프로그램을 강제 종료하기 위해 신호 기본값으로 다시 바꿔줍니다.
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def set_port(self, port_number: int):
        self.port_number = port_number
    
    def set_address(self, address: str):
        self.address = address

    def connect(self):
        app = QApplication([])
        self.server.listen(QHostAddress(self.address), self.port_number)
        self.server.newConnection.connect(self._start_market)
        self.ocx = KiwoomOCX()
        app.exec_()
    
    def _start_market(self):
        self.socket = self.server.nextPendingConnection()
        self.client_handler = ClientHandler(self.ocx, self.socket)
        self.server_handler = ServerHandler(self.ocx, self.socket)