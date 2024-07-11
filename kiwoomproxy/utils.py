import datetime
import logging
from typing import Callable

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
        logging.debug(f'At {datetime.datetime.now()}:')
        logging.debug(f'    {func.__name__} starts with args - {args}, kwargs - {kwargs}')
        result = func(*args, **kwargs)
        logging.debug(f'At {datetime.datetime.now()}:')
        logging.debug(f'    {func.__name__} ends with return value - {result}')
        return result
    return wrapper

screen_no = 1
def get_screen_no() -> str:
    """
    임의의 적당한 화면번호를 생성하고 반환합니다.

    Returns
    -------
    str
        화면번호를 반환합니다.
    """
    global screen_no
    screen_no_str = f'{screen_no:04}'
    screen_no += 1
    if screen_no > 100:
        screen_no = 1
    return screen_no_str