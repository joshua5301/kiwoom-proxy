import queue

class MarketData():
    """
    Market이 client에게 전송할 데이터를 모아두는 역할을 하는 클래스
    
    ServerSignalHandler는 이 클래스의 객체에 데이터를 저장합니다.
    Market은 이 클래스의 객체에 저장되어있는 데이터를 가져옵니다. 
    즉, 이 클래스는 Market과 ServerSignalHandler 간의 중재자 역할을 합니다.
    """
    
    def __init__(self):
        """
        몇몇 자료구조로 queue.Queue를 사용하는 것은 Market과 ServerSignalHandler 간의 동기화 때문입니다.
        다시 말해, Market이 데이터가 존재할 때까지 기다리도록 하기 위함입니다.
        """

        # login_handler가 로그인 결과를 저장하는 queue입니다.
        self.login_result = queue.Queue(maxsize=1)

        # condition_result_handler가 condition의 이름 리스트를 저장하는 queue입니다.
        self.condition_list = queue.Queue(maxsize=1)

        # queue들의 dict입니다.
        # tr_data_handler가 요청의 이름을 key로 하여 TR 데이터를 enqueue합니다.
        self.request_name_to_tr_data = {}

        # queue들의 dict입니다.
        # condition_search_result_handler가 조건검색식의 이름을 key로 하여 조건검색 결과를 enqueue합니다.
        self.condition_name_to_result = {}

        # 잔고 정보입니다. 
        # tr_data_handler에 의해 초기화되고 이후부턴 chejan handler에서 update가 이루어집니다.
        self.balance = {}

        # 체결에 전부 이뤄졌을 때 chejan_handler에서 주문 번호를 key로 하여 주문 정보를 저장합니다.
        self.order_number_to_info = {}

        # 실시간 데이터로, Market이 한번 등록을 하면 짧은 주기마다 정보가 update됩니다.
        # 등록 직후에는 데이터가 없을 수도 있습니다.
        self.price_info = {}
        self.ask_bid_info = {}
        