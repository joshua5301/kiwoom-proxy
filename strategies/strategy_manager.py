from typing import *
from PyQt5.QtCore import QThread

from .strategy import Strategy
from .strategy_buy_hold_sell import StrategyBuyHoldSell
from .strategy_sangdda import StrategySangDDa

class StrategyManager():
    
    def __init__(self, strategy_name: str):

        # strategy_name에 따라 strategy를 생성합니다.
        if strategy_name == 'SangDDa':
            self.strategy = StrategySangDDa()
        elif strategy_name == 'BuyHoldSell':
            self.strategy = StrategyBuyHoldSell()
        else:
            raise ValueError('유효하지 않은 전략 이름입니다.')
        
        # stock universe를 생성하고 등록합니다.
        self.strategy.initialize_stock_universe()

        # strategy를 실행할 thread를 만들고 strategy를 그 thread에 속하도록 옮깁니다.
        self._thread = QThread()
        self.strategy.moveToThread(self._thread)

        # thread가 시작되었을 때 strategy가 시작하도록 세팅합니다.
        self._thread.started.connect(self.strategy.start_strategy)

        # strategy가 종료되었을 때 thread가 종료하고 메모리를 정리하도록 세팅합니다.
        self.strategy.finished.connect(self._thread.quit)
        self.strategy.finished.connect(self.strategy.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)


    def start_strategy(self) -> None:
        """
        strategy를 시작합니다.
        """
        self._thread.start()
    
    def wait_strategy(self) -> None:
        """
        strategy가 끝날 때까지 기다립니다.
        """
        self._thread.wait()
    
    def get_stock_universe(self) -> List[str]:
        """
        strategy가 거래 대상으로 고려할 모든 주식 리스트를 반환합니다.

        Returns
        -------
        List[str]
            stock universe를 반환합니다.
        """
        return self.strategy.stock_universe
