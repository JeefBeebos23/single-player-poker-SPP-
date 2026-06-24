from core.cards import Card
from core.hand_evaluator import best_hand, ROYAL_FLUSH, FLUSH, TWO_PAIR

def cards(*specs):
    rank_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    result = []
    for s in specs:
        r_str, suit = s[:-1], s[-1]
        rank = rank_map[r_str] if r_str in rank_map else int(r_str)
        result.append(Card(rank, suit))
    return result

def test_best_hand_5_cards_same_as_evaluate():
    hand = cards('AS', 'KS', 'QS', 'JS', '10S')
    rank, tb = best_hand(hand)
    assert rank == ROYAL_FLUSH

def test_finds_royal_flush_in_7_cards():
    hand = cards('AS', 'KS', 'QS', 'JS', '10S', '2H', '3D')
    rank, _ = best_hand(hand)
    assert rank == ROYAL_FLUSH

def test_finds_flush_over_three_of_a_kind():
    # 5 hearts make a flush (rank 5); three 2s make three-of-a-kind (rank 3)
    # FLUSH > THREE_OF_A_KIND so best_hand picks flush
    hand = cards('AH', 'KH', '9H', '5H', '2H', '2S', '2D')
    rank, _ = best_hand(hand)
    assert rank == FLUSH

def test_picks_two_pair_from_7_cards():
    # Aces and Kings with 5 other cards — best 5-card hand is two-pair
    hand = cards('AS', 'AH', 'KS', 'KH', '2D', '3C', '4H')
    rank, _ = best_hand(hand)
    assert rank == TWO_PAIR

def test_best_hand_returns_tuple():
    hand = cards('AS', 'KH', 'QD', 'JS', '9C', '2H', '3D')
    result = best_hand(hand)
    assert isinstance(result, tuple) and len(result) == 2
