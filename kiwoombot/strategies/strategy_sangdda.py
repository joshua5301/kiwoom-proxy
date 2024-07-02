import time
import datetime
import math
import logging
from typing import *
from PyQt5.QtCore import QThread, QMutex, QMutexLocker

from ..market import MarketManager
from .strategy import Strategy
from .strategy_sangdda_const import *

logger = logging.getLogger(__name__)

class _TraderThread(QThread):
    """
    어느 한 종목에 대해 가격 및 호가를 감시하면서 매수 및 매도를 진행하는 쓰레드
    """
    def __init__(self, target_stock_code: str):
        super().__init__()
        self.target_stock_code = target_stock_code

    def run(self):
        market = MarketManager().get_market()
        start_time = datetime.datetime.now()

        # 매수 신호 포착
        while True:
            time.sleep(0.5)

            # 종목의 호가정보를 가져오고 매도세와 매수세를 계산합니다.
            ask_bid_info = market.get_ask_bid_info(self.target_stock_code)
            bid_sum = 0
            ask_sum = 0
            for price, amount in ask_bid_info['매도호가정보']:
                ask_sum += price * amount
            for price, amount in ask_bid_info['매수호가정보']:
                bid_sum += price * amount

            # 매도세가 매수세보다 N배보다 많다면 약 N만원 어치를 매수합니다.
            if ask_sum > BID_MULTIPLIER * bid_sum:
                price_info = market.get_price_info(self.target_stock_code)
                amount = math.floor(INVESTMENT_PER_STOCK / price_info['현재가'])
                if amount == 0:
                    logger.warning('!!! 수량이 0입니다. !!!')
                    return
                order_dict = {
                    '구분': '매수',
                    '주식코드': self.target_stock_code,
                    '수량': amount,
                    '가격': 0,
                    '시장가': True
                }
                request_name = market.request_order(order_dict)
                _ = market.get_order_info(request_name)
                break

            # 최대 거래 시간이 지났다면 거래를 종료합니다. 
            cur_time = datetime.datetime.now()
            if (cur_time - start_time).total_seconds() > MAX_TRANSACTION_TIME * 60:
                return
    
        # 매도 신호 포착
        while True:
            time.sleep(0.5)
            # 현 종목의 수익률을 계산합니다.
            cur_price = market.get_price_info(self.target_stock_code)['현재가']
            cur_balance = market.get_balance()[self.target_stock_code]['매입단가']
            cur_profit_percentage = (cur_balance / cur_price - 1) * 100

            # 만약 매수한 종목의 수익률이 N% 이상이면 익절하고 N% 이하면 손절합니다.
            # 또한 최대 거래 시간이 지나도 청산합니다.
            order_dict = {
                '구분': '매도',
                '주식코드': self.target_stock_code,
                '수량': amount,
                '가격': 0,
                '시장가': True
            }
            cur_time = datetime.datetime.now()
            if cur_profit_percentage > TAKE_PROFIT_PERCENTAGE or cur_profit_percentage < STOP_LOSS_PERCENTAGE or \
               (cur_time - start_time).total_seconds() > MAX_TRANSACTION_TIME * 60:
                request_name = market.request_order(order_dict)
                _ = market.get_order_info(request_name)
                break
            else:
                pass


class StrategySangDDa(Strategy):
    """
    상한가 따라잡기 전략
    """
    
    _lock = QMutex()
    _stock_universe = None
    def get_stock_universe(self) -> None:
        """
        전날 상한가에 도달한 주식들을 stock universe로 반환합니다.
        """
        print('???')
        with QMutexLocker(StrategySangDDa._lock):
            if StrategySangDDa._stock_universe is None:
                print('why')
                market = MarketManager().get_market()
                condition = market.get_condition()
                matching_stocks = market.get_matching_stocks(condition[0]['name'], condition[0]['index'])
                StrategySangDDa._stock_universe = matching_stocks
                print('why12')
        print('asdf')
        return StrategySangDDa._stock_universe
        

    def run(self) -> None:
        """
        상한가 따라잡기 전략을 수행합니다.
        """
        # universe의 각 종목에 대하여 일대일로 매수와 매도 판단을 내리는 TraderThread를 만듭니다.
        thread_list = []
        stock_universe = self.get_stock_universe()
        for stock_code in stock_universe:
            thread = _TraderThread(stock_code)
            thread.start()
            thread_list.append(thread)
            time.sleep(0.2)

        # 모든 TraderThread가 끝날 때까지 기다립니다.
        for thread in thread_list:
            thread.wait()
        