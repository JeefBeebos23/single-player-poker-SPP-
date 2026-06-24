# Foundation + Video Poker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete project skeleton, all shared core systems, the Pygame window + main menu, and a fully playable Video Poker mode — leaving clean stubs for all remaining game modules.

**Architecture:** A central `main.py` runs the top-level loop and delegates to a `Menu` class for navigation and individual game classes (each with a `.run() -> int` method that returns the updated balance). All game modules share `core/` (cards, hand evaluator, bankroll, modifiers). The menu handles mode selection and difficulty; each game module is self-contained.

**Tech Stack:** Python 3.11+, pygame 2.5.2, pytest — install via `pip install pygame==2.5.2 pytest`

---

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | Pinned dependencies |
| `.gitignore` | Exclude save/, dist/, build/__pycache__ |
| `main.py` | Entry point, top-level game loop, state routing |
| `menu.py` | Main menu screen — mode buttons, difficulty slider, balance display |
| `core/__init__.py` | Empty |
| `core/cards.py` | `Card` dataclass, `Deck` class |
| `core/hand_evaluator.py` | `evaluate(cards) -> (rank_int, tiebreaker_tuple)`, hand name constants |
| `core/bankroll.py` | `load()`, `save(balance)`, `reset()` — JSON persistence |
| `core/modifiers.py` | `ModifierSet` dataclass — empty stub, all fields False/0 |
| `game/__init__.py` | Empty |
| `game/video_poker.py` | `VideoPoker` class — full Jacks-or-Better implementation |
| `game/holdem.py` | Stub — `HoldEm.run()` returns balance unchanged |
| `game/five_card_draw.py` | Stub — `FiveCardDraw.run()` returns balance unchanged |
| `game/duel.py` | Stub — `Duel.run()` returns balance unchanged |
| `game/roguelike.py` | Stub — `Roguelike.run()` returns balance unchanged |
| `ai/__init__.py` | Empty |
| `ui/__init__.py` | Empty |
| `ui/components.py` | `Button`, `Slider` — event handling + drawing |
| `ui/renderer.py` | `draw_card()`, `draw_card_back()` — programmatic card sprites |
| `build/poker.spec` | PyInstaller spec (configured but not run in this plan) |
| `tests/test_cards.py` | Unit tests for Card, Deck |
| `tests/test_hand_evaluator.py` | Unit tests for all hand rankings |
| `tests/test_bankroll.py` | Unit tests for save/load/reset |
| `tests/test_modifiers.py` | Unit tests for ModifierSet |
| `tests/test_video_poker.py` | Unit tests for payout logic, Jacks-or-Better check |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: all `__init__.py` files and empty dirs
- Create: `build/poker.spec`

- [ ] **Step 1: Install dependencies**

```bash
pip install pygame==2.5.2 pytest
```

Expected: no errors. Verify with `python -c "import pygame; print(pygame.__version__)"` → `2.5.2`

- [ ] **Step 2: Create requirements.txt**

```
pygame==2.5.2
pytest
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
*.pyo
dist/
build/dist/
*.spec.bak
save/
.pytest_cache/
*.egg-info/
```

- [ ] **Step 4: Create directory structure**

```bash
mkdir -p core game ai ui assets/sounds assets/music assets/images assets/fonts build save tests
```

- [ ] **Step 5: Create all __init__.py files**

Create empty files at: `core/__init__.py`, `game/__init__.py`, `ai/__init__.py`, `ui/__init__.py`, `tests/__init__.py`

- [ ] **Step 6: Create PyInstaller spec stub**

