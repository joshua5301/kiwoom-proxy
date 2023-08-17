import queue
from PyQt5.QtCore import QWaitCondition

class MarketData():
    """
    KiwoomMarket이 client에게 전송할 데이터를 모아두는 역할을 하는 클래스
    
    ServerSignalHandler는 이 클래스의 객체에 데이터를 저장합니다.
    KiwoomMarket은 이 클래스의 객체에 저장되어있는 데이터를 가져옵니다. 
    즉, 이 클래스는 KiwoomMarket와 ServerSignalHandler 간의 중재자 역할을 합니다.
    """
    
    def __init__(self):
        self.buffer_for_login_result = queue.Queue()
        self.buffer_for_condition_list = queue.Queue()
        self.request_name_to_tr_data = {}
        self.condition_name_to_result = {}

        # 주문 정보 데이터
        # 오직 key-value 값 추가 연산만 이루어집니다.
        self.order_number_to_info = {}
        self.order_info_ready = QWaitCondition()

        # 실시간 데이터
        # 한번 등록을 하면 client의 요청과 관계없이 짧은 주기마다 update됩니다.
        # market이 값을 참조하려면 등록 후 데이터가 존재할 때까지 기다려야 합니다.
        self.price_info = {}
        self.ask_bid_info = {}
        self.balance = {}