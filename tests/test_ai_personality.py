import pytest
from ai.personality import generate_opponents, Personality

def test_generates_correct_count():
    ops = generate_opponents(3, difficulty=1)
    assert len(ops) == 3

def test_returns_personality_instances():
    ops = generate_opponents(2, difficulty=1)
    assert all(isinstance(p, Personality) for p in ops)

def test_names_are_unique():
    ops = generate_opponents(4, difficulty=1)
    names = [p.name for p in ops]
    assert len(names) == len(set(names))

def test_values_in_range():
    for diff in [0, 1, 2]:
        for p in generate_opponents(3, diff):
            assert 0.0 <= p.loose_tight <= 1.0
            assert 0.0 <= p.aggressive_passive <= 1.0
            assert 0.0 <= p.talk_frequency <= 1.0

def test_easy_tends_loose():
    """Easy bots average loose_tight > 0.5 over many samples."""
    ops = generate_opponents(100, difficulty=0)
    avg = sum(p.loose_tight for p in ops) / len(ops)
    assert avg > 0.5

def test_hard_tends_tight():
    """Hard bots average loose_tight < 0.5 over many samples."""
    ops = generate_opponents(100, difficulty=2)
    avg = sum(p.loose_tight for p in ops) / len(ops)
    assert avg < 0.5

def test_hard_tends_aggressive():
    """Hard bots average aggressive_passive > 0.5 over many samples."""
    ops = generate_opponents(100, difficulty=2)
    avg = sum(p.aggressive_passive for p in ops) / len(ops)
    assert avg > 0.5

def test_name_is_string():
    ops = generate_opponents(1, difficulty=1)
    assert isinstance(ops[0].name, str) and len(ops[0].name) > 0
