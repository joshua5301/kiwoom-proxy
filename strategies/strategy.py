from typing import *
from PyQt5.QtCore import QObject, pyqtSignal

class Strategy(QObject):
    """
    모든 strategy의 base class
    """
    
    # run 메서드의 맨 마지막에 이 신호를 emit 해야합니다.
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.stock_universe = None

    def initialzie_stock_universe(self) -> None:
        """
        Stock universe와 관련된 초기화 작업을 진행합니다.
        """
        raise NotImplementedError('파생 클래스는 이 메서드를 구현해야 합니다!')

    def start_strategy(self) -> None:
        """
        실제 strategy의 구현 부분입니다.
        """
        raise NotImplementedError('파생 클래스는 이 메서드를 구현해야 합니다!')