import json
import os
import sys

def _default_save_dir() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'save')

_SAVE_DIR = _default_save_dir()
STARTING_BALANCE = 1000

def _path() -> str:
    return os.path.join(_SAVE_DIR, 'bankroll.json')

def load() -> int:
    p = _path()
    if not os.path.exists(p):
        return STARTING_BALANCE
    with open(p) as f:
        return json.load(f)['balance']

def save(balance: int) -> None:
    os.makedirs(_SAVE_DIR, exist_ok=True)
    with open(_path(), 'w') as f:
        json.dump({'balance': balance}, f)

def reset() -> int:
    save(STARTING_BALANCE)
    return STARTING_BALANCE
