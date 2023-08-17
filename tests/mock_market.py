from typing import *
from PyQt5.QtCore import QThread
import random
import copy
import time
import datetime
# random.seed(3939)

from .mock_market_const import *

class _RealTimeInfoSimulator(QThread):
    """
    MockMarket의 실시간 정보가 시간에 따라 적절히 변하도록 해주는 클래스입니다.
    """
    def __init__(self, price_info: dict, ask_bid_info: dict):
        """
        MockMarket의 실시간 정보의 참조를 인자로 받고 이를 attribute에 저장합니다.

        Parameters
        ----------
        price_info : dict
            모의 실시간 가격 정보입니다.
        ask_bid_info : dict
            모의 실시간 호가 정보입니다.
        """
        super().__init__()
        self._price_info = price_info
        self._ask_bid_info = ask_bid_info
        
    def run(self):
        while True:
            time.sleep(MARKET_CHANGE_INTERVAL)
            # 가격에 랜덤한 변화를 줍니다.
            # MIN_PRICE원 미만으로 내려가지 않습니다.
            stock_codes = self._price_info.copy().keys()
            for stock_code in stock_codes:
                self._price_info[stock_code]['체결시간'] = datetime.datetime.now().strftime('%H%M%S')
                price_delta = random.randint(int(-MAX_PRICE_CHANGE / PRICE_UNIT), int(MAX_PRICE_CHANGE / PRICE_UNIT)) * PRICE_UNIT
                self._price_info[stock_code]['현재가'] = max(MIN_PRICE, self._price_info[stock_code]['현재가'] + price_delta)
                self._price_info[stock_code]['고가'] = max(self._price_info[stock_code]['고가'], self._price_info[stock_code]['현재가'])
                self._price_info[stock_code]['저가'] = min(self._price_info[stock_code]['저가'], self._price_info[stock_code]['현재가'])
            
            # 호가 수량에 랜덤한 변화를 줍니다.
            # 0개 미만으로 내려가지 않습니다.
            stock_codes = self._ask_bid_info.copy().keys()
            for stock_code in stock_codes:
                prev_ask_bid_info = self._ask_bid_info[stock_code]
                new_ask_bid_info = {
                    '호가시간': datetime.datetime.now().strftime('%H%M%S'),
                    '매수호가정보': [],
                    '매도호가정보': [],
                }
                cur_price = self._price_info[stock_code]['현재가']
                for i in range(10):
                    ask_delta = random.randint(-MAX_ASK_BID_CHANGE, MAX_ASK_BID_CHANGE)
                    new_ask_bid_info['매도호가정보'].append((cur_price + (i + 1) * 10, max(0, prev_ask_bid_info['매도호가정보'][i][1] + ask_delta)))
                    bid_delta = random.randint(-MAX_ASK_BID_CHANGE, MAX_ASK_BID_CHANGE)
                    new_ask_bid_info['매수호가정보'].append((cur_price - i * 10, max(0, prev_ask_bid_info['매수호가정보'][i][1] + bid_delta)))
                self._ask_bid_info[stock_code] = new_ask_bid_info
                    
