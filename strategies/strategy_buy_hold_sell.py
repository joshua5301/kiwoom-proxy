import time
from PyQt5.QtCore import QThread

from ..market import MarketManager
from .strategy import Strategy
from .strategy_buy_hold_sell_const import STOCK_NUM, WAIT_SECOND, HOLD_SECOND

class TraderThread(QThread):
    """
    어느 한 종목에 대해 가격 및 호가를 감시하면서 매수 및 매도를 진행하는 쓰레드
    """
    def __init__(self, target_stock_code: str):
        super().__init__()
        self.target_stock_code = target_stock_code

    def run(self):
        market = MarketManager.get_market()
        time.sleep(WAIT_SECOND)
        order_dict = {
            '구분': '매수',
            '주식코드': self.target_stock_code,
            '가격': 0,
            '수량': STOCK_NUM,
            '시장가': True
        }
        order_name = market.request_order(order_dict)
        _ = market.get_order_info(order_name)
        
        time.sleep(HOLD_SECOND)
        order_dict = {
            '구분': '매도',
            '주식코드': self.target_stock_code,
            '가격': 0,
            '수량': STOCK_NUM,
            '시장가': True
        }
        order_name = market.request_order(order_dict)
        _ = market.get_order_info(order_name)


class StrategyBuyHoldSell(Strategy):
    """
    매수 후 매매 전략
    """
    
    def run(self):

        # universe의 각 종목에 대하여 일대일로 매수와 매도 판단을 내리는 TraderThread를 만듭니다.
        thread_list = []
        for stock_code in self.stock_universe:
            thread = TraderThread(stock_code)
            thread.start()
            thread_list.append(thread)
            time.sleep(0.2)

        # 모든 TraderThread가 끝날 때까지 기다립니다.
        for thread in thread_list:
            thread.wait()
        