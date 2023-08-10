from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread
from .market.market_manager import MarketManager
from .analyzer import Analyzer
from .strategies import StrategyFactory

class Manager(QThread):
    """
    자동매매를 총괄하는 중심 클래스
    """

    def run(self):
        
        # market을 초기화합니다.
        market = MarketManager.get_market()
        market.initialize()
        
        # 주식의 universe를 구성합니다.
        stock_universe = ['035720', '005930']
        
        # universe의 모든 종목에 대해 실시간 정보를 받는다고 등록합니다.
        market.register_price_info(stock_universe)
        market.register_ask_bid_info(stock_universe)
        
        # 전략을 수행하는 쓰레드를 만들고 시작합니다.
        
        strategy = StrategyFactory().get_strategy('BuyHoldSell', stock_universe)
        strategy.start()

        # 정보를 수집하고 분석하는 쓰레드를 만들고 시작합니다.
        analyzer = Analyzer(stock_universe)
        analyzer.start()

        # 전략이 끝남과 동시에 정보 수집도 종료합니다.
        strategy.wait()
        analyzer.stop()
        analyzer.wait()

        # 거래 내역을 분석하고 이에 대한 그래프 또한 그립니다.
        analyzer.analyze_transaction()

        # 프로그램을 종료합니다.
        QApplication.quit()

