import re

MASK_PATTERN = re.compile(r'^\*{3}.{4}$')


def is_secrecy_value(value: str) -> bool:
    return bool(MASK_PATTERN.match(value))


def secrecy_value(value: str) -> str:
    return '***' + value[-4:] if len(value) > 4 else '***'
