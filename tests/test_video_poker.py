from core.cards import Card
from game.video_poker import VideoPoker, payout, is_jacks_or_better

def cards(*specs):
    rank_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    result = []
    for s in specs:
        r_str, suit = s[:-1], s[-1]
        rank = rank_map[r_str] if r_str in rank_map else int(r_str)
        result.append(Card(rank, suit))
    return result

def test_royal_flush_pays_800x():
    hand = cards('AS', 'KS', 'QS', 'JS', '10S')
    assert payout(hand, bet=5) == 4000

def test_straight_flush_pays_50x():
    hand = cards('9H', '8H', '7H', '6H', '5H')
    assert payout(hand, bet=1) == 50

def test_four_of_a_kind_pays_25x():
    hand = cards('AS', 'AH', 'AD', 'AC', 'KS')
    assert payout(hand, bet=2) == 50

def test_full_house_pays_9x():
    hand = cards('KS', 'KH', 'KD', 'AS', 'AH')
    assert payout(hand, bet=1) == 9

def test_flush_pays_6x():
    hand = cards('AS', 'KS', 'JS', '8S', '3S')
    assert payout(hand, bet=1) == 6

def test_straight_pays_4x():
    hand = cards('9H', '8S', '7D', '6C', '5H')
    assert payout(hand, bet=1) == 4

def test_three_of_a_kind_pays_3x():
    hand = cards('AS', 'AH', 'AD', 'KS', 'QH')
    assert payout(hand, bet=1) == 3

def test_two_pair_pays_2x():
    hand = cards('AS', 'AH', 'KS', 'KH', 'QD')
    assert payout(hand, bet=1) == 2

def test_pair_jacks_or_better_pays_1x():
    hand = cards('JS', 'JH', 'AS', 'KH', 'QD')
    assert payout(hand, bet=1) == 1

def test_pair_tens_pays_nothing():
    hand = cards('10S', '10H', 'AS', 'KH', 'QD')
    assert payout(hand, bet=1) == 0

def test_high_card_pays_nothing():
    hand = cards('AS', 'KH', 'QD', 'JS', '9C')
    assert payout(hand, bet=1) == 0

def test_jacks_or_better_ace():
    hand = cards('AS', 'AH', '2D', '3C', '4H')
    assert is_jacks_or_better(hand)

def test_not_jacks_or_better_tens():
    hand = cards('10S', '10H', '2D', '3C', '4H')
    assert not is_jacks_or_better(hand)
