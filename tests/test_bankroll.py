import os
import pytest
import core.bankroll as bankroll

@pytest.fixture(autouse=True)
def tmp_save(tmp_path, monkeypatch):
    """Redirect save path to a temp dir for each test."""
    monkeypatch.setattr(bankroll, '_SAVE_DIR', str(tmp_path))

def test_load_returns_starting_balance_when_no_file():
    assert bankroll.load() == bankroll.STARTING_BALANCE

def test_save_and_load_roundtrip():
    bankroll.save(2500)
    assert bankroll.load() == 2500

def test_reset_returns_starting_balance():
    bankroll.save(100)
    result = bankroll.reset()
    assert result == bankroll.STARTING_BALANCE
    assert bankroll.load() == bankroll.STARTING_BALANCE

def test_save_creates_directory(tmp_path, monkeypatch):
    nested = str(tmp_path / 'a' / 'b')
    monkeypatch.setattr(bankroll, '_SAVE_DIR', nested)
    bankroll.save(500)
    assert bankroll.load() == 500
