import logging
import json
from PyQt5.QtNetwork import QTcpSocket

from .utils import *
from .kiwoom_api_const import *
from .kiwoom_ocx import KiwoomOCX

logger = logging.getLogger(__name__)

class ServerHandler():
    """
    서버로부터 보내진 수신 신호를 처리하는 클래스
    """

    def __init__(self, ocx: KiwoomOCX, socket: QTcpSocket):
        """
        서버 핸들러를 초기화합니다.

        Parameters
        ----------
        ocx : KiwoomOCX
            _description_
        socket: QTcpSocket
            Client 측의 요청을 읽기 위한 socket입니다.
            socket은 미리 연결되어있어야 합니다.
        """
        self._ocx = ocx
        self._socket = socket
        self._set_signal_slots_for_ocx(self._ocx)
        
    def _set_signal_slots_for_ocx(self, ocx: KiwoomOCX):
        ocx.OnEventConnect.connect(self._login_result_handler)
        ocx.OnReceiveTrData.connect(self._tr_data_handler)
        ocx.OnReceiveConditionVer.connect(self._condition_name_result_handler)
        ocx.OnReceiveTrCondition.connect(self._condition_search_result_handler)
        ocx.OnReceiveChejanData.connect(self._chejan_data_handler)
        ocx.OnReceiveRealData.connect(self._real_data_handler)
        ocx.OnReceiveMsg.connect(self._server_msg_handler)

    def _send_to_client(self, data_dict: dict):
        data = json.dumps(data_dict) + '\n'
        self._socket.write(data.encode())

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
            raise ConnectionError(f'로그인에 실패하였습니다. - err_code {result}')
        self._send_to_client({'type': 'login_result', 'key': '', 'value': result})
    
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
            deposit = clean_integer(self._ocx.get_comm_data(tr_code, request_name, 0, '주문가능금액'))
            tr_result = deposit
        
        # 보유 주식 요청
        elif tr_code == 'opw00018':
            balance_dict = {}
            info_num = self._ocx.get_repeat_cnt(tr_code, tr_name)
            for i in range(info_num):
                stock_code = clean_string(self._ocx.get_comm_data(tr_code, request_name, i, '종목번호'))
                stock_name = clean_string(self._ocx.get_comm_data(tr_code, request_name, i, '종목명'))
                amount = clean_integer(self._ocx.get_comm_data(tr_code, request_name, i, '보유수량'))
                available_amount = clean_integer(self._ocx.get_comm_data(tr_code, request_name, i, '매매가능수량'))
                purchased_price = clean_integer(self._ocx.get_comm_data(tr_code, request_name, i, '매입가'))

                # stock_code의 맨 앞 문자는 주식의 구분 알파벳이므로 제외합니다.
                stock_code = stock_code[1:]

                balance_dict[stock_code] = {
                    '종목코드': stock_code,
                    '종목명': stock_name,
                    '보유수량': amount,
                    '주문가능수량': available_amount,
                    '매입단가': purchased_price,
                }
            tr_result = balance_dict
        
        # 주식 기본 정보 요청
        elif tr_code == 'opt10001':
            cur_price = clean_integer(self._ocx.get_comm_data(tr_code, request_name, 0, '현재가'))
            start_price = clean_integer(self._ocx.get_comm_data(tr_code, request_name, 0, '시가'))
            high_price = clean_integer(self._ocx.get_comm_data(tr_code, request_name, 0, '고가'))
            low_price = clean_integer(self._ocx.get_comm_data(tr_code, request_name, 0, '저가'))
            info_dict = {
                '현재가': cur_price,
                '시가': start_price,
                '고가': high_price,
                '저가': low_price,
            }
            tr_result = info_dict
        
        # 주식 호가 정보 요청
        elif tr_code == 'opt10004':
            bid_info_list = []
            ask_info_list = []
            orders = ['최우선'] + [f'{i}차선' for i in range(2, 11)]
            # 키움증권 API가 6차선 때만 특별한 이유없이 일관성이 깨집니다.
            for order in orders:
                # 매수6차선호가 매수6차선잔량 (X), 매수6우선호가 매수6우선잔량 (O)
                if order == '6차선':
                    order = '6우선'
                cur_bid_price = self._ocx.get_comm_data(tr_code, request_name, 0, f'매수{order}호가')
                cur_bid_amount = self._ocx.get_comm_data(tr_code, request_name, 0, f'매수{order}잔량')
                bid_info_list.append((int(cur_bid_price.strip('+- ')), int(cur_bid_amount.strip('+- '))))
            for order in orders:
                cur_ask_price = self._ocx.get_comm_data(tr_code, request_name, 0, f'매도{order}호가')
                # 매도6차선잔량 (X), 매도6우선잔량 (O)
                if order == '6차선':
                    order = '6우선'
                cur_ask_amount = self._ocx.get_comm_data(tr_code, request_name, 0, f'매도{order}잔량')
                ask_info_list.append((int(cur_ask_price.strip('+- ')), int(cur_ask_amount.strip('+- '))))
            info_dict = {
                '매수호가정보': bid_info_list,
                '매도호가정보': ask_info_list,
            }
            tr_result = info_dict
        
        # 거래량 급증 주식 요청
        elif tr_code == 'opt10023':
            stock_codes = []
            info_num = self._ocx.get_repeat_cnt(tr_code, tr_name)
            for i in range(info_num):
                stock_code = clean_string(self._ocx.get_comm_data(tr_code, request_name, i, '종목코드'))
                stock_codes.append(stock_code)
            tr_result = stock_codes

        # 주문 요청
        elif (tr_code == 'KOA_NORMAL_BUY_KP_ORD' or tr_code == 'KOA_NORMAL_SELL_KP_ORD' or
             tr_code == 'KOA_NORMAL_BUY_KQ_ORD' or tr_code == 'KOA_NORMAL_SELL_KQ_ORD' or
             tr_code == 'KOA_NORMAL_KP_CANCEL' or tr_code == 'KOA_NORMAL_KQ_CANCEL'):
            # 주문 요청이 들어오면 주문 번호를 받고 보냅니다.
            order_number = clean_string(self._ocx.get_comm_data(tr_code, request_name, 0, '주문번호'))
            tr_result = order_number
            
        else:
            raise NotImplementedError(f'아직 구현되지 않은 TR 코드 - {tr_code} 입니다.')
        
        self._send_to_client({'type': 'tr_result', 'key': request_name, 'value': (tr_result, next_data)})

    @trace
    def _condition_name_result_handler(self, is_success: int, msg: str) -> None:
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
            raise ConnectionError(f'조건검색식을 불러오는 준비에 실패하였습니다. err_code - {is_success}')
        
        condition_list = []
        result = self._ocx.get_condition_name_list()
        index_and_name_list = result.split(';')[:-1]
        for index_and_name in index_and_name_list:
            index, name = index_and_name.split('^')
            condition_list.append({'name': name, 'index': int(index)})
        self._send_to_client({'type': 'condition_names', 'key': '', 'value': condition_list})

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
        self._send_to_client({'type': 'matching_stocks', 'key': condition_name, 'value': stock_code_list})

    @trace
    def _chejan_data_handler(self, data_type: str, info_num: int, fid_list: str) -> None:
        """
        체결 혹은 잔고 관련 데이터에 변화가 있었을 시 호출되는 핸들러입니다.

        미체결클리어의 경우 정정 혹은 취소 주문에서 발생하며 
        주문이 일부 체결되었을 경우 체결로, 그렇지 않을 경우 접수로 들어옵니다.

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
            order_number = clean_string(self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문번호']))
            stock_code = clean_string(self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목코드']))
            stock_name = clean_string(self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목명']))
            order_status = clean_string(self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문상태']))
            order_type = clean_string(self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문구분']))
            order_amount = clean_integer(self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문수량']))
            traded_price = clean_integer(self._ocx.get_chejan_data(KOR_NAME_TO_FID['체결가']))
            traded_amount = clean_integer(self._ocx.get_chejan_data(KOR_NAME_TO_FID['체결량']))
            nontraded_amount = clean_integer(self._ocx.get_chejan_data(KOR_NAME_TO_FID['미체결수량']))
            
            if order_status == '접수':
                # 다른 접수 신호는 무시하고 미체결 클리어 신호만 처리합니다.
                if nontraded_amount == 0:
                    info_dict = {
                        '종목코드': stock_code,
                        '종목명': stock_name,
                        '주문상태': order_status,
                        '주문구분': order_type,
                        '주문수량': order_amount,
                        '체결가': 0,
                        '체결량': 0,
                        '미체결수량': 0,
                        '주문번호': order_number,
                    }
                    self._send_to_client({'type': 'order_result', 'key': order_number, 'value': info_dict})

            elif order_status == '확인':
                if order_type == '매수취소' or order_type == '매도취소':
                    self._send_to_client({'type': 'order_result', 'key': order_number, 'value': {}})
                else:
                    raise NotImplementedError(f'예상치 못한 주문구분 - {order_type} 입니다.')
            
            elif order_status == '체결':
                info_dict = {
                    '종목코드': stock_code,
                    '종목명': stock_name,
                    '주문상태': order_status,
                    '주문구분': order_type,
                    '주문수량': order_amount,
                    '체결가': traded_price,
                    '체결량': traded_amount,
                    '미체결수량': nontraded_amount,
                    '주문번호': order_number,
                }
                logger.info(f'{info_dict["종목코드"]} {info_dict["종목명"]} - 주문이 일부 혹은 완전히 체결되었습니다.')
                logger.info(f'{info_dict["종목코드"]} {info_dict["종목명"]} - 체결량: {info_dict["체결량"]}, 주문수량: {info_dict["주문수량"]}')
                
                # 주문이 완전히 체결되었을 때만 보냅니다.
                if nontraded_amount == 0:
                    self._send_to_client({'type': 'order_result', 'key': order_number, 'value': info_dict})
            
            else:
                raise NotImplementedError(f'확인되지 않은 주문 상태 - {order_status}입니다.')

        # 잔고 관련 데이터
        elif data_type == '1':
            stock_code = clean_string(self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목코드']))
            stock_name = clean_string(self._ocx.get_chejan_data(KOR_NAME_TO_FID['종목명']))
            total_amount = clean_integer(self._ocx.get_chejan_data(KOR_NAME_TO_FID['보유수량']))
            available_amount = clean_integer(self._ocx.get_chejan_data(KOR_NAME_TO_FID['주문가능수량']))
            avg_buy_price = clean_integer(self._ocx.get_chejan_data(KOR_NAME_TO_FID['매입단가']))

            # 종목코드 맨 앞의 속성 구분 알파벳은 제거합니다.
            info_dict = {
                '종목코드': stock_code[1:],
                '종목명': stock_name,
                '보유수량': total_amount,
                '주문가능수량': available_amount,
                '매입단가': avg_buy_price,
            }
            self._send_to_client({'type': 'balance_change', 'key': info_dict['종목코드'], 'value': info_dict})

        elif data_type == '4':
            raise NotImplementedError('파생잔고 변경은 아직 구현되지 않았습니다.')

    @trace
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
        
        # 실시간 가격 정보를 등록한 뒤 주식이 체결되었을 때 발생하는 신호
        # '체결 시간'은 HHMMSS의 문자열 포맷으로 전달됩니다.
        if signal_type == '주식체결':
            cur_price = clean_integer(self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['현재가']))
            start_price = clean_integer(self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['시가']))
            high_price = clean_integer(self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['고가']))
            low_price = clean_integer(self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID['저가']))
            info_dict = {
                '현재가': cur_price,
                '시가': start_price,
                '고가': high_price,
                '저가': low_price,
            }
            self._send_to_client({'type': 'price_change', 'key': stock_code, 'value': info_dict})


        # 실시간 호가정보를 등록한 뒤 호가의 변경이 일어났을 때 발생하는 신호
        elif signal_type == '주식호가잔량':
            bid_info_list = []
            ask_info_list = []
            for num in range(10):
                cur_bid_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID[f'매수호가{num + 1}'])
                cur_bid_amount = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID[f'매수호가 수량{num + 1}'])
                cur_bid_price, cur_bid_amount = clean_integer(cur_bid_price), clean_integer(cur_bid_amount)
                bid_info_list.append((cur_bid_price, cur_bid_amount))
            for num in range(10):
                cur_ask_price = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID[f'매도호가{num + 1}'])
                cur_ask_amount = self._ocx.get_comm_real_data(stock_code, KOR_NAME_TO_FID[f'매도호가 수량{num + 1}'])
                cur_ask_price, cur_ask_amount = clean_integer(cur_ask_price), clean_integer(cur_ask_amount)
                ask_info_list.append((cur_ask_price, cur_ask_amount))
            info_dict = {
                '매수호가정보': bid_info_list,
                '매도호가정보': ask_info_list,
            }
            self._send_to_client({'type': 'ask_bid_change', 'key': stock_code, 'value': info_dict})

        # 장외주식호가
        elif signal_type == 'ECN주식호가잔량':
            pass
        # 장외주식체결
        elif signal_type == 'ECN주식체결':
            pass
        # 동시 호가시 예상되는 체결 관련 정보
        elif signal_type == '주식예상체결':
            pass
        # 장 시작하기 이전에 보내지는 신호
        elif signal_type == '장시작시간':
            pass
        # 최우선호가 정보
        elif signal_type == '주식우선호가':
            pass
        else:
            logger.debug(f'예상치 못한 signal_type - {signal_type}이 전송되었습니다.')
    
    @trace
    def _server_msg_handler(self, screen_no: str, request_name: str, tr_code: str, msg: str) -> None:
        """
        서버로부터 메세지를 전송받았을 때 동작하는 핸들러입니다.
        """
        logger.info(f'SERVER MSG: "{request_name}"로부터 "{msg}"를 전송받았습니다.')
