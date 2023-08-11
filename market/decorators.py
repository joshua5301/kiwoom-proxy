import logging
import time
import datetime
import threading
from PyQt5.QtCore import QThread, QMutex, QMutexLocker
from typing import *

def trace(func: Callable) -> Callable:
    """
    함수의 시작과 끝을 trace하는 decorator 입니다.
    log level은 DEBUG입니다.

    Parameters
    ----------
    func : Callable
        trace 당할 함수입니다.

    Returns
    -------
    Callable
        시작과 끝을 logging하는 함수를 반환합니다.
    """
    def wrapper(*args, **kwargs):
        logging.debug(f'{threading.current_thread().name} at {datetime.datetime.now()}:')
        logging.debug(f'    {func.__name__} starts with args - {args}, kwargs - {kwargs}')
        result = func(*args, **kwargs)
        logging.debug(f'{threading.current_thread().name} at {datetime.datetime.now()}:')
        logging.debug(f'    {func.__name__} ends with return value - {result}')
        return result
    return wrapper

_request_api_num_per_second = 0
def request_api_method(func: Callable) -> Callable:
    """ 
    키움증권 데이터 조회 요청을 하는 함수는 이 decorator를 사용함으로써 
    과도한 조회로 인한 조회 실패를 방지해야합니다.

    Parameters
    ----------
    func : Callable
        조회를 요청하는 함수입니다.

    Returns
    -------
    Callable
        최근에 호출한 조회 API 횟수에 따라 잠깐 기다리는 closure를 반환합니다.
    """
    
    lock = QMutex()
    def wrapper(*args, **kwargs):
        
        # 만약 1초 내로 요청이 5번 이상 왔다면 1초 기다립니다.
        global _request_api_num_per_second
        with QMutexLocker(lock):
            if _request_api_num_per_second >= 5:
                time.sleep(1)
            _request_api_num_per_second += 1
            
        result = func(*args, **kwargs)
        return result
    return wrapper

_order_api_num_per_second = 0
def order_api_method(func: Callable) -> Callable:
    """
    키움증권 주문 요청하는 함수는 이 decorator를 사용함으로써 
    과도한 주문으로 인한 주문 실패를 방지해야합니다.

    Parameters
    ----------
    func : Callable
        주문을 요청하는 함수입니다.

    Returns
    -------
    Callable
        최근에 호출한 주문 API 횟수에 따라 잠깐 기다리는 closure를 반환합니다.
    """
    lock = QMutex()
    def wrapper(*args, **kwargs):
        
        # 만약 1초 내로 요청이 5번 이상 왔다면 1초 기다립니다.
        global _order_api_num_per_second
        with QMutexLocker(lock):
            if _order_api_num_per_second >= 5:
                time.sleep(1)
            _order_api_num_per_second += 1
            
        result = func(*args, **kwargs)
        return result
    return wrapper

class _APICallCountResetter(QThread):
    """
    API 호출 횟수를 1초마다 초기화해주는 클래스입니다.
    """
    def run(self):
        global _order_api_num_per_second
        global _request_api_num_per_second
        while True:
            time.sleep(1)
            _order_api_num_per_second = 0
            _request_api_num_per_second = 0
            
resetter = _APICallCountResetter()
resetter.start()
            