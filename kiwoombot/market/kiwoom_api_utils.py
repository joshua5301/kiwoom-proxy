import datetime

class KiwoomAPIUtils():
    """
    키움증권 API를 호출할 때 필요한 값들을 생성해주는 클래스입니다.

    screen_no와 request_name 혹은 order_name을 생성해주는 스태틱 메서드가 존재합니다.
    """
    screen_no = 1
    @staticmethod
    def get_screen_no() -> str:
        """
        임의의 적당한 화면번호를 생성하고 반환합니다.

        Returns
        -------
        str
            화면번호를 반환합니다.
        """
        screen_no_str = f'{KiwoomAPIUtils.screen_no:04}'
        KiwoomAPIUtils.screen_no += 1
        if KiwoomAPIUtils.screen_no > 100:
            KiwoomAPIUtils.screen_no = 1
        return screen_no_str
    
    request_name_no = 0
    @staticmethod
    def create_request_name(name: str) -> str:
        """
        unique한 임의의 request_name을 만들고 반환합니다.

        Parameters
        ----------
        name : str
            request_name을 만들때 앞에 포함되는 문자열입니다.
            이는 unique하지 않아도 됩니다.

        Returns
        -------
        str
            request_name을 반환합니다.
        """
        request_name_no_str = f'{KiwoomAPIUtils.request_name_no:06}'
        KiwoomAPIUtils.request_name_no += 1
        if KiwoomAPIUtils.request_name_no >= 1000000:
            raise RuntimeError('너무 많은 이름이 생성돼 더 이상 unique 해질 수 없습니다.')
        request_name = name + '-' + request_name_no_str
        return request_name