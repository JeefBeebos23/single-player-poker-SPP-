import random
from ai.personality import Personality

_ACTIONS = ['fold', 'check', 'call', 'raise', 'all_in']


def decide(hand_strength: float, pot_odds: float, phase: str,
           difficulty: int, personality: Personality) -> str:
    """
    Return a poker action string for an AI bot.

    hand_strength: 0.0 (worst) to 1.0 (best)
    pot_odds:      fraction of pot needed to call (0.0 = free, 1.0 = very expensive)
    phase:         'pre_flop', 'post_flop', 'draw', 'showdown'
    difficulty:    0=Easy, 1=Normal, 2=Hard
    personality:   Personality instance
    """
    weights = _base_weights(hand_strength, pot_odds, difficulty)
    weights = _apply_personality(weights, personality)
    return random.choices(_ACTIONS, weights=weights, k=1)[0]


def _base_weights(hs: float, po: float, difficulty: int) -> list[float]:
    """
    Returns [fold, check, call, raise, all_in] weights before personality.
    Higher hand_strength → less fold, more raise/all_in.
    Higher pot_odds → more fold for weak hands.
    """
    fold_w  = max(0, (0.5 - hs) * 2) * (0.5 + po * 0.5)
    check_w = max(0, 0.4 - abs(hs - 0.4))
    call_w  = max(0, 1.0 - abs(hs - 0.5) * 2)
    raise_w = max(0, hs - 0.3) * 1.5
    allin_w = max(0, hs - 0.7) * 1.0

    if difficulty == 0:
        weights = [fold_w * 0.5, check_w * 1.5, call_w * 1.8, raise_w * 0.6, allin_w * 0.4]
    elif difficulty == 2:
        weights = [fold_w * 1.5, check_w * 0.7, call_w * 0.9, raise_w * 1.4, allin_w * 1.3]
    else:
        weights = [fold_w, check_w, call_w, raise_w, allin_w]

    return [max(0.05, w) for w in weights]


def _apply_personality(weights: list[float], p: Personality) -> list[float]:
    """Nudge weights based on loose/tight and aggressive/passive traits."""
    fold_i, check_i, call_i, raise_i, allin_i = 0, 1, 2, 3, 4

    weights[fold_i]  *= (1.0 - p.loose_tight * 0.5)
    weights[call_i]  *= (0.5 + p.loose_tight)
    weights[check_i] *= (1.0 - p.aggressive_passive * 0.5)
    weights[raise_i] *= (0.5 + p.aggressive_passive)
    weights[allin_i] *= (0.5 + p.aggressive_passive * 0.7)

    return weights
