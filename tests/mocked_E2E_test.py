import sys
import types

from unittest import main, TestCase
from .mock_market_manager import MockMarketManager

mock_module = types.ModuleType('mock')
mock_module.MarketManager = MockMarketManager
sys.modules['kiwoombot.market.market_manager'] = mock_module
class MockedE2ETest(TestCase):

    def test_main(self):
        from kiwoombot.start import start
        start()

if __name__ == '__main__':
    main()