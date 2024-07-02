from .mock_market import MockMarket

class MockMarketManager():
    
    def create_market(self) -> None:
        pass
    
    @staticmethod
    def get_market() -> MockMarket:
        return MockMarket('dummy', 'dummy')