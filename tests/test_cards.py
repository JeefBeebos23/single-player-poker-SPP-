import pytest
from core.cards import Card, Deck, SUITS, RANKS

def test_card_repr():
    assert repr(Card(14, 'S')) == 'AS'
    assert repr(Card(11, 'H')) == 'JH'
    assert repr(Card(7, 'D')) == '7D'

def test_deck_has_52_cards():
    deck = Deck()
    assert len(deck) == 52

def test_deck_has_all_combinations():
    deck = Deck()
    pairs = {(c.rank, c.suit) for c in deck.cards}
    assert len(pairs) == 52

def test_deck_deal_removes_cards():
    deck = Deck()
    hand = deck.deal(5)
    assert len(hand) == 5
    assert len(deck) == 47

def test_deck_deal_raises_when_empty():
    deck = Deck()
    deck.deal(52)
    with pytest.raises(ValueError):
        deck.deal(1)

def test_deck_shuffle_changes_order():
    import random
    random.seed(42)
    deck1 = Deck()
    order_before = [repr(c) for c in deck1.cards]
    deck1.shuffle()
    order_after = [repr(c) for c in deck1.cards]
    assert order_before != order_after
