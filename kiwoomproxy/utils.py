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
        logging.debug(f'{func.__name__} starts with args - {args}, kwargs - {kwargs}')
        result = func(*args, **kwargs)
        logging.debug(f'{func.__name__} ends with return value - {result}')
        return result
    return wrapper

_screen_no = 1
def get_screen_no() -> str:
    """
    임의의 적당한 화면번호를 생성하고 반환합니다.
    화면번호는 0001부터 0100까지 순환합니다.

    Returns
    -------
    str
        화면번호를 반환합니다.
    """
    global _screen_no
    screen_no_str = f'{_screen_no:04}'
    _screen_no += 1
    if _screen_no > 100:
        _screen_no = 1
    return screen_no_str

def clean_string(value: str) -> str:
    """
    앞 뒤의 +, -와 공백문자를 제거한 문자열을 반환합니다.

    Parameters
    ----------
    value : str
        기존의 문자열입니다.

    Returns
    -------
    str
        깨끗해진 문자열입니다.
    """
    return value.strip('+- ')

def clean_integer(value: str) -> int | None:
    """
    문자열에서 변환된 정수를 반환합니다.
    부호는 무시합니다.

    Parameters
    ----------
    value : str
        변환될 문자열입니다.

    Returns
    -------
    int | None
        변환된 정수를 반환합니다.
        변환할 수 없다면 None을 반환합니다.
    """
    try:
        clean_value = int(clean_string(value))
    except ValueError:
        clean_value = None
    return clean_value