import logging
import datetime

from .decorators import trace
from .kiwoom_api_const import KOR_NAME_TO_FID, FID_TO_KOR_NAME
from .kiwoom_ocx import KiwoomOCX
from .market_data import MarketData

logger = logging.getLogger(__name__)

class ServerSignalHandler():
    """
    서버로부터 보내진 수신 신호를 처리하는 클래스
    """

    def __init__(self, ocx: KiwoomOCX, data: MarketData):
        super().__init__()
        self._ocx = ocx
        self._data = data
        self._set_signal_slots_for_ocx(self._ocx)
        
    def _set_signal_slots_for_ocx(self, ocx: KiwoomOCX):
        ocx.OnEventConnect.connect(self._login_result_handler)
        ocx.OnReceiveTrData.connect(self._tr_data_handler)
        ocx.OnReceiveConditionVer.connect(self._condition_result_handler)
        ocx.OnReceiveTrCondition.connect(self._condition_search_result_handler)
        ocx.OnReceiveChejanData.connect(self._chejan_data_handler)
        ocx.OnReceiveRealData.connect(self._real_data_handler)
        ocx.OnReceiveMsg.connect(self._server_msg_handler)


    @trace
    def _login_result_handler(self, result: int) -> None:
        """
        로그인 시도 결과가 준비되었을 때 호출되는 handler입니다.

        Parameters
        ----------
        result : int
            0이면 성공적으로 로그인했음을, 그 이외의 값은 실패했음을 의미합니다.
            자세한 정보는 개발가이드를 참조하세요.
        """
        if result == 0:
            logger.info('성공적으로 로그인했습니다.')
        else:
            raise ConnectionError(f'!!! 로그인에 실패하였습니다. - err_code {result} !!!')
        self._data.login_result.put(result, block=False)
    
    @trace
    def _tr_data_handler(self, screen_no: str, request_name: str, tr_code: str, tr_name: str, next_data: int,
                         unused1, unused2, unused3, unused4) -> None:
        """
        TR 데이터가 준비되었을 때 호출되는 핸들러입니다.

        Parameters
        ----------
        screen_no : str
            화면번호입니다.
        request_name : str
            unique한 요청의 이름입니다.
        tr_code : str
            요청한 데이터의 TR 코드입니다.
        tr_name : str
            TR 코드의 이름입니다.
        next_data : int
            연속 조회의 필요 여부를 나타냅니다. 0일시 필요없음을, 2일시 필요함을 의미합니다.
            멀티 데이터일 때 해당됩니다.
        """
        # 주문 가능 금액 요청
        if tr_code == 'opw00001':
            deposit = self._ocx.get_comm_data(tr_code, request_name, 0, '주문가능금액')
            deposit = int(deposit)
            self._data.request_name_to_tr_data[request_name].put(deposit, block=False)
        
        # 보유 주식 요청
        elif tr_code == 'opw00018':
            balance_dict = {}
            info_num = self._ocx.get_repeat_cnt(tr_code, tr_name)
            for i in range(info_num):
                stock_code = self._ocx.get_comm_data(tr_code, request_name, i, '종목번호')
                stock_name = self._ocx.get_comm_data(tr_code, request_name, i, '종목명')
                amount = self._ocx.get_comm_data(tr_code, request_name, i, '보유수량')
                available_amount = self._ocx.get_comm_data(tr_code, request_name, i, '매매가능수량')
                purchased_price = self._ocx.get_comm_data(tr_code, request_name, i, '매입가')
                current_price = self._ocx.get_comm_data(tr_code, request_name, i, '현재가')
                profit_percentage = self._ocx.get_comm_data(tr_code, request_name, i, '수익률(%)')
                
                # stock_code의 맨 앞 문자는 주식의 구분 알파벳이므로 제외합니다.
                balance_dict[stock_code.strip()[1:]] = {
                    '종목코드': stock_code.strip()[1:],
                    '종목명': stock_name.strip(),
                    '보유수량': int(amount),
                    '주문가능수량': int(available_amount),
                    '매입단가': int(purchased_price),
                }
            # 결과는 request_name_to_tr_data에 저장되지 않고 _data.balance를 초기화하는 데에 사용됩니다.
            self._data.balance = balance_dict
        
        # 주문 요청
        elif tr_code == 'KOA_NORMAL_BUY_KP_ORD' or tr_code == 'KOA_NORMAL_SELL_KP_ORD' or\
             tr_code == 'KOA_NORMAL_BUY_KQ_ORD' or tr_code == 'KOA_NORMAL_SELL_KQ_ORD':
                 
            # 주문 번호를 저장합니다.
            order_number = self._ocx.get_comm_data(tr_code, request_name, 0, '주문번호')
            self._data.request_name_to_tr_data[request_name].put(order_number, block=False)
            
        else:
            raise NotImplementedError(f'!!! 아직 구현되지 않은 TR 코드 - {tr_code} 입니다. !!!')

    @trace
    def _condition_result_handler(self, is_success: int, msg: str) -> None:
        """
        조건검색식이 요청에 따라 로드되었을 때 호출되는 핸들러입니다.
        
        조건검색식의 이름과 인덱스를 요청하고 이를 client에게 전달하기 위해 저장합니다.

        Parameters
        ----------
        is_success : int
            로드가 성공했으면 1, 실패했다면 그 이외의 값을 전달받습니다.
        msg : str
            서버로부터의 메세지입니다.
        """
        if is_success == 1:
            logger.info('조건검색식이 준비되었습니다.')
        else:
            raise ConnectionError(f'!!! 조건검색식을 불러오는 준비에 실패하였습니다. err_code - {is_success} !!!')
        
        condition_list = []
        result = self._ocx.get_condition_name_list()
        index_and_name_list = result.split(';')[:-1]
        for index_and_name in index_and_name_list:
            index = int(index_and_name.split('^')[0])
            name = index_and_name.split('^')[1]
            condition_list.append({'name': name, 'index': index})
        self._data.condition_list.put(condition_list, block=False)

    @trace
    def _condition_search_result_handler(self, screen_no: str, stock_codes: str, condition_name: str, 
                                         condition_index: int, next_data: int) -> None:
        """
        조건검색식과 부합하는 종목 검색을 완료했을 때 호출되는 핸들러입니다.

        Parameters
        ----------
        screen_no : str
            화면번호입니다.
        stock_codes : str
            조건 검색식과 부합하는 종목들입니다. ';'로 구분되어 있습니다.
        condition_name : str
            검색에 사용된 조건 검색식의 이름입니다.
        condition_index : int
            검색에 사용된 조건 검색식의 인덱스입니다.
        next_data : int
            연속 조회가 필요한지 나타내는 값입니다. 0이면 필요없음을, 2이면 필요함을 의미합니다.
        """
        stock_code_list = stock_codes.split(';')[:-1]
        self._data.condition_name_to_result[condition_name].put(stock_code_list, block=False)

    @trace
    def _chejan_data_handler(self, data_type: str, info_num: int, fid_list: str) -> None:
        """
        체결 혹은 잔고 관련 데이터에 변화가 있었을 시 호출되는 핸들러입니다.

        Parameters
        ----------
        data_type : str
            체결 관련 데이터인지 잔고 관련 데이터인지 구분해주는 타입입니다.
            '0'일 경우 체결관련 데이터이며 '1'일 경우 잔고관련 데이터입니다.
        info_num : int
            데이터에서 가져올 수 있는 FID의 개수입니다.
        fid_list : str
            데이터에서 가져올 수 있는 FID의 리스트입니다.
            ';'로 구분되어 있습니다.
        """
        # 체결 관련 데이터
        if data_type == '0':
            stock_code = self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목코드'])
            stock_name = self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목명'])
            order_status = self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문상태'])
            order_amount = self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문수량'])
            traded_amount = self._ocx.get_chejan_data(KOR_NAME_TO_FID['체결량'])
            order_number = self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문번호'])
            
            # 아마 접수 시에 일부 항목이 공백으로 오는듯.. 제대로된 확인 필요
            if traded_amount.strip() == '':
                # print(stock_code, stock_name, order_status, order_amount, traded_amount, order_number)
                return
            
            info_dict = {
                '종목코드': stock_code.strip(),
                '종목명': stock_name.strip(),
                '주문상태': order_status.strip(),
                '주문수량': int(order_amount.strip('+- ')),
                '체결량': int(traded_amount.strip('+- ')),
                '주문번호': order_number.strip(),
            }
            if info_dict['주문상태'] == '체결' and info_dict['체결량'] == info_dict['주문수량']:
                logger.info(f'{info_dict["종목코드"]} {info_dict["종목명"]} - 주문이 완전히 체결되었습니다.')
                self._data.order_number_to_info[info_dict['주문번호']] = info_dict
            else:
                logger.info(f'{info_dict["종목코드"]} {info_dict["종목명"]} - 주문이 일부 체결되었습니다.')
                logger.info(f'{info_dict["종목코드"]} {info_dict["종목명"]} - 체결량: {info_dict["체결량"]}, 주문수량: {info_dict["주문수량"]}')
        
        # 잔고 관련 데이터
        elif data_type == '1':
            stock_code = self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목코드'])
            stock_name = self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목명'])
            total_amount = self._ocx.get_chejan_data(KOR_NAME_TO_FID['보유수량'])
            available_amount = self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문가능수량'])
            avg_buy_price = self._ocx.get_chejan_data(KOR_NAME_TO_FID['매입단가'])

            info_dict = {
                '종목코드': stock_code.strip()[1:],
                '종목명': stock_name.strip(),
                '보유수량': int(total_amount.strip('+- ')),
                '주문가능수량': int(available_amount.strip('+- ')),
                '매입단가': int(avg_buy_price.strip('+- ')),
            }
            if info_dict['보유수량'] == 0:
                if stock_code.strip()[1:] in self._data.balance:
                    del self._data.balance[stock_code.strip()[1:]]
            else:
                self._data.balance[stock_code.strip()[1:]] = info_dict

        elif data_type == '4':
            raise NotImplementedError('!!! 파생잔고 변경은 아직 구현되지 않았습니다. !!!')

    # @trace
    def _real_data_handler(self, stock_code: str, signal_type: str, unused) -> None:
        """
        서버로부터 실시간 데이터를 수신받았을 때 호출되는 핸들러입니다.

        Parameters
        ----------
        stock_code : str
            실시간 데이터의 주식 코드입니다.
        signal_type : str
            받은 실시간 데이터가 어떤 종류인지 나타냅니다.
        """
        
        # 실시간 가격 정보를 등록한 뒤 주식이 체결되었을 때 발생하는 signal입니다.
        if signal_type == '주식체결':
            # 체결 시간은 HHMMSS의 문자열 포맷으로 전달되며, 이를 통해 datetime 객체를 만듭니다.
            transacted_at = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['체결시간'])
            date = datetime.datetime.now()
            time = datetime.datetime.strptime(transacted_at.strip(), '%H%M%S')
            date_with_time = datetime.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
            cur_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['현재가'])
            start_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['시가'])
            high_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['고가'])
            low_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['저가'])
            info_dict = {
                '체결시간': date_with_time,
                '현재가': int(cur_price.strip('+- ')),
                '시가': int(start_price.strip('+- ')),
                '고가': int(high_price.strip('+- ')),
                '저가': int(low_price.strip('+- ')),
            }
            self._data.price_info[stock_code] = info_dict


        # 실시간 호가정보를 등록한 뒤 호가의 변경이 일어났을 때 발생하는 signal입니다.
        elif signal_type == '주식호가잔량':
            # 호가 시간은 HHMMSS의 문자열 포맷으로 전달됩니다.
            bided_or_asked_at = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['호가시간'])
            date = datetime.datetime.now()
            time = datetime.datetime.strptime(bided_or_asked_at.strip(), '%H%M%S')
            date_with_time = datetime.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)

            # 매수/매도 호가 정보를 각각 RANGE개 기록합니다.
            RANGE = 10
            bid_info_list = []
            ask_info_list = []
            for num in range(1, RANGE + 1):
                cur_bid_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['매수호가' + str(num)])
                cur_bid_amount = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['매수호가 수량' + str(num)])
                bid_info_list.append((int(cur_bid_price.strip('+- ')), int(cur_bid_amount.strip('+- '))))
            for num in range(1, RANGE + 1):
                cur_ask_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['매도호가' + str(num)])
                cur_ask_amount = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['매도호가 수량' + str(num)])
                ask_info_list.append((int(cur_ask_price.strip('+- ')), int(cur_ask_amount.strip('+- '))))
            info_dict = {
                '호가시간': date_with_time,
                '매수호가정보': bid_info_list,
                '매도호가정보': ask_info_list,
            }
            self._data.ask_bid_info[stock_code] = info_dict

        # 장외주식호가
        elif signal_type == 'ECN주식호가잔량':
            pass
        # 장외주식체결
        elif signal_type == 'ECN주식체결':
            pass
        # 동시 호가시 예상되는 체결 관련 정보...인듯?
        elif signal_type == '주식예상체결':
            pass
        elif signal_type == '장시작시간':
            pass
        else:
            logger.warning(f'!!! 예상치 못한 signal_type - {signal_type}이 전송되었습니다. !!!')
    
    @trace
    def _server_msg_handler(self, screen_no: str, request_name: str, tr_code: str, msg: str) -> None:
        """
        서버로부터 메세지를 전송받았을 때 동작하는 핸들러입니다.
        """
        logger.info(f'SERVER MSG: \'{request_name}\'로부터 \'{msg}\'를 전송받았습니다.')
