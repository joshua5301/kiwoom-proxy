from .strategy import Strategy
from .strategy_buy_hold_sell import StrategyBuyHoldSell
from .strategy_sangdda import StrategySangDDa
from .strategy_test import StrategyTest

class StrategyFactory():
    
    @staticmethod
    def get_strategy(name: str, stock_universe: list[str]) -> Strategy:
        if name == 'BuyHoldSell':
            return StrategyBuyHoldSell(stock_universe)
        elif name == 'SangDDa':
            return StrategySangDDa(stock_universe)
        elif name == 'Test':
            return StrategyTest(stock_universe)