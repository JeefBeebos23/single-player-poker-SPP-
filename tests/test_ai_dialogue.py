import pytest
from ai.personality import Personality
from ai.dialogue import get_line, all_triggers

def _p(freq):
    return Personality('T', 0.5, 0.5, freq)

def test_silent_when_freq_zero():
    """talk_frequency=0 → always returns None."""
    for trigger in all_triggers():
        for diff in [0, 1, 2]:
            assert get_line(trigger, diff, _p(0.0)) is None

def test_speaks_when_freq_one():
    """talk_frequency=1 → always returns a string."""
    for trigger in all_triggers():
        for diff in [0, 1, 2]:
            result = get_line(trigger, diff, _p(1.0))
            assert isinstance(result, str) and len(result) > 0

def test_unknown_trigger_returns_none():
    assert get_line('nonexistent_trigger', 1, _p(1.0)) is None

def test_all_difficulties_have_lines():
    for trigger in all_triggers():
        for diff in [0, 1, 2]:
            result = get_line(trigger, diff, _p(1.0))
            assert result is not None

def test_returns_string_or_none():
    result = get_line('win_pot', 1, _p(0.5))
    assert result is None or isinstance(result, str)

def test_all_triggers_returns_list():
    triggers = all_triggers()
    assert isinstance(triggers, list) and len(triggers) >= 7
