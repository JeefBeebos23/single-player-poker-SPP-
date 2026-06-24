from core.cards import Card
from core.hand_evaluator import (
    evaluate, ROYAL_FLUSH, STRAIGHT_FLUSH, FOUR_OF_A_KIND,
    FULL_HOUSE, FLUSH, STRAIGHT, THREE_OF_A_KIND, TWO_PAIR,
    ONE_PAIR, HIGH_CARD, HAND_NAMES
)

def cards(*specs):
    """Build cards from ('AS', 'KH', ...) notation."""
    rank_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    result = []
    for s in specs:
        r_str, suit = s[:-1], s[-1]
        rank = rank_map[r_str] if r_str in rank_map else int(r_str)
        result.append(Card(rank, suit))
    return result

def test_royal_flush():
    hand = cards('AS', 'KS', 'QS', 'JS', '10S')
    rank, _ = evaluate(hand)
    assert rank == ROYAL_FLUSH

def test_straight_flush():
    hand = cards('9H', '8H', '7H', '6H', '5H')
    rank, _ = evaluate(hand)
    assert rank == STRAIGHT_FLUSH

def test_four_of_a_kind():
    hand = cards('AS', 'AH', 'AD', 'AC', 'KS')
    rank, _ = evaluate(hand)
    assert rank == FOUR_OF_A_KIND

def test_full_house():
    hand = cards('KS', 'KH', 'KD', 'AS', 'AH')
    rank, _ = evaluate(hand)
    assert rank == FULL_HOUSE

def test_flush():
    hand = cards('AS', 'KS', 'JS', '8S', '3S')
    rank, _ = evaluate(hand)
    assert rank == FLUSH

def test_straight():
    hand = cards('9H', '8S', '7D', '6C', '5H')
    rank, _ = evaluate(hand)
    assert rank == STRAIGHT

def test_wheel_straight():
    hand = cards('AS', '2H', '3D', '4C', '5S')
    rank, _ = evaluate(hand)
    assert rank == STRAIGHT

def test_three_of_a_kind():
    hand = cards('AS', 'AH', 'AD', 'KS', 'QH')
    rank, _ = evaluate(hand)
    assert rank == THREE_OF_A_KIND

def test_two_pair():
    hand = cards('AS', 'AH', 'KS', 'KH', 'QD')
    rank, _ = evaluate(hand)
    assert rank == TWO_PAIR

def test_one_pair():
    hand = cards('AS', 'AH', 'KS', 'QH', 'JD')
    rank, _ = evaluate(hand)
    assert rank == ONE_PAIR

def test_high_card():
    hand = cards('AS', 'KH', 'QD', 'JS', '9C')
    rank, _ = evaluate(hand)
    assert rank == HIGH_CARD

def test_higher_hand_beats_lower():
    flush = cards('AS', 'KS', 'JS', '8S', '3S')
    straight = cards('9H', '8S', '7D', '6C', '5H')
    assert evaluate(flush) > evaluate(straight)

def test_hand_names_complete():
    for rank in range(10):
        assert rank in HAND_NAMES