`build/poker.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[('../assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='poker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

- [ ] **Step 7: Set up git branches**

```bash
git checkout -b feature/foundation
```

- [ ] **Step 8: Initial commit**

```bash
git add requirements.txt .gitignore build/poker.spec core/__init__.py game/__init__.py ai/__init__.py ui/__init__.py tests/__init__.py
git commit -m "chore: project scaffold — dirs, deps, gitignore, pyinstaller spec"
```

---

## Task 2: Core — Cards

**Files:**
- Create: `core/cards.py`
- Create: `tests/test_cards.py`

- [ ] **Step 1: Write failing tests**

`tests/test_cards.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_cards.py -v
```

Expected: `ModuleNotFoundError` — `core.cards` does not exist yet.

- [ ] **Step 3: Implement core/cards.py**

```python
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_cards.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add core/cards.py tests/test_cards.py
git commit -m "feat: Card and Deck with full test coverage"
```

---

## Task 3: Core — Hand Evaluator

**Files:**
- Create: `core/hand_evaluator.py`
- Create: `tests/test_hand_evaluator.py`

- [ ] **Step 1: Write failing tests**

`tests/test_hand_evaluator.py`:
```python
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
        rank = rank_map.get(r_str, int(r_str))
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_hand_evaluator.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement core/hand_evaluator.py**

```python
from collections import Counter
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

    # Tiebreaker: sort by frequency desc, then rank desc
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_hand_evaluator.py -v
```

Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add core/hand_evaluator.py tests/test_hand_evaluator.py
git commit -m "feat: hand evaluator covering all rankings + tiebreakers"
```

---

## Task 4: Core — Bankroll

**Files:**
- Create: `core/bankroll.py`
- Create: `tests/test_bankroll.py`

- [ ] **Step 1: Write failing tests**

`tests/test_bankroll.py`:
```python
import os
import pytest
import core.bankroll as bankroll

@pytest.fixture(autouse=True)
def tmp_save(tmp_path, monkeypatch):
    """Redirect save path to a temp dir for each test."""
    monkeypatch.setattr(bankroll, '_SAVE_DIR', str(tmp_path))

def test_load_returns_starting_balance_when_no_file():
    assert bankroll.load() == bankroll.STARTING_BALANCE

def test_save_and_load_roundtrip():
    bankroll.save(2500)
    assert bankroll.load() == 2500

def test_reset_returns_starting_balance():
    bankroll.save(100)
    result = bankroll.reset()
    assert result == bankroll.STARTING_BALANCE
    assert bankroll.load() == bankroll.STARTING_BALANCE

def test_save_creates_directory(tmp_path):
    nested = str(tmp_path / 'a' / 'b')
    bankroll._SAVE_DIR = nested
    bankroll.save(500)
    assert bankroll.load() == 500
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_bankroll.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement core/bankroll.py**

```python
import json
import os
import sys

def _default_save_dir() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'save')

_SAVE_DIR = _default_save_dir()
STARTING_BALANCE = 1000

def _path() -> str:
    return os.path.join(_SAVE_DIR, 'bankroll.json')

def load() -> int:
    p = _path()
    if not os.path.exists(p):
        return STARTING_BALANCE
    with open(p) as f:
        return json.load(f)['balance']

def save(balance: int) -> None:
    os.makedirs(_SAVE_DIR, exist_ok=True)
    with open(_path(), 'w') as f:
        json.dump({'balance': balance}, f)

def reset() -> int:
    save(STARTING_BALANCE)
    return STARTING_BALANCE
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_bankroll.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add core/bankroll.py tests/test_bankroll.py
git commit -m "feat: persistent bankroll with JSON save/load"
```

---

## Task 5: Core — ModifierSet Stub

**Files:**
- Create: `core/modifiers.py`
- Create: `tests/test_modifiers.py`

- [ ] **Step 1: Write failing tests**

`tests/test_modifiers.py`:
```python
from core.modifiers import ModifierSet, EMPTY

def test_empty_modifier_set():
    m = ModifierSet()
    assert m.is_empty()

def test_empty_constant_is_empty():
    assert EMPTY.is_empty()

def test_non_empty_when_wildcards():
    m = ModifierSet(wildcards=True)
    assert not m.is_empty()

def test_non_empty_when_timer():
    m = ModifierSet(decision_timer_seconds=3)
    assert not m.is_empty()
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_modifiers.py -v
```

