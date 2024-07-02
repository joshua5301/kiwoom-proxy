from typing import *
from PyQt5.QtCore import QThread

class Strategy(QThread):
    """
    모든 strategy의 base class
    """

    def get_stock_universe(self) -> List[str]:
        """
        stock universe를 반환하는 함수입니다.
        """
        raise NotImplementedError('파생 클래스는 이 메서드를 구현해야 합니다!')

    def run(self) -> None:
        """
        실제 strategy의 구현 부분입니다.
        """
        raise NotImplementedError('파생 클래스는 이 메서드를 구현해야 합니다!')