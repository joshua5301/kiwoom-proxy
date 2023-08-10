import logging
from PyQt5.QtWidgets import QApplication

from .market_data import MarketData
from .kiwoom_ocx import KiwoomOCX
from .client_signal_handler import ClientSignalHandler
from .server_signal_handler import ServerSignalHandler
from .market import Market

logger = logging.getLogger(__name__)

class MarketManager():
    """
    KiwoomMarket 객체를 관리하는 클래스입니다.
    """

    _market = None
    def create_market(self) -> None:
        """
        KiwoomMarket 객체를 생성 후 클래스 변수로 저장합니다.
        반드시 main thread에서 호출되어야 합니다.
        """
        if MarketManager._market is not None:
            logger.error('!!! KiwoomMarket 객체는 한번만 생성되어야 합니다. !!!')
            return
        self._app = QApplication([])
        self._data = MarketData()
        self._ocx = KiwoomOCX()
        self._client_signal_handler = ClientSignalHandler(self._ocx, self._data)
        self._server_signal_handler = ServerSignalHandler(self._ocx, self._data)
        MarketManager._market = Market(self._client_signal_handler, self._data)
    
    @staticmethod
    def get_market() -> Market:
        """
        KiwoomMarket의 유일한 객체를 반환합니다.

        Returns
        -------
        KiwoomMarket
            클래스의 유일한 객체를 반환합니다.
        """
        if MarketManager._market is None:
            logger.error('!!! KiwoomMarket 객체가 아직 생성되지 않았습니다. !!!')
            return
        return MarketManager._market
    
    _is_started = False
    def start_signal_handling(self) -> None:
        """
        pyqt5 메인 이벤트 루프를 시작합니다.
        이 이벤트 루프는 키움증권 서버에서 온 signal을 계속 처리하면서 KiwoomMarket이 동작하게끔 합니다.
        반드시 main thread에서 호출되어야 합니다.
        """
        if MarketManager._is_started is True:
            logger.error('!!! KiwoomMarket 객체는 한번만 시작되어야 합니다. !!!')
            return
        MarketManager._is_started = True
        self._app.exec()