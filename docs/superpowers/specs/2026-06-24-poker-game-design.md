# Single Player Poker — Design Spec
**Date:** 2026-06-24
**Tech:** Python + Pygame, packaged with PyInstaller

---

## Overview

A polished, offline, single-player poker game for Windows. The player selects from multiple game modes via a main menu, competes against AI opponents with distinct personalities, and maintains a persistent chip bankroll that saves between sessions. The game is distributed as a standalone `poker.exe` — no installation required.

---

## Game Modes

Four selectable modes from the main menu:

### Video Poker (Jacks or Better)
- Deal 5 cards from a shuffled deck
- Player marks cards to hold/discard
- Draw phase replaces discarded cards
- Score final hand against a standard Jacks-or-Better pay table
- No AI opponents — purely player vs. the deck
- Minimum bet selected before each hand

### Texas Hold'em
- 2–4 AI opponents at the table (player selects count at mode entry, default 3)
- Full betting rounds: pre-flop, flop, turn, river
- Player and AI share community cards
- AI acts in turn order using the difficulty-based engine
- Buy-in deducted from bankroll at session start; winnings returned at end

### 5-Card Draw
- 2–4 AI opponents (player selects count at mode entry, default 3)
- Two betting rounds with a draw phase in between
- Each player may exchange up to 3 cards (4 if holding an Ace)
- Simpler than Hold'em but uses the same AI engine and difficulty system

### 1v1 Duel Mode
- Player selects either Hold'em or 5-Card Draw as the duel variant
- Thin wrapper over the chosen engine with exactly 1 AI opponent and a fixed ante structure
- Faster, higher-stakes feel — good for quick sessions
- Same AI difficulty and personality system applies

---

## AI System

### Personality Generation (`ai/personality.py`)
- Every game session generates a fresh set of AI opponents
- Each bot receives: a randomized name, a base temperament (loose / tight / aggressive / passive), and a personality bias that nudges the difficulty bell curve slightly
- Two "Normal" opponents will play noticeably differently from each other
- Personality also determines dialogue frequency and tone

### Decision Engine (`ai/engine.py`)
- AI decisions are drawn from a weighted probability distribution that shifts based on the selected difficulty
- Difficulty acts as a bell-curve shift, not a hard mode switch:

| Behavior | Easy | Normal | Hard |
|---|---|---|---|
| Fold weak hands | rarely | sometimes | often |
| Bluff | rarely | sometimes | often |
| Slow-play strong hand | never | rarely | sometimes |
| Call with marginal hand | often | sometimes | rarely |
| Aggressive re-raise | rarely | sometimes | often |

- Personality bias applies on top of difficulty — a loose-aggressive bot on Easy still calls more than a tight-passive bot on Easy
- The difficulty slider is global, set from the main menu before launching any mode

### Dialogue System (`ai/dialogue.py`)
- Each AI bot has a bank of lines organized by trigger and difficulty
- **Triggers:** bluff attempt, bluff success, winning a pot, losing a big pot, player raises big, player folds, showdown
- **Difficulty tone:**
  - Easy — overconfident and dumb (*"I always win!"*, *"Uh... I raise? Yeah."*)
  - Normal — casual taunts and reads (*"Bold move."*, *"You sure about that?"*)
  - Hard — cold, precise, unsettling (*"I counted that."*, *"You've done this before. Twice."*, *"..."*)
- Speech bubbles render above the AI's seat in the Pygame UI, fade out after a few seconds
- Dialogue frequency is influenced by personality — a loose-aggressive bot talks more than a tight-passive one

---

## Bankroll System (`core/bankroll.py`)

- Player starts with a configurable starting balance (default: $1,000)
- Balance persists between sessions, saved to `save/bankroll.json`
- All game modes draw bets and pay winnings against this shared balance
- If balance reaches $0, the player is offered a reset to the starting amount
- Balance is displayed on the main menu and in-game HUD

---

## Modifier System (`core/modifiers.py`)

Architecture placeholder shared by Party Mode and Roguelike Mode. Defines a `ModifierSet` class — an object that holds active modifier flags and values for a session. All game modules accept a `ModifierSet` at startup and check it at relevant decision points. For all currently implemented modes, the `ModifierSet` is always empty.

**Planned modifiers (not yet implemented):**
- Wildcard cards
- No-score cards
- Hands always visible to all players
- 3-second decision timer
- Other Balatro-style rule modifiers

Party Mode will be a fourth entry point in `menu.py` — lets the player pick or randomize modifiers, then launches an existing game engine with a populated `ModifierSet`.

Roguelike Mode (see below) consumes the same `ModifierSet` but populates it programmatically based on the current run round rather than player selection.

---

## UI & Rendering

**Style:** Polished casino aesthetic — green felt table, card graphics, chip animations, score counters, player seats.

