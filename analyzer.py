import os
import time
from typing import *
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread

from .market import MarketManager
from .analyzer_const import RECORD_INTERVAL, RESAMPLE_INTERVAL

class Analyzer(QThread):
    """
    Strategy를 통해 이루어진 거래 결과를 분석하는 클래스
    """

    def __init__(self, stock_universe: List[str]):
        """
        정보를 기록할 주식들을 받고 이에 대한 정보를 저장할 dict를 초기화합니다.

        Parameters
        ----------
        stock_universe : List[str]
            Analyzer가 정보를 기록하게 될 모든 주식입니다.
        """
        super().__init__()
        self.is_finished = False
        self.stock_universe = stock_universe
        self.price_history = {}
        self.ask_bid_history = {}
        self.balance_history = {}
        for stock_code in self.stock_universe:              
            self.price_history[stock_code] = {
                'price': [],
                'time': [],
            }
            self.ask_bid_history[stock_code] = {
                'total_ask_amount': [],
                'total_bid_amount': [],
                'time': []
            }
            self.balance_history[stock_code] = {
                'avg_buy_price': [],
                'time': []
            }

    def run(self):
        """
        일정 주기마다 계좌 정보와 strategy에 의해 등록된 실시간 주식 정보를 기록합니다.

        start 메소드에 의해 새로운 쓰레드에서 호출됩니다.
        """
        market = MarketManager.get_market()
        while self.is_finished is False:
            time.sleep(RECORD_INTERVAL)

            # 가격 정보를 기록합니다.
            for stock_code in self.stock_universe:
                price_info = market.get_price_info(stock_code)
                self.price_history[stock_code]['price'].append(price_info['현재가'])
                self.price_history[stock_code]['time'].append(price_info['체결시간'])
                self.balance_history[stock_code]['avg_buy_price'].append(np.NaN)

            # 잔고 정보를 기록합니다.
            balance = market.get_balance()
            for stock_code in balance.keys():
                self.balance_history[stock_code]['avg_buy_price'].append(balance['매입가'])

            # 호가 정보를 기록합니다.
            for stock_code in self.stock_universe:
                ask_bid_info = market.get_ask_bid_info(stock_code)
                bid_sum = 0
                ask_sum = 0
                for price, amount in ask_bid_info['매도호가정보']:
                    ask_sum += price * amount
                for price, amount in ask_bid_info['매수호가정보']:
                    bid_sum += price * amount
                self.ask_bid_history[stock_code]['total_ask_amount'].append(ask_sum)
                self.ask_bid_history[stock_code]['total_bid_amount'].append(bid_sum)
                self.ask_bid_history[stock_code]['time'].append(ask_bid_info['호가시간'])      
                
    def stop(self) -> None:
        """
        정보 수집을 멈춥니다.
        """
        self.is_finished = True
    
    def analyze_transaction(self) -> None:
        """
        잔고 내역과 시장 정보를 가지고 결과를 분석합니다.
        분석 결과는 output 폴더에 그래프로 저장됩니다.
        """
        current_path = os.path.dirname(os.path.abspath(__file__))
        output_dir_path = os.path.join(current_path, 'output')
        if os.path.exists(output_dir_path) is False:
            os.mkdir(output_dir_path)

        for stock_code in self.balance_history.keys():
            # ohlc 데이터프레임을 만듭니다.
            df = pd.DataFrame(self.price_history[stock_code])
            df['time'] = pd.to_datetime(df['time'], format='%H%M%S')
            df.set_index('time', inplace=True)
            ohlc_price = df['price'].resample(RESAMPLE_INTERVAL).ohlc()
            ohlc_price['close'] = ohlc_price['close'].fillna(method='pad')
            ohlc_price['open'] = ohlc_price['open'].fillna(ohlc_price['close'])
            ohlc_price['low'] = ohlc_price['low'].fillna(ohlc_price['close'])
            ohlc_price['high'] = ohlc_price['high'].fillna(ohlc_price['close'])
            ohlc_df = pd.DataFrame({
                'open': ohlc_price['open'],
                'high': ohlc_price['high'],
                'low': ohlc_price['low'],
                'close': ohlc_price['close'],
            })

            # 매수가에 대한 addplot을 만듭니다.
            df = pd.DataFrame(self.balance_history[stock_code])
            df['time'] = pd.to_datetime(df['time'], format='%H%M%S')
            df.set_index('time', inplace=True)
            avg_buy_price = df['avg_buy_price'].resample(RESAMPLE_INTERVAL).first()

            ap = [
                mpf.make_addplot(data=avg_buy_price)
            ]
            output_path = os.path.join(output_dir_path, stock_code + '.png')
            mpf.plot(ohlc_df, addplot=ap, type='candle', style='charles', savefig=output_path)