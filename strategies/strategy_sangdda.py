import time
import math
from typing import *
from PyQt5.QtCore import QThread

from ..market import MarketManager
from .strategy import Strategy
from .strategy_sangdda_const import *

class TraderThread(QThread):
    """
    어느 한 종목에 대해 가격 및 호가를 감시하면서 매수 및 매도를 진행하는 쓰레드
    """
    def __init__(self, target_stock_code: str):
        super().__init__()
        self.target_stock_code = target_stock_code

    def run(self):
        print('시작!')
        market = MarketManager().get_market()
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
                print(f'{self.target_stock_code} 매수합니다. - {ask_sum} > {BID_MULTIPLIER} * {bid_sum}')
                price_info = market.get_price_info(self.target_stock_code)
                amount = math.floor(INVESTMENT_PER_STOCK / price_info['현재가'])
                if amount == 0:
                    print('!!! 수량이 0입니다. !!!')
                order_dict = {
                    '구분': '매수',
                    '주식코드': self.target_stock_code,
                    '수량': amount,
                    '가격': 0,
                    '시장가': True
                }
                request_name = market.request_order(order_dict)
                print(f'{self.target_stock_code} 매수요청을 보냈습니다. - {ask_sum} > {BID_MULTIPLIER} * {bid_sum}')
                _ = market.get_order_info(request_name)
                print(f'{self.target_stock_code} 전부 체결되었습니다. - {ask_sum} > {BID_MULTIPLIER} * {bid_sum}')
                break
    
        # 매도 신호 포착
        while True:
            time.sleep(0.5)
            # 현 종목의 수익률을 가져옵니다.
            cur_balance = market.get_balance()
            cur_profit_percentage = cur_balance[self.target_stock_code]['수익률']
            print(f'{self.target_stock_code} 수익률 - {cur_profit_percentage}%')

            # 만약 매수한 종목의 수익률이 N% 이상이면 익절하고 N% 이하면 손절합니다.
            order_dict = {
                '구분': '매도',
                '주식코드': self.target_stock_code,
                '수량': amount,
                '가격': 0,
                '시장가': True
            }
            if cur_profit_percentage > TAKE_PROFIT_PERCENTAGE:
                print(f'{self.target_stock_code} 익절합니다.')
                request_name = market.request_order(order_dict)
                _ = market.get_order_info(request_name)
                break
            elif cur_profit_percentage < STOP_LOSS_PERCENTAGE:
                print(f'{self.target_stock_code} 손절합니다.')
                request_name = market.request_order(order_dict)
                _ = market.get_order_info(request_name)
                break
            else:
                pass


class StrategySangDDa(Strategy):
    """
    상한가 따라잡기 전략
    """
    
    def initialize_stock_universe(self) -> None:
        """
        Stock universe와 관련된 초기화 작업을 진행합니다.
        """
        # stock universe를 설정합니다.
        market = MarketManager().get_market()
        condition = market.get_condition()
        matching_stocks = market.get_matching_stocks(condition[0]['name'], condition[0]['index'])
        self.stock_universe = matching_stocks
        

    def start_strategy(self) -> None:
        """
        전략을 시작합니다.
        """
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

        self.finished.emit()
        