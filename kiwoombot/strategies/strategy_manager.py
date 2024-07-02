from typing import *
from PyQt5.QtCore import QThread

from .strategy import Strategy
from .strategy_buy_hold_sell import StrategyBuyHoldSell
from .strategy_sangdda import StrategySangDDa

class StrategyManager():
    
    def create_strategy(self, strategy_name: str):
        """
        strategy_name에 따라 strategy를 생성합니다.
        """
        if strategy_name == 'SangDDa':
            self.strategy = StrategySangDDa()
        elif strategy_name == 'BuyHoldSell':
            self.strategy = StrategyBuyHoldSell()
        else:
            raise ValueError('유효하지 않은 전략 이름입니다.')

    def start_strategy(self):
        """
        전략을 시작합니다.
        """
        self.strategy.start()
        
    def wait_strategy(self):
        """
        전략이 끝날 때까지 기다립니다.
        """
        self.strategy.wait()
        
    def get_stock_universe(self) -> List[str]:
        """
        전략이 거래대상으로 고려하는 stock universe를 반환합니다.

        Returns
        -------
        List[str]
            stock universe를 반환합니다.
        """
        return self.strategy.get_stock_universe()
        
    
