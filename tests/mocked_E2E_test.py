import sys
import unittest
import types
from .mock_market import MockMarket

mock_module = types.ModuleType('market')
mock_module.Market = MockMarket
sys.modules['kiwoom.src.market.market'] = mock_module

class MockedE2ETest(unittest.TestCase):

    def test_main(self):
        from ..src.__main__ import main
        
if __name__ == '__main__':
    unittest.main()