**Pygame rendering (`ui/renderer.py`):**
- Card sprites (face-up and face-down)
- Felt table background with player seat positions
- Chip stack visualization
- Speech bubble overlay per AI seat
- Smooth transitions between game states (deal animation, card flip, chip slide)

**UI components (`ui/components.py`):**
- Buttons (Hold, Fold, Call, Raise, Draw)
- Difficulty slider (Easy / Normal / Hard)
- Bankroll display
- Mode selection cards on main menu
- Fade-in/out overlays for screen transitions

**Assets (`assets/`):**
- Card images or procedurally rendered card sprites
- Felt texture
- Chip graphics
- Fonts (casino-style)
- Sound effects (card deal, chip click, win/lose stings)

---

## File Structure

```
poker-game/
├── main.py                        # Entry point, main game loop, state machine
├── menu.py                        # Main menu, mode selection, difficulty slider
├── core/
│   ├── cards.py                   # Deck and Card classes
│   ├── hand_evaluator.py          # Hand ranking shared by all modes
│   ├── bankroll.py                # Persistent save/load
│   └── modifiers.py               # ModifierSet — active modifier flags/values
├── game/
│   ├── video_poker.py
│   ├── holdem.py
│   ├── five_card_draw.py
│   ├── duel.py                    # 1v1 wrapper
│   └── roguelike.py               # Placeholder stub — not yet implemented
├── ai/
│   ├── engine.py                  # Bell-curve decision engine
│   ├── personality.py             # Randomized name + trait generation
│   └── dialogue.py                # Contextual speech bubble lines
├── ui/
│   ├── renderer.py                # Card/chip/table drawing
│   └── components.py              # Buttons, sliders, overlays
├── assets/
│   ├── fonts/
│   ├── sounds/
│   └── images/
├── build/
│   └── poker.spec                 # PyInstaller config
├── docs/
│   └── superpowers/specs/
│       └── 2026-06-24-poker-game-design.md
└── save/
    └── bankroll.json              # Auto-created at runtime (gitignored)
```

---

## State Machine

`main.py` manages transitions between screens:

```
MENU → MODE_SELECT → GAME → RESULT → MENU
```

Each game module receives: current bankroll, difficulty setting, modifier set. It runs its own internal loop and returns the updated bankroll when done. The state machine in `main.py` never reaches into game logic — it only passes inputs and receives outputs.

---

## Branch & Release Strategy

| Branch | Purpose |
|---|---|
| `main` | All code, active development. Tagged at each version (`v1.0`, `v1.1`, etc.) |
| `feature/*` | One branch per feature, merged into `main` when complete |
| `release` | Always contains the latest `poker.exe`. Friends download from here — no technical knowledge needed. |

**Release flow:**
1. Feature complete and tested on `main`
2. Tag the commit: `git tag v1.0`
3. Run `pyinstaller build/poker.spec` → produces `dist/poker.exe`
4. Push `poker.exe` to `release` branch
5. Friends go to the repo, switch to `release`, click `poker.exe`, hit Download

---

## Packaging

```bash
pyinstaller build/poker.spec
```

`poker.spec` includes:
- All Python source files
- `assets/` directory (fonts, sounds, images)
- Pygame runtime
- Output: `dist/poker.exe` — single file, no install needed

`save/bankroll.json` is created at runtime in the same directory as the `.exe`.

---

## Out of Scope (this version)

- Multiplayer / networking
- Party Mode modifier implementation (architecture placeholder only)
- Roguelike Mode implementation (architecture placeholder only — see below)
- Leaderboards or stats tracking
- Mobile or web versions

---

## Placeholder: Roguelike Progression Mode

**Not implemented in v1. Architecture is reserved — `game/roguelike.py` is a stub file.**

A Balatro-inspired endless progression mode. The run is structured as a series of rounds, each harder than the last, with modifiers layering in as the run progresses.

**Intended design (to be fully specified when modifiers are ready):**

- Player starts at Easy difficulty with no modifiers active
- Each round completed advances the run — difficulty increases along a curve toward Hard
- At intervals, a new modifier is added to the active `ModifierSet` (e.g., round 5 adds a 3-second decision timer, round 8 makes all opponent hands visible, etc.)
- Stacking modifiers create increasingly chaotic and challenging combinations
- The run ends when the player goes broke or quits — there is no "win" state, only how far you get
- Bankroll resets at the start of each run (separate from the persistent main bankroll)
- Final round count and bankroll at bust are recorded as a personal best

**Dependencies before implementation:**
- `core/modifiers.py` fully built out with all planned modifiers
- Party Mode implemented first (proves the modifier pipeline works)
- Roguelike round/progression curve designed and balanced

**File stub:** `game/roguelike.py` — created as an empty placeholder so the branch and import structure are reserved.
