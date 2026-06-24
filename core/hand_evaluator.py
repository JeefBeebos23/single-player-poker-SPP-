from collections import Counter
from itertools import combinations as _combinations
from core.cards import Card

HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9

HAND_NAMES = {
    0: 'High Card', 1: 'One Pair', 2: 'Two Pair',
    3: 'Three of a Kind', 4: 'Straight', 5: 'Flush',
    6: 'Full House', 7: 'Four of a Kind',
    8: 'Straight Flush', 9: 'Royal Flush',
}

def _check_straight(ranks: list[int]) -> tuple[bool, tuple]:
    """Returns (is_straight, rank_tuple_for_tiebreak)."""
    if len(set(ranks)) == 5:
        if ranks[0] - ranks[4] == 4:
            return True, tuple(ranks)
        if set(ranks) == {14, 2, 3, 4, 5}:  # wheel: A-2-3-4-5
            return True, (5, 4, 3, 2, 1)
    return False, tuple(ranks)

def evaluate(cards: list[Card]) -> tuple[int, tuple]:
    """
    Evaluate a 5-card poker hand.
    Returns (hand_rank, tiebreaker_tuple) — compare directly; higher tuple wins.
    """
    ranks = sorted([c.rank for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    counts = Counter(ranks)
    freq = sorted(counts.values(), reverse=True)

    is_flush = len(set(suits)) == 1
    is_straight, straight_ranks = _check_straight(ranks)

    sorted_ranks = tuple(sorted(ranks, key=lambda r: (counts[r], r), reverse=True))

    if is_straight and is_flush:
        if straight_ranks[0] == 14:
            return (ROYAL_FLUSH, straight_ranks)
        return (STRAIGHT_FLUSH, straight_ranks)
    if freq[0] == 4:
        return (FOUR_OF_A_KIND, sorted_ranks)
    if freq[:2] == [3, 2]:
        return (FULL_HOUSE, sorted_ranks)
    if is_flush:
        return (FLUSH, tuple(ranks))
    if is_straight:
        return (STRAIGHT, straight_ranks)
    if freq[0] == 3:
        return (THREE_OF_A_KIND, sorted_ranks)
    if freq[:2] == [2, 2]:
        return (TWO_PAIR, sorted_ranks)
    if freq[0] == 2:
        return (ONE_PAIR, sorted_ranks)
    return (HIGH_CARD, tuple(ranks))

def best_hand(cards: list[Card]) -> tuple[int, tuple]:
    """Return the best evaluate() result from all 5-card combos in cards (min 5 cards)."""
    if len(cards) == 5:
        return evaluate(cards)
    best = None
    for combo in _combinations(cards, 5):
        result = evaluate(list(combo))
        if best is None or result > best:
            best = result
    return best
