import re

MASK_PATTERN = re.compile(r'^\*{3}.{4}$')


def is_secrecy_key(key: str) -> bool:
    return bool(MASK_PATTERN.match(key))


def secrecy_key(key: str) -> str:
    return '***' + key[-4:] if len(key) > 4 else '***'
