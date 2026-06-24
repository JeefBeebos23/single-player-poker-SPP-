import pytest
from ai.personality import Personality
from ai.engine import decide

_VALID = {'fold', 'check', 'call', 'raise', 'all_in'}

def _p(lt=0.5, ap=0.5, freq=0.5):
    return Personality('Test Bot', lt, ap, freq)

def test_returns_valid_action():
    action = decide(0.5, 0.3, 'post_flop', 1, _p())
    assert action in _VALID

def test_all_difficulties_return_valid():
    for d in [0, 1, 2]:
        assert decide(0.5, 0.3, 'post_flop', d, _p()) in _VALID

def test_all_phases_return_valid():
    for phase in ['pre_flop', 'post_flop', 'draw', 'showdown']:
        assert decide(0.5, 0.3, phase, 1, _p()) in _VALID

def test_strong_hand_rarely_folds_on_hard():
    """With hs=1.0 on Hard, fold should be very rare over 200 trials."""
    folds = sum(1 for _ in range(200) if decide(1.0, 0.1, 'post_flop', 2, _p(lt=0.3, ap=0.8)) == 'fold')
    assert folds < 30

def test_weak_hand_rarely_raises_on_hard():
    """With hs=0.0 on Hard, raise/all_in should be rare."""
    aggressive = sum(1 for _ in range(200)
                     if decide(0.0, 0.5, 'post_flop', 2, _p(lt=0.3, ap=0.5)) in {'raise', 'all_in'})
    assert aggressive < 60

def test_easy_calls_more_than_hard_with_weak_hand():
    """Easy AI calls more with weak hands than Hard AI."""
    easy_calls = sum(1 for _ in range(200) if decide(0.2, 0.3, 'post_flop', 0, _p()) in {'call', 'check'})
    hard_calls = sum(1 for _ in range(200) if decide(0.2, 0.3, 'post_flop', 2, _p()) in {'call', 'check'})
    assert easy_calls > hard_calls

def test_loose_personality_folds_less_than_tight():
    loose = _p(lt=0.9, ap=0.5)
    tight = _p(lt=0.1, ap=0.5)
    loose_folds = sum(1 for _ in range(200) if decide(0.3, 0.4, 'post_flop', 1, loose) == 'fold')
    tight_folds = sum(1 for _ in range(200) if decide(0.3, 0.4, 'post_flop', 1, tight) == 'fold')
    assert loose_folds < tight_folds

def test_aggressive_personality_raises_more_than_passive():
    agg = _p(lt=0.5, ap=0.9)
    pas = _p(lt=0.5, ap=0.1)
    agg_raises = sum(1 for _ in range(200) if decide(0.6, 0.3, 'post_flop', 1, agg) in {'raise', 'all_in'})
    pas_raises = sum(1 for _ in range(200) if decide(0.6, 0.3, 'post_flop', 1, pas) in {'raise', 'all_in'})
    assert agg_raises > pas_raises

def test_extreme_hand_strength_boundaries():
    assert decide(0.0, 1.0, 'post_flop', 1, _p()) in _VALID
    assert decide(1.0, 0.0, 'post_flop', 1, _p()) in _VALID

def test_deterministic_with_seed():
    import random
    random.seed(42)
    a = decide(0.6, 0.2, 'post_flop', 1, _p())
    random.seed(42)
    b = decide(0.6, 0.2, 'post_flop', 1, _p())
    assert a == b
