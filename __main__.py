import signal
import logging

from PyQt5.QtWidgets import QApplication
from .market import MarketManager
from .manager import Manager

logging.basicConfig(level=logging.INFO)

# Ctrl + C로 프로그램을 강제 종료하기 위해 신호 기본값으로 다시 바꿔줍니다. - 개선 필요
signal.signal(signal.SIGINT, signal.SIG_DFL)

app = QApplication([])
market_manager = MarketManager()
market_manager.create_market()
manager = Manager()
manager.start()
app.exec_()
