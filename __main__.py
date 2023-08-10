import signal
import logging

from .market.market_manager import MarketManager
from .manager import Manager

logging.basicConfig(level=logging.INFO)

# Ctrl + C로 프로그램을 강제 종료하기 위해 신호 기본값으로 다시 바꿔줍니다. - 개선 필요
signal.signal(signal.SIGINT, signal.SIG_DFL)

market_manager = MarketManager()
market_manager.create_market()

# 전체 자동매매를 총괄하는 매니저 클래스 생성하고 시작합니다.
manager = Manager()
manager.start()

market_manager.start_signal_handling()