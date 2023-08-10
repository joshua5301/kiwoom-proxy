from PyQt5.QtCore import QThread

class Strategy(QThread):
    """
    모든 strategy의 base class
    """
    def __init__(self, stock_universe: list[str]):
        super().__init__()
        self.stock_universe = stock_universe
    
    def run(self):
        pass