- [ ] **Step 3: Implement core/modifiers.py**

```python
from dataclasses import dataclass

@dataclass
class ModifierSet:
    wildcards: bool = False
    no_score_cards: bool = False
    hands_visible: bool = False
    decision_timer_seconds: int = 0

    def is_empty(self) -> bool:
        return not any([
            self.wildcards,
            self.no_score_cards,
            self.hands_visible,
            self.decision_timer_seconds > 0,
        ])

EMPTY = ModifierSet()
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_modifiers.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Run full test suite to confirm nothing broken**

```bash
pytest tests/ -v
```

Expected: all 27 tests pass.

- [ ] **Step 6: Commit**

```bash
git add core/modifiers.py tests/test_modifiers.py
git commit -m "feat: ModifierSet stub — placeholder for party/roguelike modes"
```

---

## Task 6: Pygame Window + Main Loop

**Files:**
- Create: `main.py`

- [ ] **Step 1: Create main.py**

```python
import sys
import pygame
import core.bankroll as bankroll
from core.modifiers import EMPTY

WIDTH, HEIGHT = 1280, 720
FPS = 60
FELT_GREEN = (10, 46, 26)

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Single Player Poker')
    clock = pygame.time.Clock()

    balance = bankroll.load()
    difficulty = 1  # 0=Easy 1=Normal 2=Hard

    from menu import Menu
    menu = Menu(screen, WIDTH, HEIGHT)

    running = True
    while running:
        action = None
        while action is None and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    action = menu.handle_event(event)

            screen.fill(FELT_GREEN)
            menu.draw(balance, difficulty)
            pygame.display.flip()
            clock.tick(FPS)

        if not running:
            break

        kind, value = action
        if kind == 'quit':
            break
        if kind == 'difficulty':
            difficulty = value
            continue
        if kind == 'play':
            balance = _launch(value, screen, clock, balance, difficulty)
            bankroll.save(balance)

    pygame.quit()
    sys.exit()

