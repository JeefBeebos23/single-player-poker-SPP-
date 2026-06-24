import random
from dataclasses import dataclass

SUITS = ['H', 'D', 'C', 'S']
RANKS = list(range(2, 15))  # 2-14, where 14=Ace

_RANK_NAMES = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}

@dataclass
class Card:
    rank: int   # 2-14
    suit: str   # 'H', 'D', 'C', 'S'

    def __repr__(self) -> str:
        return f"{_RANK_NAMES.get(self.rank, str(self.rank))}{self.suit}"

class Deck:
    def __init__(self):
        self.cards: list[Card] = [Card(r, s) for s in SUITS for r in RANKS]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self, n: int) -> list[Card]:
        if n > len(self.cards):
            raise ValueError(f"Not enough cards: need {n}, have {len(self.cards)}")
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt

    def __len__(self) -> int:
        return len(self.cards)
