import logging
from typing import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from .decorators import trace
from .kiwoom_api_utils import KiwoomAPIUtils
from .kiwoom_api_const import KOR_NAME_TO_FID
from .kiwoom_ocx import KiwoomOCX
from .market_data import MarketData

logger = logging.getLogger(__name__)

class ClientSignalHandler(QWidget):
    """
    Client로부터 보내진 요청 신호를 처리하는 클래스
    """
    
    # client로부터 요청이 왔다고 알려주는 signal들
    login_request_signal = pyqtSignal()
    account_number_request_signal = pyqtSignal()
    condition_request_signal = pyqtSignal()
    condition_search_request_signal = pyqtSignal(str, int)
    deposit_request_signal = pyqtSignal(str)
    balance_request_signal = pyqtSignal(str)
    order_request_signal = pyqtSignal(dict, str)
    price_register_request_signal = pyqtSignal(list, bool) 
    ask_bid_register_request_signal = pyqtSignal(list, bool)

    def __init__(self, ocx: KiwoomOCX, data: MarketData):
        """
        ClientSignalHandler 클래스의 객체를 초기화합니다.

        Parameters
        ----------
        ocx : KiwoomOCX
            키움증권 측과 OCX로 통신하기 위해 사용되는 객체입니다.
            이 객체의 메서드를 호출함으로써 키움증권 Open API를 사용할 수 있습니다.
        data : KiwoomData
            Client로 데이터를 전송하기 위해 사용되는 저장공간입니다.
            따라서 주로 ServerSignalHandler 클래스에서 사용되지만 이 클래스에서도
            _order_request_handler에서 생성된 주문 이름을 전달해주기 위해 사용됩니다.
        """
        super().__init__()
        self._ocx = ocx
        self._data = data
        self._account_number = None
        self._set_client_signal_slots()

    def _set_client_signal_slots(self) -> None:
        """
        client가 보낼 신호와 핸들러를 알맞게 연결시켜줍니다.
        """
        self.login_request_signal.connect(self._login_request_handler)
        self.account_number_request_signal.connect(self._account_number_request_handler)
        self.condition_request_signal.connect(self._condition_request_handler)
        self.condition_search_request_signal.connect(self._condition_search_request_handler)
        self.deposit_request_signal.connect(self._deposit_request_handler)
        self.balance_request_signal.connect(self._balance_request_handler)
        self.order_request_signal.connect(self._order_request_handler)
        self.price_register_request_signal.connect(self._price_register_request_handler)
        self.ask_bid_register_request_signal.connect(self._ask_bid_register_request_handler)

    @trace
    def _login_request_handler(self) -> None:
        """
        clinet으로부터 로그인 시도 요청을 받았을 때 호출되는 handler입니다.
        """
        result = self._ocx.comm_connect()
        if result == 0:
            logger.info('로그인 시도 요청에 성공하였습니다.')
        else:
            raise ConnectionError(f'!!! 로그인 시도 요청에 실패하였습니다. err_code - {result}')
            
    @trace
    def _account_number_request_handler(self) -> None:
        """
        client으로부터 계좌번호 로드 요청을 받았을 때 호출되는 handler입니다.
        
        계좌번호는 self.account_number에 저장되며 이는 다른 API 호출에 파라미터로 사용됩니다.
        """
        account_list = self._ocx.get_login_info('ACCLIST')
        account_list = account_list.split(';')[:-1]
        if len(account_list) > 1:
            logger.warning(f'다수의 계정이 검색되었습니다: {account_list}')
            logger.warning(f'첫번째 계정이 선택됩니다.')
        self.account_number = account_list[0]
        logger.info('계좌번호 로드가 성공하였습니다.')
    
    @trace
    def _condition_request_handler(self) -> None:
        """
        client으로부터 조건검색식 요청을 받았을 때 호출되는 handler입니다.
        
        조건검색식을 로드 후 ServerSignalHandler 측에서 각 검색식의 이름과 인덱스를 가져옵니다.
        """
        is_success = self._ocx.get_condition_load()
        if is_success == 1:
            logger.info('조건 검색식 로드 요청이 성공하였습니다.')
        else:
            raise ConnectionError(f'!!! 조건 검색식 로드 요청이 실패하였습니다. err_code - {is_success} !!!')

    @trace
    def _condition_search_request_handler(self, condition_name: str, condition_index: int) -> None:
        """
        client으로부터 조건검색식과 부합하는 종목 검색 요청 신호를 받았을 때 호출되는 handler입니다.

        Parameters
        ----------
        condition_name : str
            조건검색식의 이름입니다.
        condition_index : int
            조건검색식의 인덱스입니다.
        """ 
        screen_no = KiwoomAPIUtils.get_screen_no()
        is_success = self._ocx.send_condition(screen_no, condition_name, condition_index, 0)
        if is_success == 1:
            logger.info('조건검색식에 부합하는 종목검색에 성공하였습니다.')
        else:
            raise RuntimeError(f'!!! 조건검색식에 부합하는 종목검색에 실패하였습니다. err_code - {is_success} !!!')

    @trace
    def _deposit_request_handler(self, request_name: str) -> None:
        """
        client으로부터 주문가능금액 조회 요청 신호를 받았을 때 호출되는 handler입니다.
        """
        self._ocx.set_input_value('계좌번호', self.account_number)
        self._ocx.set_input_value('비밀번호입력매체구분', '00')
        self._ocx.set_input_value('조회구분', '2')
        screen_no = KiwoomAPIUtils.get_screen_no()
        result = self._ocx.comm_rq_data(request_name, 'opw00001', 0, screen_no)
        if result == 0:
            logger.info('주문가능금액 조회에 성공하였습니다.')
        else:
            raise RuntimeError(f'!!! 주문가능금액 조회에 실패하였습니다. err_code - {result} !!!')
    
    @trace
    def _balance_request_handler(self, request_name: str) -> None:
        """
        client으로부터 보유주식 조회 요청 신호를 받았을 때 호출되는 handler입니다.
        """
        self._ocx.set_input_value('계좌번호', self.account_number)
        self._ocx.set_input_value('비밀번호입력매체구분', '00')
        self._ocx.set_input_value('조회구분', '1')
        screen_no = KiwoomAPIUtils.get_screen_no()
        result = self._ocx.comm_rq_data(request_name, 'opw00018', 0, screen_no)
        if result == 0:
            logger.info('보유주식 조회 요청에 성공하였습니다.')
        else:
            raise RuntimeError(f'!!! 보유주식 조회 요청에 실패하였습니다. err_code - {result}!!!')
    
    @trace
    def _order_request_handler(self, order_dict: Dict[str, Any], order_name: str) -> None:
        """
        client으로부터 주문을 전송하겠다는 신호를 받았을 때 동작하는 핸들러입니다.

        Parameters
        ----------
        order_dict : Dict[str, Any]
            주문의 정보가 들어가있는 dict입니다.
            
            order_dict = {
                '구분': '매수' or '매도',
                '주식코드': str,
                '수량': int,
                '가격': int,
                '시장가': bool
            }
        """
        screen_no = KiwoomAPIUtils.get_screen_no()
        
        # arguments들을 Open API 인터페이스에 맞도록 다듬어줍니다.
        if order_dict['구분'] == '매수':
            order_type = 1
        elif order_dict['구분'] == '매도':
            order_type = 2
        else:
            raise ValueError(f'!!! 유효하지 않은 주문 타입입니다. - {order_dict["구분"]} !!!')
        stock_code = order_dict['주식코드']
        amount = order_dict['수량']
        price = order_dict['가격']
        if order_dict['시장가'] is True:
            how = '03'
            if price != 0:
                raise ValueError('!!! 시장가 주문의 경우 가격을 0으로 설정해야 합니다. !!!')
        else:
            how = '00'

        # send_order API를 호출합니다.
        params = [order_name, screen_no, self.account_number, order_type, stock_code, amount, price, how, '']
        result = self._ocx.send_order(*params)
        if result == 0:
            logger.info('정상적으로 주문이 전송되었습니다.')
        elif result == -308:
            raise ConnectionError('!!! 너무 많은 주문이 동시에 전송되어 실패하였습니다. (최대 1초에 5번) !!!')
        else:
            raise RuntimeError(f'!!! 주문 전송에 실패하였습니다. err_code - {result} !!!')

    @trace
    def _price_register_request_handler(self, stock_code_list: List[str], is_add: bool) -> None:
        """
        client으로부터 실시간 가격정보를 등록하겠다는 신호를 받았을 때 호출되는 핸들러입니다.
        
        _register_real_time_info 함수의 wrapper function입니다.
        """
        fid_list = [KOR_NAME_TO_FID['현재가'], KOR_NAME_TO_FID['시가'], KOR_NAME_TO_FID['고가']]
        self._register_real_time_info(stock_code_list, fid_list, is_add)
    
    @trace
    def _ask_bid_register_request_handler(self, stock_code_list: List[str], is_add: bool) -> None:
        """
        client으로부터 실시간 호가정보를 등록하겠다는 신호를 받았을 때 호출되는 핸들러입니다.
        
        _register_real_time_info 함수의 wrapper function입니다.
        """
        fid_list = [KOR_NAME_TO_FID['매수호가1'], KOR_NAME_TO_FID['매수호가 수량1']]
        self._register_real_time_info(stock_code_list, fid_list, is_add)

    @trace
    def _register_real_time_info(self, stock_code_list: List[str], fid_list: List[str], is_add: bool) -> None:
        """
        실시간 정보를 받겠다고 등록하는 함수입니다.

        Parameters
        ----------
        stock_code_list : List[str]
            실시간 정보를 등록할 종목 코드의 리스트입니다.
        fid_list : List[str]
            받고 싶은 fid들의 리스트입니다.
            이에 따라 전송되는 실시간 정보의 signal이 달라집니다.
        is_add : bool
            True일시 화면번호에 존재하는 기존의 등록은 사라집니다.
            False일시 기존에 등록된 종목과 함께 실시간 정보를 받습니다.
        """
        screen_no = KiwoomAPIUtils.get_screen_no()
        
        # arguments들을 Open API 인터페이스에 맞도록 다듬어줍니다.
        if is_add is True:
            is_add = '1'
        elif is_add is False:
            is_add = '0'
        stock_code_str = ''
        for stock_code in stock_code_list:
            stock_code_str += stock_code + ';'
        fid_str = ''
        for fid in fid_list:
            fid_str += fid + ';'
        
        # set_real_reg API를 호출합니다.
        result = self._ocx.set_real_reg(screen_no, stock_code_str, fid_str, is_add)
        if result == 0:
            logger.info('실시간 정보가 정상적으로 등록되었습니다.')
        else:
            raise RuntimeError(f'!!! 등록에 실패하였습니다. err_code - {result} !!!')