def _launch(mode: str, screen, clock, balance: int, difficulty: int) -> int:
    if mode == 'video_poker':
        from game.video_poker import VideoPoker
        return VideoPoker(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'holdem':
        from game.holdem import HoldEm
        return HoldEm(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'five_card_draw':
        from game.five_card_draw import FiveCardDraw
        return FiveCardDraw(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'duel':
        from game.duel import Duel
        return Duel(screen, clock, balance, difficulty, EMPTY).run()
    return balance

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Verify window opens (before menu exists)**

Temporarily add to the bottom of `main.py` to test:

```python
# TEMP TEST — remove after verifying
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('Poker — window test')
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((10, 46, 26))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
```

Run: `python main.py`
Expected: a 1280×720 green window opens, closes cleanly when X is clicked.

Remove the temp test block after verifying.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: Pygame window and top-level game loop"
```

---

## Task 7: UI Components

**Files:**
- Create: `ui/components.py`

No Pygame display tests — Button and Slider logic is tested via manual smoke test in Task 9.

- [ ] **Step 1: Create ui/components.py**

```python
import pygame

_BUTTON_COLOR = (30, 100, 60)
_BUTTON_HOVER = (45, 140, 80)
_BUTTON_TEXT = (255, 255, 255)
_GOLD = (245, 200, 66)
_SLIDER_BG = (20, 70, 40)

class Button:
    def __init__(self, rect: tuple, label: str, font: pygame.font.Font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True on left-click."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        color = _BUTTON_HOVER if self._hovered else _BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, _GOLD, self.rect, 2, border_radius=8)
        text = self.font.render(self.label, True, _BUTTON_TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Slider:
    """Integer-step slider. Snaps to nearest integer on release."""

    def __init__(self, rect: tuple, min_val: int, max_val: int,
                 initial: int, font: pygame.font.Font, labels: list[str]):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self._value = float(initial)
        self.font = font
        self.labels = labels
        self._dragging = False
        self.changed = False  # Set True when snapped value changes; caller clears it

    @property
    def value(self) -> int:
        return round(self._value)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            if self._dragging:
                self._dragging = False
                self.changed = True
        if event.type == pygame.MOUSEMOTION and self._dragging:
            ratio = (event.pos[0] - self.rect.x) / max(self.rect.width, 1)
            ratio = max(0.0, min(1.0, ratio))
            self._value = self.min_val + ratio * (self.max_val - self.min_val)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, _SLIDER_BG, self.rect, border_radius=4)
        ratio = (self._value - self.min_val) / max(self.max_val - self.min_val, 1)
        hx = int(self.rect.x + ratio * self.rect.width)
        handle = pygame.Rect(hx - 10, self.rect.y - 6, 20, self.rect.height + 12)
        pygame.draw.rect(surface, _GOLD, handle, border_radius=4)
        label = self.labels[self.value] if self.labels else str(self.value)
        text = self.font.render(f'Difficulty: {label}', True, (255, 255, 255))
        surface.blit(text, (self.rect.x, self.rect.y - 28))
```

- [ ] **Step 2: Commit**

```bash
git add ui/components.py
git commit -m "feat: Button and Slider UI components"
```

---

## Task 8: Card Renderer

**Files:**
- Create: `ui/renderer.py`

- [ ] **Step 1: Create ui/renderer.py**

```python
import pygame

CARD_W = 80
CARD_H = 110

_CARD_BG = (255, 255, 255)
_CARD_BACK = (0, 80, 160)
_CARD_BACK_INNER = (0, 55, 110)
_RED = (200, 0, 0)
_BLACK = (20, 20, 20)
_SELECTED_BORDER = (255, 215, 0)
_UNSELECTED_BORDER = (180, 180, 180)

_SUIT_SYMBOLS = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}
_RANK_NAMES = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}


def draw_card(surface: pygame.Surface, card, x: int, y: int,
              font: pygame.font.Font, selected: bool = False) -> None:
    """Draw a face-up card. `card` is a core.cards.Card instance."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BG, rect, border_radius=6)
    border_color = _SELECTED_BORDER if selected else _UNSELECTED_BORDER
    pygame.draw.rect(surface, border_color, rect, 3 if selected else 1, border_radius=6)

    color = _RED if card.suit in ('H', 'D') else _BLACK
    rank_str = _RANK_NAMES.get(card.rank, str(card.rank))
    suit_str = _SUIT_SYMBOLS[card.suit]

    corner = font.render(f'{rank_str}{suit_str}', True, color)
    surface.blit(corner, (x + 5, y + 5))

    center_suit = font.render(suit_str, True, color)
    surface.blit(center_suit, center_suit.get_rect(center=(x + CARD_W // 2, y + CARD_H // 2)))


def draw_card_back(surface: pygame.Surface, x: int, y: int) -> None:
    """Draw a face-down card."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BACK, rect, border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=6)
    inner = pygame.Rect(x + 6, y + 6, CARD_W - 12, CARD_H - 12)
    pygame.draw.rect(surface, _CARD_BACK_INNER, inner, border_radius=4)
```

- [ ] **Step 2: Commit**

```bash
git add ui/renderer.py
git commit -m "feat: programmatic card renderer (face-up, face-down, selected state)"
```

---

## Task 9: Main Menu

**Files:**
- Create: `menu.py`

- [ ] **Step 1: Create menu.py**

```python
import pygame
from ui.components import Button, Slider

_GOLD = (245, 200, 66)
_WHITE = (255, 255, 255)
_GRAY = (180, 180, 180)
_FELT = (10, 46, 26)


class Menu:
    def __init__(self, screen: pygame.Surface, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height

        font_title = pygame.font.SysFont('Georgia', 56, bold=True)
        font_btn = pygame.font.SysFont('Georgia', 26)
        font_small = pygame.font.SysFont('Georgia', 20)
        self._font_small = font_small

        self._title = font_title.render('SINGLE PLAYER POKER', True, _GOLD)
        self._title_rect = self._title.get_rect(center=(width // 2, 110))

        cx = width // 2
        self._buttons = {
            'video_poker':   Button((cx - 160, 230, 320, 52), 'Video Poker',    font_btn),
            'holdem':        Button((cx - 160, 298, 320, 52), "Texas Hold'em",  font_btn),
            'five_card_draw':Button((cx - 160, 366, 320, 52), '5-Card Draw',    font_btn),
            'duel':          Button((cx - 160, 434, 320, 52), '1v1 Duel',       font_btn),
            'quit':          Button((cx - 160, 522, 320, 52), 'Quit',           font_btn),
        }
        self._slider = Slider(
            (cx - 160, 624, 320, 16), 0, 2, 1,
            font_small, ['Easy', 'Normal', 'Hard']
        )
        self._balance_font = font_small

    def handle_event(self, event: pygame.event.Event):
        """Returns (kind, value) tuple or None."""
        self._slider.handle_event(event)
        if self._slider.changed:
            self._slider.changed = False
            return ('difficulty', self._slider.value)

        for name, btn in self._buttons.items():
            if btn.handle_event(event):
                if name == 'quit':
                    return ('quit', None)
                return ('play', name)
        return None

    def draw(self, balance: int, difficulty: int) -> None:
        self.screen.blit(self._title, self._title_rect)

        bal_text = self._balance_font.render(f'Balance: ${balance:,}', True, _GOLD)
        self.screen.blit(bal_text, bal_text.get_rect(center=(self.width // 2, 175)))

        for btn in self._buttons.values():
            btn.draw(self.screen)
        self._slider.draw(self.screen)
```

- [ ] **Step 2: Smoke test — run the game and verify the menu appears**

```bash
python main.py
```

Expected: window opens with title, balance display, five buttons, and a difficulty slider. Clicking Quit closes the window. Clicking any game mode should not crash (stubs come next).

- [ ] **Step 3: Commit**

```bash
git add menu.py
git commit -m "feat: main menu with mode buttons, difficulty slider, balance display"
```

---

## Task 10: Game Module Stubs

**Files:**
- Create: `game/holdem.py`
- Create: `game/five_card_draw.py`
- Create: `game/duel.py`
- Create: `game/roguelike.py`

- [ ] **Step 1: Create stub files**

`game/holdem.py`:
```python
import pygame
from core.modifiers import ModifierSet


class HoldEm:
    """Texas Hold'em — not yet implemented."""

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock = clock
        self.balance = balance

    def run(self) -> int:
        font = pygame.font.SysFont('Georgia', 32)
        msg = font.render("Hold'em — Coming Soon!  Press any key.", True, (255, 255, 255))
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
            self.screen.fill((10, 46, 26))
            self.screen.blit(msg, msg.get_rect(center=self.screen.get_rect().center))
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance
```

`game/five_card_draw.py`:
```python
import pygame
from core.modifiers import ModifierSet


class FiveCardDraw:
    """5-Card Draw — not yet implemented."""

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock = clock
        self.balance = balance

    def run(self) -> int:
        font = pygame.font.SysFont('Georgia', 32)
        msg = font.render('5-Card Draw — Coming Soon!  Press any key.', True, (255, 255, 255))
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
            self.screen.fill((10, 46, 26))
            self.screen.blit(msg, msg.get_rect(center=self.screen.get_rect().center))
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance
```

`game/duel.py`:
```python
import pygame
from core.modifiers import ModifierSet


class Duel:
    """1v1 Duel — not yet implemented."""

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock = clock
        self.balance = balance

    def run(self) -> int:
        font = pygame.font.SysFont('Georgia', 32)
        msg = font.render('1v1 Duel — Coming Soon!  Press any key.', True, (255, 255, 255))
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
            self.screen.fill((10, 46, 26))
            self.screen.blit(msg, msg.get_rect(center=self.screen.get_rect().center))
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance
```

`game/roguelike.py`:
```python
import pygame
from core.modifiers import ModifierSet


class Roguelike:
    """Roguelike Progression Mode — not yet implemented. See design spec."""

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock = clock
        self.balance = balance

    def run(self) -> int:
        return self.balance
```

- [ ] **Step 2: Smoke test — click each stub mode from the menu**

```bash
python main.py
```

Expected: clicking Hold'em, 5-Card Draw, and 1v1 Duel each shows a "Coming Soon" screen that returns to the menu on any key press. No crashes.

- [ ] **Step 3: Commit**

```bash
git add game/holdem.py game/five_card_draw.py game/duel.py game/roguelike.py
git commit -m "feat: stub screens for Hold'em, 5-Card Draw, Duel, Roguelike"
```

---

## Task 11: Video Poker Logic

**Files:**
- Create: `tests/test_video_poker.py`
- Create: `game/video_poker.py`

- [ ] **Step 1: Write failing tests for payout logic**

`tests/test_video_poker.py`:
```python
from core.cards import Card
from game.video_poker import VideoPoker, payout, is_jacks_or_better

def cards(*specs):
    rank_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    result = []
    for s in specs:
        r_str, suit = s[:-1], s[-1]
        rank = rank_map.get(r_str, int(r_str))
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_video_poker.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement game/video_poker.py**

```python
import pygame
from collections import Counter
from core.cards import Deck, Card
from core.hand_evaluator import (
    evaluate, ONE_PAIR, HAND_NAMES,
    ROYAL_FLUSH, STRAIGHT_FLUSH, FOUR_OF_A_KIND, FULL_HOUSE,
    FLUSH, STRAIGHT, THREE_OF_A_KIND, TWO_PAIR, HIGH_CARD
)
from core.modifiers import ModifierSet
from ui.renderer import draw_card, draw_card_back, CARD_W, CARD_H

_PAYTABLE = {
    ROYAL_FLUSH:     800,
    STRAIGHT_FLUSH:  50,
    FOUR_OF_A_KIND:  25,
    FULL_HOUSE:      9,
    FLUSH:           6,
    STRAIGHT:        4,
    THREE_OF_A_KIND: 3,
    TWO_PAIR:        2,
    ONE_PAIR:        1,  # only if Jacks or Better
    HIGH_CARD:       0,
}

_GOLD = (245, 200, 66)
_WHITE = (255, 255, 255)
_FELT = (10, 46, 26)
_RED_WIN = (220, 50, 50)
_GREEN_WIN = (50, 200, 100)


def is_jacks_or_better(hand: list[Card]) -> bool:
    """True if the hand contains exactly one pair of Jacks or higher."""
    rank_val, _ = evaluate(hand)
    if rank_val != ONE_PAIR:
        return False
    counts = Counter(c.rank for c in hand)
    pair_rank = next(r for r, cnt in counts.items() if cnt == 2)
    return pair_rank >= 11


def payout(hand: list[Card], bet: int) -> int:
    """Return chip payout for the given 5-card hand and bet amount."""
    rank_val, _ = evaluate(hand)
    if rank_val == ONE_PAIR and not is_jacks_or_better(hand):
        return 0
    return _PAYTABLE.get(rank_val, 0) * bet


class VideoPoker:
    _MIN_BET = 5
    _MAX_BET = 100
    _BET_STEP = 5

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock = clock
        self.balance = balance
        self.modifiers = modifiers

        self._font = pygame.font.SysFont('Georgia', 24, bold=True)
        self._small = pygame.font.SysFont('Georgia', 18)
        self._w, self._h = screen.get_size()

        self._bet = self._MIN_BET
        self._hand: list[Card] = []
        self._held = [False] * 5
        self._phase = 'betting'   # 'betting' | 'holding' | 'result'
        self._result_msg = ''
        self._win_amount = 0
        self._deck = Deck()

        # Buttons
        bw, bh = 110, 40
        card_start_x = (self._w - (5 * CARD_W + 4 * 16)) // 2
        card_y = self._h // 2 - CARD_H // 2
        self._hold_rects = [
            pygame.Rect(card_start_x + i * (CARD_W + 16), card_y + CARD_H + 10, CARD_W, 30)
            for i in range(5)
        ]
        cx = self._w // 2
        self._deal_btn = pygame.Rect(cx - bw // 2, card_y + CARD_H + 55, bw, bh)
        self._bet_up = pygame.Rect(cx + 90, self._h - 80, 40, 36)
        self._bet_dn = pygame.Rect(cx + 140, self._h - 80, 40, 36)
        self._back_btn = pygame.Rect(30, 30, 100, 36)
        self._card_start_x = card_start_x
        self._card_y = card_y

    def run(self) -> int:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._back_btn.collidepoint(event.pos):
                        running = False
                    else:
                        self._handle_click(event.pos)
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance

    def _handle_click(self, pos: tuple) -> None:
        if self._phase == 'betting':
            if self._deal_btn.collidepoint(pos):
                if self.balance >= self._bet:
                    self._deal_initial()
            if self._bet_up.collidepoint(pos):
                self._bet = min(self._MAX_BET, self._bet + self._BET_STEP)
            if self._bet_dn.collidepoint(pos):
                self._bet = max(self._MIN_BET, self._bet - self._BET_STEP)

        elif self._phase == 'holding':
            for i, rect in enumerate(self._hold_rects):
                if rect.collidepoint(pos):
                    self._held[i] = not self._held[i]
            if self._deal_btn.collidepoint(pos):
                self._draw_phase()

        elif self._phase == 'result':
            if self._deal_btn.collidepoint(pos):
                self._phase = 'betting'
                self._hand = []
                self._held = [False] * 5

    def _deal_initial(self) -> None:
        self.balance -= self._bet
        self._deck = Deck()
        self._deck.shuffle()
        self._hand = self._deck.deal(5)
        self._held = [False] * 5
        self._phase = 'holding'

    def _draw_phase(self) -> None:
        for i in range(5):
            if not self._held[i]:
                self._hand[i] = self._deck.deal(1)[0]
        won = payout(self._hand, self._bet)
        self.balance += won
        rank_val, _ = evaluate(self._hand)
        if rank_val == ONE_PAIR and not is_jacks_or_better(self._hand):
            self._result_msg = 'No Win'
            self._win_amount = 0
        else:
            self._result_msg = HAND_NAMES[rank_val]
            self._win_amount = won
        self._phase = 'result'

    def _draw(self) -> None:
        self.screen.fill(_FELT)

        # Title + balance
        title = self._font.render('VIDEO POKER — Jacks or Better', True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, 50)))
        bal = self._small.render(f'Balance: ${self.balance:,}', True, _WHITE)
        self.screen.blit(bal, (self._w - 200, 20))

        # Back button
        pygame.draw.rect(self.screen, (60, 60, 60), self._back_btn, border_radius=6)
        back_t = self._small.render('← Menu', True, _WHITE)
        self.screen.blit(back_t, back_t.get_rect(center=self._back_btn.center))

        # Cards
        for i, card in enumerate(self._hand):
            x = self._card_start_x + i * (CARD_W + 16)
            draw_card(self.screen, card, x, self._card_y, self._font, self._held[i])
            if self._phase == 'holding':
                label = 'HOLD' if self._held[i] else 'DISCARD'
                color = _GOLD if self._held[i] else (150, 150, 150)
                t = self._small.render(label, True, color)
                self.screen.blit(t, t.get_rect(center=self._hold_rects[i].center))

        # Bet display
        cx = self._w // 2
        bet_t = self._font.render(f'Bet: ${self._bet}', True, _GOLD)
        self.screen.blit(bet_t, bet_t.get_rect(center=(cx, self._h - 65)))

        if self._phase == 'betting':
            pygame.draw.rect(self.screen, (30, 100, 60), self._deal_btn, border_radius=8)
            t = self._font.render('DEAL', True, _WHITE)
            self.screen.blit(t, t.get_rect(center=self._deal_btn.center))
            pygame.draw.rect(self.screen, (30, 100, 60), self._bet_up, border_radius=4)
            self.screen.blit(self._small.render('+', True, _WHITE), self._bet_up.move(12, 8))
            pygame.draw.rect(self.screen, (30, 100, 60), self._bet_dn, border_radius=4)
            self.screen.blit(self._small.render('-', True, _WHITE), self._bet_dn.move(14, 8))

        elif self._phase == 'holding':
            pygame.draw.rect(self.screen, (80, 30, 30), self._deal_btn, border_radius=8)
            t = self._font.render('DRAW', True, _WHITE)
            self.screen.blit(t, t.get_rect(center=self._deal_btn.center))

        elif self._phase == 'result':
            color = _GREEN_WIN if self._win_amount > 0 else _RED_WIN
            msg = f'{self._result_msg}  +${self._win_amount}' if self._win_amount > 0 else self._result_msg
            result_t = self._font.render(msg, True, color)
            self.screen.blit(result_t, result_t.get_rect(center=(cx, self._card_y - 40)))
            pygame.draw.rect(self.screen, (30, 100, 60), self._deal_btn, border_radius=8)
            t = self._font.render('PLAY AGAIN', True, _WHITE)
            self.screen.blit(t, t.get_rect(center=self._deal_btn.center))
```

- [ ] **Step 4: Run logic tests — expect PASS**

```bash
pytest tests/test_video_poker.py -v
```

Expected: 13 passed.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all 40 tests pass.

- [ ] **Step 6: Smoke test — play a full hand of Video Poker**

```bash
python main.py
```

- Click **Video Poker** from the menu
- Adjust bet with + / - buttons
- Click **DEAL** — 5 cards appear with HOLD/DISCARD labels below
- Click cards to toggle hold state
- Click **DRAW** — un-held cards are replaced, result is shown with win/loss
- Click **PLAY AGAIN** — returns to betting phase
- Click **← Menu** — returns to main menu; check that balance persisted

- [ ] **Step 7: Commit**

```bash
git add game/video_poker.py tests/test_video_poker.py
git commit -m "feat: Video Poker (Jacks or Better) — fully playable"
```

---

## Task 12: Merge + Tag

- [ ] **Step 1: Run full test suite one final time**

```bash
pytest tests/ -v
```

Expected: all 40 tests pass, 0 failures.

- [ ] **Step 2: Merge feature branch to main**

```bash
git checkout main
git merge feature/foundation --no-ff -m "feat: foundation + Video Poker complete"
```

- [ ] **Step 3: Tag v0.1**

```bash
git tag v0.1-foundation
```

- [ ] **Step 4: Push everything**

```bash
git push origin main
git push origin --tags
```

- [ ] **Step 5: Delete feature branch**

```bash
git branch -d feature/foundation
git push origin --delete feature/foundation
```

---

## Self-Review Notes

- All hand rank constants (`ONE_PAIR`, `ROYAL_FLUSH`, etc.) are defined in `core/hand_evaluator.py` and imported consistently across `test_video_poker.py` and `game/video_poker.py`
- `_SAVE_DIR` is a module-level variable in `core/bankroll.py` so tests can monkeypatch it — this is the only reason it's exposed at module level
- `draw_card` in `ui/renderer.py` takes a `font` parameter — `VideoPoker` passes `self._font` which is 24pt; this is intentional (card text matches the game's font size)
- `Deck.deal()` mutates `self.cards` in place — callers should create a new `Deck` per hand (VideoPoker does this in `_deal_initial`)
- Game module stubs show a "Coming Soon" screen rather than returning immediately — this lets you click through and verify routing works without a crash
