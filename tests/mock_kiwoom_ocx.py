

class MockKiwoomOCX():
    """
    TODO: 일단 클래스를 만들었지만 구현하기는 힘들듯...
    """
    def comm_connect(self) -> int:
        pass

    def get_login_info(self, info_type: str) -> str:
        pass

    def get_condition_load(self) -> int:
        pass

    def send_condition(self, screen_no: str, condition_name: str, condition_index: int, request_type: int) -> int:
        pass

    def set_input_value(self, input_name: str, input_value: str) -> None:
        pass

    def comm_rq_data(self, request_name: str, tr_code: str, request_type: int, screen_no: str) -> int:
        pass

    def send_order(self, order_name: str, screen_no: str, account_number: str, order_type: int, 
                   stock_code: str, amount: int, price: int, how: str, original_order_number: str) -> int:
        pass
    
    def set_real_reg(self, screen_no: str, stock_codes: str, fids: str, is_add: str) -> int:
        pass

    def get_comm_data(self, tr_code: str, request_name: str, index: int, data_name: str) -> str:
        pass
    
    def get_repeat_cnt(self, tr_code: str, tr_name: str) -> int:
        pass

    def get_condition_name_list(self) -> str:
        pass

    def get_chejan_data(self, fid: int) -> str:
        pass

    def get_comm_real_data(self, stock_code: str, fid: int) -> str:
        pass

        

   