from __future__ import annotations
import datetime
import logging
import time
import queue
from typing import Any
from PyQt5.QtCore import QMutex, QMutexLocker

from .decorators import trace
from .kiwoom_api_utils import KiwoomAPIUtils
from .market_data import MarketData
from .client_signal_handler import ClientSignalHandler

logger = logging.getLogger(__name__)

class Market():
    """
    주식시장을 구현한 클래스
    
    Client는 이 클래스의 메서드를 통해 주식과 계좌 정보를 얻고 이를 바탕으로 매매할 수 있습니다.
    여러 쓰레드가 동시에 메서드를 호출해도 안전합니다.
    """

    def __init__(self, client_signal_handler: ClientSignalHandler, data: MarketData):
        """
        KiwoomMarket의 components들을 생성하고 객체의 attribute를 설정합니다.

        Parameters
        ----------
        client_signal_handler : ClientSignalHandler
            _sig에 등록되어있는 신호를 emit함으로써 키움증권 서버에 요청을 보냅니다.
        data : KiwoomMarketData
            data 객체의 attribute를 접근함으로써 키움증권 서버로부터 온 데이터를 받습니다.
        """
        
        self._sig = client_signal_handler
        self._data = data

    @trace
    def initialize(self) -> None:
        """
        주식시장을 초기화(로그인 후 계좌번호를 로드)합니다.
        
        다른 메서드를 사용하기 전에 한번만 호출되어야 합니다.
        """
        while True:
            self._sig.login_request_signal.emit()
            login_result = self._data.buffer_for_login_result.get()
            if login_result == 0:
                break
        self._sig.account_number_request_signal.emit()

    @trace
    def get_condition(self) -> list[dict[str, Any]]:
        """
        조건검색식을 로드하고 각각의 이름과 인덱스를 반환합니다.

        Returns
        -------
        list[dict[str, Any]]
            dict의 list를 반환합니다.
            각 dict는 조건검색식을 의미합니다.
            
            dict = {
                'index': int,
                'name': str
            }
        """
        
        # 동시에 조건검색식을 요청했다면 이에 대한 응답이 서로 뒤바뀔 수 있습니다.
        # 다만 실제 영향은 미미합니다.
        self._sig.condition_request_signal.emit()
        condition_list = self._data.buffer_for_condition_list.get()
        return condition_list

    @trace
    def get_matching_stocks(self, condition_name: str, condition_index: int) -> list[str]:
        """
        주어진 조건검색식과 부합하는 주식 코드의 리스트를 반환합니다.

        Parameters
        ----------
        condition_name : str
            조건검색식의 이름입니다.
        condition_index : int
            조건검색식의 인덱스입니다.

        Returns
        -------
        list[str]
            부합하는 주식 종목의 코드 리스트를 반환합니다.
        """
        
        # 같은 condition에 대해 동시에 요청하였다면 이에 대한 응답이 서로 뒤바뀔 수 있습니다.
        # 다만 같은 condition에 대한 요청 결과이기에 영향은 미미합니다.
        self._data.condition_name_to_result[condition_name] = queue.Queue()
        self._sig.condition_search_request_signal.emit(condition_name, condition_index)
        matching_stocks = self._data.condition_name_to_result[condition_name].get()
        del self._data.condition_name_to_result[condition_name]
        return matching_stocks
    
    @trace
    def get_deposit(self) -> int:
        """
        계좌의 주문가능금액을 반환합니다.

        Returns
        -------
        int
            주문가능금액을 반환합니다.
        """
        request_name = KiwoomAPIUtils.create_request_name('GetDeposit-')
        self._data.request_name_to_tr_data[request_name] = queue.Queue()
        self._sig.deposit_request_signal.emit(request_name)
        deposit = self._data.request_name_to_tr_data[request_name].get()
        del self._data.request_name_to_tr_data[request_name]
        return deposit

    @trace
    def get_balance(self) -> dict[str, dict[str, Any]]:
        """
        보유주식정보를 반환합니다.
        
        주의: 연속조회는 아직 지원되지 않으므로 보유주식이 많을 경우 
        정보의 일부분만 전송될 수 있습니다.

        Returns
        -------
        dict[str, dict[str, Any]]
            보유주식정보를 반환합니다.
            dict[stock_code] = {
                '종목명': str,
                '수량': int,
                '매매가능수량': int,
                '매입가': int
                '현재가': int
                '수익률': float
            }
        """
        request_name = KiwoomAPIUtils.create_request_name('GetBalance-')
        self._data.request_name_to_tr_data[request_name] = queue.Queue()
        self._sig.balance_request_signal.emit(request_name)
        balance = self._data.request_name_to_tr_data[request_name].get()
        del self._data.request_name_to_tr_data[request_name]
        return balance
    
    @trace
    def request_order(self, order_dict: dict[str, Any]) -> str:
        """
        주문을 전송합니다.

        Parameters
        ----------
        order_dict : dict[str, Any]
            order_dict = {
                '구분': '매도' or '매수',
                '주식코드': str,
                '수량': int,
                '가격': int,
                '시장가': bool
            }
            
            시장가 주문을 전송할 경우 가격은 0으로 전달해야 합니다.

        Returns
        -------
        str
            unique한 주문 번호를 반환합니다.
        """
        request_name = KiwoomAPIUtils.create_request_name(f'RequestOrder-{order_dict["주식코드"]}-')
        self._data.request_name_to_tr_data[request_name] = queue.Queue()
        self._sig.order_request_signal.emit(order_dict, request_name)
        order_number = self._data.request_name_to_tr_data[request_name].get()
        del self._data.request_name_to_tr_data[request_name]
        return order_number
 
    @trace
    def get_order_info(self, order_number: str) -> dict[str, str]:
        """
        주문 번호을 가지고 주문 정보를 얻어옵니다.
        만약 주문이 전부 체결되지 않았다면 체결될 때까지 기다립니다.

        Parameters
        ----------
        order_number : str
            send_order 함수로 얻은 unique한 주문 번호입니다.

        Returns
        -------
        dict[str, str]
            주문 정보입니다.
        """
        lock = QMutex()
        with QMutexLocker(lock):
            while order_number not in self._data.order_number_to_info:
                self._data.order_info_ready.wait(lock)
        order_info = self._data.order_number_to_info[order_number]
        return order_info 
    
    @trace
    def register_price_info(self, stock_code_list: list[str], is_add: bool = False) -> None:
        """
        주어진 주식 코드에 대한 실시간 가격 정보를 등록합니다.

        Parameters
        ----------
        stock_code_list : list[str]
            실시간 정보를 등록하고 싶은 주식의 코드 리스트입니다.
        is_add : bool, optional
            True일시 화면번호에 존재하는 기존의 등록은 사라집니다.
            False일시 기존에 등록된 종목과 함께 실시간 정보를 받습니다.
            Default로 False입니다.
        """
        self._sig.price_register_request_signal.emit(stock_code_list, is_add)

    @trace
    def register_ask_bid_info(self, stock_code_list: list[str], is_add: bool = False) -> None:
        """
        주어진 주식 코드에 대한 실시간 호가 정보를 등록합니다.

        Parameters
        ----------
        stock_code_list : list[str]
            실시간 정보를 등록하고 싶은 주식의 코드 리스트입니다.
        is_add : bool, optional
            True일시 화면번호에 존재하는 기존의 등록은 사라집니다.
            False일시 기존에 등록된 종목과 함께 실시간 정보를 받습니다.
            Default로 False입니다.
        """
        self._sig.ask_bid_register_request_signal.emit(stock_code_list, is_add)

    @trace
    def get_price_info(self, stock_code: str) -> dict[str, Any]:
        """
        주어진 주식 코드에 대한 실시간 가격 정보를 가져옵니다.
        주식시장이 과열되면 일정시간동안 거래가 중지되어 정보가 들어오지 않을 수 있습니다.

        Parameters
        ----------
        stock_code : str
            실시간 정보를 가져올 주식 코드입니다.

        Returns
        -------
        dict[str, Any]
            주어진 주식 코드의 실시간 가격 정보입니다.
            info_dict = {
                '체결시간': str (HHMMSS),
                '현재가': int,
                '시가': int,
                '고가': int,
                '저가': int,
            }
        """
        while True:
            try:
                price_info = self._data.price_info[stock_code]
                break
            except KeyError:
                time.sleep(1)
        
        cur_time = datetime.datetime.now().replace(year=1900, month=1, day=1)
        info_time = datetime.datetime.strptime(price_info['체결시간'], '%H%M%S')
        time_delta = cur_time - info_time
        if time_delta.total_seconds() > 10:
            logger.warning('!!! 실시간 체결 데이터의 시간이 실제 시간과 큰 차이가 있습니다. !!!')
            logger.warning('!!! 주식이 상/하한가이거나 과열될 경우 일어날 수 있습니다. !!!')
            logger.warning(f'!!! {stock_code} - {info_time} vs {cur_time} !!!')
        return price_info
    
    @trace
    def get_ask_bid_info(self, stock_code: str) -> dict[str, Any]:
        """
        주어진 주식 코드에 대한 실시간 호가 정보를 가져옵니다.
        주식시장이 과열되면 일정시간동안 거래가 중지되어 정보가 들어오지 않을 수 있습니다.

        Parameters
        ----------
        stock_code : str
            실시간 정보를 가져올 주식 코드입니다.

        Returns
        -------
        dict[str, Any]
            주어진 주식 코드의 실시간 호가 정보입니다.
           info_dict = {
                '호가시간': str (HHMMSS),
                '매수호가정보': list[tuple[int, int]],
                '매도호가정보': list[tuple[int, int]],
            }
            
            매수호가정보는 (가격, 수량)의 호가정보가 리스트에 1번부터 10번까지 순서대로 들어있습니다.
            매도호가정보도 마찬가지입니다.
        """
        while True:
            try:
                ask_bid_info = self._data.ask_bid_info[stock_code]
                break
            except KeyError:
                time.sleep(1)
        
        cur_time = datetime.datetime.now().replace(year=1900, month=1, day=1)
        info_time = datetime.datetime.strptime(ask_bid_info['호가시간'], '%H%M%S')
        time_delta = cur_time - info_time
        if time_delta.total_seconds() > 10:
            logger.warning('!!! 실시간 호가 데이터의 시간이 실제 시간과 큰 차이가 있습니다. !!!')
            logger.warning('!!! 주식이 상/하한가이거나 과열될 경우 일어날 수 있습니다. !!!')
            logger.warning(f'!!! {stock_code} - {info_time} vs {cur_time} !!!')
        return ask_bid_info
            
    