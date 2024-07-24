import platform
import logging
from PyQt5.QAxContainer import QAxWidget

logger = logging.getLogger(__name__)

class KiwoomOCX(QAxWidget):

    def __init__(self):
        """
        키움증권 Open API를 제공하는 COM 객체와 연결합니다.
        """
        super().__init__()
        if platform.architecture()[0] != '32bit':
            logger.critical('32bit 환경이 필요합니다.')
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1')

    def comm_connect(self) -> int:
        """
        키움증권 로그인 창을 띄우고 만약 자동 로그인 설정이 되어있다면 로그인을 시도합니다.

        Returns
        -------
        int
            로그인이 성공했다면 0을, 실패했다면 음수값을 리턴합니다.
        """
        result = self.dynamicCall('CommConnect()')
        return result
    
    def get_connect_state(self) -> int:
        """
        키움증권에 로그인 되었는지 확인합니다.

        Returns
        -------
        int
            로그인이 되어있는 상태라면 1을, 그렇지 않으면 0을 리턴합니다.
        """
        result = self.dynamicCall('GetConnectState()')
        return result

    def get_login_info(self, info_type: str) -> str:
        """
        로그인 정보를 가져옵니다.

        Parameters
        ----------
        info_type : str
            로그인 정보의 종류입니다.

            ACCOUNT_CNT - 보유계좌 갯수\n
            ACCLIST 또는 ACCNO - 구분자 ';'로 연결된 보유계좌 목록\n
            USER_ID - 사용자 ID\n
            USER_NAME - 사용자 이름\n
            GetServerGubun - 접속서버 구분 (1 : 모의투자, 나머지 : 실거래서버)\n
            KEY_BSECGB - 키보드 보안 해지여부(0 : 정상, 1 : 해지)\n
            FIREW_SECGB - 방화벽 설정여부(0 : 미설정, 1 : 설정, 2 : 해지)\n

        Returns
        -------
        str
            info_type에 따른 적절한 값을 반환합니다.
        """
        result = self.dynamicCall('GetLoginInfo(QString)', info_type)
        return result

    def get_condition_load(self) -> int:
        """
        조건검색식을 로드합니다.

        Returns
        -------
        int
            조건검색식 로드에 성공했다면 1을, 아니면 0을 반환합니다.
        """
        result = self.dynamicCall('GetConditionLoad()')
        return result

    def send_condition(self, screen_no: str, condition_name: str, condition_index: int, request_type: int) -> int:
        """
        조건검색식을 보내고 이에 부합하는 종목을 검색합니다.\n
        get_condition_load 함수를 통해 조건검색식이 먼저 로드되어야 합니다.

        Parameters
        ----------
        screen_no : str
            화면번호 입니다.
        condition_name : str
            사용할 조건검색식의 이름입니다.
        condition_index : int
            사용할 조건검색식의 인덱스입니다.
        request_type : int
            0이면 조건검색만 실시하고 1이면 조건 검색과 함께 실시간 조건 검색도 등록됩니다.

        Returns
        -------
        int
            전송에 성공시 1을, 실패시 0을 반환합니다.
        """
        result = self.dynamicCall('SendCondition(QString, Qstring, int, int)', screen_no, condition_name, condition_index, request_type)
        return result

    def set_input_value(self, input_name: str, input_value: str) -> None:
        """
        TR 데이터 조회를 위해 이와 관련된 입력 값을 설정하는 함수입니다.

        Parameters
        ----------
        input_name : str
            입력의 이름입니다.
        input_value : str
            입력의 값입니다.
        """
        self.dynamicCall('SetInputValue(Qstring, Qstring)', input_name, input_value)

    def comm_rq_data(self, request_name: str, tr_code: str, request_type: int, screen_no: str) -> int:
        """
        TR 데이터를 요청합니다.

        Parameters
        ----------
        request_name : str
            요청 이름입니다. unique 해야합니다.
        tr_code : str
            요청할 TR 코드입니다.
        request_type : int
            연속 조회 여부입니다. 처음 조회시 0을, 연속 조회시 2를 전달해주세요.
        screen_no : str
            화면 번호입니다.

        Returns
        -------
        int
            정상적으로 요청되었을 시 0을 반환합니다. 실패했을 경우 그 이외의 값을 반환합니다.
        """
        result = self.dynamicCall('CommRqData(Qstring, Qstring, int, Qstring)', request_name, tr_code, request_type, screen_no)
        return result

    def send_order(self, order_name: str, screen_no: str, account_number: str, order_type: int, 
                   stock_code: str, amount: int, price: int, how: str, original_order_number: str) -> int:
        """
        주문을 전송합니다.

        Parameters
        ----------
        order_name : str
            주문의 이름입니다. unique 해야합니다.
        screen_no : str
            화면번호입니다.
        account_number : str
            계좌 번호입니다.
        order_type : int
            주문의 종류입니다.\n
            1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정\n
        stock_code : str
            주문할 주식의 코드입니다.
        amount : int
            주문 수량입니다.
        price : int
            주문 가격입니다.
        how : str
            거래 구분입니다.\n
            00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 07: 최우선지정가,\n
            10: 지정가IOC, 13: 시장가IOC, 16: 최유리IOC, 20: 지정가FOK, 23: 시장가FOK,\n
            26: 최유리FOK, 61: 장전시간외종가, 62: 시간외단일가매매, 81: 장후시간외종가\n
        original_order_number : str
            원 주문 번호입니다. 취소 혹은 정정시에 사용됩니다. 그 이외의 경우엔 빈 문자열을 전달해주세요.

        Returns
        -------
        int
            주문을 정상적으로 전송했을 시 0을 반환합니다. 실패 시 그 이외의 값을 반환합니다.
        """
    
        params = [order_name, screen_no, account_number, order_type, stock_code, amount, price, how, original_order_number]
        result = self.dynamicCall('SendOrder(Qstring, Qstring, Qstring, int, Qstring, int, int, Qstring, Qstring)', params)
        return result
    
    def set_real_reg(self, screen_no: str, stock_codes: str, fids: str, is_add: str) -> int:
        """
        실시간 정보를 받겠다고 등록하는 함수입니다.

        Parameters
        ----------
        screen_no : str
            화면번호입니다.
        stock_codes : str
            등록할 종목의 코드의 목록입니다. ';'로 구분되어있습니다.
        fids : str
            받을 FID 목록입니다. ';'로 구분되어있습니다.
        is_add : str
            '0'일시 화면번호에 존재하는 기존의 등록은 사라집니다.\n
            '1'일시 기존에 등록된 종목과 함께 실시간 정보를 받습니다. 

        Returns
        -------
        int
            성공적으로 등록되었다면 0을, 그렇지 않다면 그 이외의 값을 반환합니다.
        """
        result = self.dynamicCall('SetRealReg(Qstring, Qstring, Qstring, Qstring)', screen_no, stock_codes, fids, is_add)
        return result

    def get_comm_data(self, tr_code: str, request_name: str, index: int, data_name: str) -> str:
        """
        TR 요청에 따른 데이터를 가져옵니다.
        tr_data_handler에서 호출됩니다.

        Parameters
        ----------
        tr_code : str
            TR 데이터의 코드입니다.
        request_name : str
            요청 이름입니다.
        index : int
            조회할 인덱스입니다. 멀티데이터의 경우, get_repeat_cnt 함수로 데이터의 최대 인덱스를 알 수 있습니다.
        data_name : str
            TR 데이터 중 수신받은 항목입니다.

        Returns
        -------
        str
            수신한 데이터를 반환합니다.
        """
        data = self.dynamicCall('GetCommData(QString, Qstring, int, Qstring)', tr_code, request_name, index, data_name)
        return data
    
    def get_repeat_cnt(self, tr_code: str, tr_name: str) -> int:
        """
        멀티데이터를 다 받기 위해서 가져와야 할 횟수를 반환합니다.\n
        get_comm_data 함수와 같이 사용됩니다.\n
        마찬가지로 tr_data_handler에서 호출됩니다.

        Parameters
        ----------
        tr_code : str
            TR 데이터의 코드입니다.
        data_name : str
            TR 코드의 이름입니다.

        Returns
        -------
        int
            데이터를 가져와야 할 횟수를 반환합니다.
        """
        info_num = self.dynamicCall('GetRepeatCnt(Qstring, Qstring)', tr_code, tr_name)
        return info_num

    def get_condition_name_list(self) -> str:
        """
        로드한 모든 조건검색식의 이름과 인덱스를 가져옵니다.\n
        get_condition_load 함수를 통해 조건검색식이 먼저 로드되어야 합니다.

        Returns
        -------
        str
            '^'과 ';'로 구분된 모든 조건검색식의 이름과 인덱스를 반환합니다.\n
            ex: 조건인덱스1^조건명1;조건인덱스2^조건명2;…;
        """
        condition_list = self.dynamicCall('GetConditionNameList()')
        return condition_list

    def get_chejan_data(self, fid: int) -> str:
        """
        체결 혹은 잔고 관련 데이터를 가져옵니다.
        chejan_data_handler에서 호출됩니다.

        Parameters
        ----------
        fid : int
            가져올 데이터의 FID 값입니다.

        Returns
        -------
        str
            FID와 대응되는 데이터를 반환합니다.
        """
        data = self.dynamicCall('GetChejanData(int)', fid)
        return data

    def get_comm_real_data(self, stock_code: str, fid: int) -> str:
        """
        실시간 데이터를 가져옵니다.
        real_data_handler에서 호출됩니다.

        Parameters
        ----------
        stock_code : str
            실시간 데이터의 종목 코드입니다.
        fid : int
            받아올 항목의 FID 값입니다.

        Returns
        -------
        str
            FID와 대응하는 값을 반환합니다.
        """
        data = self.dynamicCall('GetCommRealData(QString, int)', stock_code, fid)
        return data

        

   