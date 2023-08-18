import os
import time
import datetime
from typing import *
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
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
        self.start_deposit = market.get_deposit()
        self.start_balance = market.get_balance()
        
        while self.is_finished is False:
            time.sleep(RECORD_INTERVAL)
            os.system('cls')

            # 가격 정보를 기록합니다.
            for stock_code in self.stock_universe:
                price_info = market.get_price_info(stock_code)
                self.price_history[stock_code]['price'].append(price_info['현재가'])
                self.price_history[stock_code]['time'].append(price_info['체결시간'])

            # 잔고 정보를 기록합니다.
            balance = market.get_balance()
            for stock_code in self.stock_universe:
                self.balance_history[stock_code]['time'].append(datetime.datetime.now())
                if stock_code in balance.keys():
                    self.balance_history[stock_code]['avg_buy_price'].append(balance[stock_code]['매입단가'])
                else:
                    self.balance_history[stock_code]['avg_buy_price'].append(np.NaN)

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
                
            # 현재 주식 정보를 터미널에 출력합니다.
            for stock_code in self.stock_universe:
                cur_price = self.price_history[stock_code]['price'][-1]
                avg_buy_price = self.balance_history[stock_code]['avg_buy_price'][-1]
                total_ask_amount = self.ask_bid_history[stock_code]['total_ask_amount'][-1]
                total_bid_amount = self.ask_bid_history[stock_code]['total_bid_amount'][-1]
                print(f'{stock_code} - 현재가: {cur_price}, 매입가: {avg_buy_price}, 매도세: {total_ask_amount}, 매수세: {total_bid_amount}')

        self.final_deposit = market.get_deposit()
        self.final_balance = market.get_balance()
        
    def stop(self) -> None:
        """
        정보 수집을 멈춥니다.
        """
        self.is_finished = True
    
    def analyze_transaction(self) -> None:
        """
        잔고 내역과 시장 정보를 가지고 결과를 분석하고 이를 파일로 저장합니다.
        """
        # 결과를 저장할 파일을 생성합니다.
        current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir_path = os.path.join(current_path, 'output')
        if os.path.exists(output_dir_path) is False:
            os.mkdir(output_dir_path)
        output_dir_path = os.path.join(output_dir_path, datetime.datetime.now().strftime('%y%m%d-%H%M%S'))
        if os.path.exists(output_dir_path) is False:
            os.mkdir(output_dir_path)
            
        # 전체 거래에 대한 텍스트 파일을 생성합니다.
        def evaluate_total_asset_value(balance: dict, deposit: int) -> int:
            total_asset_value = deposit
            for stock_code in balance.keys():
                total_asset_value += balance[stock_code]['수량'] * balance[stock_code]['현재가']
            return total_asset_value
        output_txt_path = os.path.join(output_dir_path, 'result.txt')
        with open(output_txt_path, 'w') as file:
            file.write(f'시작 주문가능금액: {self.start_deposit}원\n')
            file.write(f'시작 보유주식: {self.start_balance}\n')
            start_asset_value = evaluate_total_asset_value(self.start_balance, self.start_deposit)
            file.write(f'시작 자산가치: {start_asset_value}원\n\n')
            file.write(f'종료 주문가능금액 : {self.final_deposit}원\n')
            file.write(f'종료 보유주식: {self.final_balance}\n')
            final_asset_value = evaluate_total_asset_value(self.final_balance, self.final_deposit)
            file.write(f'종료 자산가치: {final_asset_value}원\n\n')
            total_profit_percentage = (final_asset_value / start_asset_value - 1) * 100
            file.write(f'수익률 : {total_profit_percentage:.2f}%\n')

        # 각 종목마다 ohlc 그래프를 그리고 저장합니다.
        for stock_code in self.balance_history.keys():
            
            # 현재가에 대한 ohlc 데이터프레임을 만듭니다.
            price_df = pd.DataFrame(self.price_history[stock_code])
            price_df.set_index('time', inplace=True)
            
            # 리샘플링 후 간격마다 누락된 데이터를 채워넣습니다.
            ohlc_df = price_df['price'].resample(RESAMPLE_INTERVAL).ohlc()
            ohlc_df['close'] = ohlc_df['close'].fillna(method='ffill')
            ohlc_df['open'] = ohlc_df['open'].fillna(ohlc_df['close'])
            ohlc_df['low'] = ohlc_df['low'].fillna(ohlc_df['close'])
            ohlc_df['high'] = ohlc_df['high'].fillna(ohlc_df['close'])
            
            # open 열의 경우, close 열의 이전 값으로 변경해줍니다.
            ohlc_df['open'].iloc[1:] = ohlc_df['close'].shift(1).iloc[1:]

            # 매수가에 대한 addplot을 만듭니다.
            avg_price_df = pd.DataFrame(self.balance_history[stock_code])
            avg_price_df.set_index('time', inplace=True)
            avg_price_df = avg_price_df['avg_buy_price'].resample(RESAMPLE_INTERVAL).first()
            
            # 호가정보에 대한 addplot을 만듭니다.
            ask_bid_df = pd.DataFrame(self.ask_bid_history[stock_code])
            ask_bid_df.set_index('time', inplace=True)
            ask_df = ask_bid_df['total_ask_amount'].resample(RESAMPLE_INTERVAL).first()
            bid_df = -ask_bid_df['total_bid_amount'].resample(RESAMPLE_INTERVAL).first()
            
            # 각 데이터프레임의 길이를 동일하게 맞춰줍니다.
            min_len = min(len(ohlc_df), len(avg_price_df), len(ask_df), len(bid_df))
            ohlc_df = ohlc_df.iloc[:min_len]
            avg_price_df = avg_price_df.iloc[:min_len]
            ask_df = ask_df.iloc[:min_len]
            bid_df = bid_df.iloc[:min_len]
            
            # 메인 데이터프레임과 addplot들을 plot하고 이를 저장합니다.
            market_colors = mpf.make_marketcolors(up='#E71809', down='#115BCB', inherit=True)
            kiwoom_style = mpf.make_mpf_style(marketcolors=market_colors, gridstyle='-', gridcolor='#D8D8D8', gridaxis='horizontal')
            ap = [
                mpf.make_addplot(data=avg_price_df, panel=0, secondary_y=False, type='line', color='black'),
                mpf.make_addplot(data=ask_df, panel=1, secondary_y=False, type='bar', color='#115BCB'),
                mpf.make_addplot(data=bid_df, panel=1, secondary_y=False, type='bar', color='#E71809')
            ]
            output_graph_path = os.path.join(output_dir_path, stock_code + '.png')
            mpf.plot(ohlc_df, addplot=ap, type='candle', figratio=(18,10), tight_layout=True, 
                     datetime_format='%HH %MM %SS', style=kiwoom_style, savefig=output_graph_path)
            
        # 분석 결과가 저장된 폴더 창을 띄웁니다.
        os.system(f'start "" "{output_dir_path}"')