class MockMarket:
    def __init__(self, client_signal_handler, data):
        self._deposit = START_DEPOSIT
        self._balance = {}
        self._price_info = {}
        self._ask_bid_info = {}
        self._next_order_number = '000000'
        self._real_time_info_simulator = _RealTimeInfoSimulator(self._price_info, self._ask_bid_info)
        self._real_time_info_simulator.start()

    def initialize(self) -> None:
        pass

    def get_condition(self) -> List[Dict[str, Any]]:
        return [{'name': '임의의 조건식0', 'index': 0}, {'name': '임의의 조건식1', 'index': 1}]

    def get_matching_stocks(self, condition_name: str, condition_index: int) -> List[str]:
        if condition_index == 0:
            return ['123690', '159910', '217820', '047310']
        elif condition_index == 1:
            return ['005930', '035720']
        else:
            raise ValueError('mock 객체에서 유효하지 않은 condition_index입니다.')

    def get_deposit(self) -> int:
        return self._deposit

    def get_balance(self) -> Dict[str, Dict[str, Any]]:
        balance = copy.deepcopy(self._balance)
        for stock_code in balance.keys():
            balance[stock_code]['현재가'] = self._price_info[stock_code]['현재가']
            balance[stock_code]['수익률'] = (balance[stock_code]['현재가'] / balance[stock_code]['매입가'] - 1) * 100
        return balance

    def request_order(self, order_dict: Dict[str, Any]) -> str:
        # 지정가 주문은 예외를 발생시킵니다.
        if order_dict['시장가'] is False:
            raise NotImplementedError('mock 객체에서 지정가 주문은 아직 구현되지 않았습니다.')
        
        # 주식 정보가 생성되지 않았을 경우 생성합니다.
        _ = self.get_price_info(order_dict['주식코드'])
        
        # 매수 주문을 처리합니다.
        if order_dict['구분'] == '매수':
            # 보유하지 않은 종목일 때
            if order_dict['주식코드'] not in self._balance:
                self._balance[order_dict['주식코드']] = {
                    '종목명': f'{order_dict["주식코드"]}의 종목명',
                    '수량': order_dict['수량'],
                    '매매가능수량': order_dict['수량'],
                    '매입가': self._price_info[order_dict['주식코드']]['현재가'],
                    '현재가': 'get_balance함수에서 정해짐',
                    '수익률': 'get_balance함수에서 정해짐',
                }
            # 이미 보유한 종목일 때
            else:
                total_value = self._balance[order_dict['주식코드']]['수량'] * self._balance[order_dict['주식코드']]['매입가'] +\
                              order_dict['수량'] * self._price_info[order_dict['주식코드']]['현재가']
                total_amount = self._balance[order_dict['주식코드']]['수량'] + order_dict['수량']
                self._balance[order_dict['주식코드']]['수량'] += order_dict['수량']
                self._balance[order_dict['주식코드']]['매매가능수량'] += order_dict['수량']
                self._balance[order_dict['주식코드']]['매입가'] = int(total_value / total_amount)
            self._deposit -= order_dict['수량'] * self._price_info[order_dict['주식코드']]['현재가']
            if self._deposit < 0:
                raise RuntimeError('주문가능금액이 충분하지 않습니다.')
        
        # 매도주문을 처리합니다.
        elif order_dict['구분'] == '매도':
            # 보유하지 않은 종목일 때
            if order_dict['주식코드'] not in self._balance:
                raise RuntimeError('보유하지 않은 종목은 팔 수 없습니다.')
            
            # 이미 보유한 종목일 때
            else:
                self._balance[order_dict['주식코드']]['수량'] -= order_dict['수량']
                self._balance[order_dict['주식코드']]['매매가능수량'] -= order_dict['수량']
            self._deposit += order_dict['수량'] * self._price_info[order_dict['주식코드']]['현재가']
            if self._balance[order_dict['주식코드']]['매매가능수량'] < 0:
                raise RuntimeError('보유 주식이 충분하지 않습니다.')
            elif self._balance[order_dict['주식코드']]['매매가능수량'] == 0:
                del self._balance[order_dict['주식코드']]
        
        cur_order_number = self._next_order_number
        self._next_order_number = f'{int(self._next_order_number) + 1:06}'
        return cur_order_number

    def get_order_info(self, order_number: str) -> Dict[str, str]:
        pass

    def register_price_info(self, stock_code_list: List[str], is_add: bool = False) -> None:
        pass

    def register_ask_bid_info(self, stock_code_list: List[str], is_add: bool = False) -> None:
        pass

    def get_price_info(self, stock_code: str) -> Dict[str, Any]:
        if stock_code not in self._price_info:
            price_dict = {}
            price_dict['체결시간'] = datetime.datetime.now().strftime('%H%M%S')
            price_dict['현재가'] = random.randint(int(START_PRICE_RANGE[0] / PRICE_UNIT), int(START_PRICE_RANGE[1] / PRICE_UNIT)) * PRICE_UNIT
            price_dict['고가'] = random.randint(int(price_dict['현재가'] / PRICE_UNIT), int(START_PRICE_RANGE[1] / PRICE_UNIT)) * PRICE_UNIT
            price_dict['저가'] = random.randint(int(START_PRICE_RANGE[0] / PRICE_UNIT), int(price_dict['현재가'] / PRICE_UNIT)) * PRICE_UNIT
            price_dict['시가'] = random.randint(int(price_dict['저가'] / PRICE_UNIT), int(price_dict['고가'] / PRICE_UNIT)) * PRICE_UNIT
            self._price_info[stock_code] = price_dict
        return self._price_info[stock_code]

    def get_ask_bid_info(self, stock_code: str) -> Dict[str, Any]:
        if stock_code not in self._ask_bid_info:
            ask_bid_dict = {}
            ask_bid_dict['호가시간'] = datetime.datetime.now().strftime('%H%M%S')
            ask_bid_dict['매수호가정보'] = []
            ask_bid_dict['매도호가정보'] = []
            cur_price = self.get_price_info(stock_code)['현재가']
            for i in range(10):
                ask_bid_dict['매수호가정보'].append((cur_price - i * 10, random.randint(START_ASK_BID_RANGE[0], START_ASK_BID_RANGE[1])))
                ask_bid_dict['매도호가정보'].append((cur_price + (i + 1) * 10, random.randint(START_ASK_BID_RANGE[0], START_ASK_BID_RANGE[1])))
            self._ask_bid_info[stock_code] = ask_bid_dict
        return self._ask_bid_info[stock_code]