import random
from dataclasses import dataclass

_FIRST = ['Marco', 'Rex', 'Sal', 'Nina', 'Dex', 'Vera', 'Lou', 'Cass', 'Bo', 'Ida',
          'Mick', 'Dot', 'Stu', 'Faye', 'Kane', 'Rosa', 'Gil', 'Nell', 'Ace', 'Rue']
_LAST  = ['Stone', 'Park', 'Vance', 'Cole', 'Walsh', 'Knox', 'Dunn', 'Ray', 'Cross', 'Hart']

@dataclass
class Personality:
    name: str
    loose_tight: float        # 0.0=very tight (folds often), 1.0=very loose (calls often)
    aggressive_passive: float # 0.0=very passive (checks/calls), 1.0=very aggressive (bets/raises)
    talk_frequency: float     # 0.0-1.0 chance to fire dialogue per trigger

def generate_opponents(n: int, difficulty: int) -> list[Personality]:
    """
    Generate n AI opponents with personalities influenced by difficulty.
    difficulty: 0=Easy, 1=Normal, 2=Hard
    """
    opponents = []
    used_names: set[str] = set()
    for _ in range(n):
        name = _pick_name(used_names)
        used_names.add(name)

        if difficulty == 0:
            loose_tight        = random.gauss(0.70, 0.15)
            aggressive_passive = random.gauss(0.30, 0.20)
            talk_freq          = random.uniform(0.5, 0.9)
        elif difficulty == 2:
            loose_tight        = random.gauss(0.35, 0.10)
            aggressive_passive = random.gauss(0.70, 0.10)
            talk_freq          = random.uniform(0.1, 0.4)
        else:
            loose_tight        = random.gauss(0.50, 0.20)
            aggressive_passive = random.gauss(0.50, 0.20)
            talk_freq          = random.uniform(0.3, 0.7)

        opponents.append(Personality(
            name=name,
            loose_tight=max(0.0, min(1.0, loose_tight)),
            aggressive_passive=max(0.0, min(1.0, aggressive_passive)),
            talk_frequency=max(0.0, min(1.0, talk_freq)),
        ))
    return opponents

def _pick_name(used: set) -> str:
    candidates = [f'{f} {l}' for f in _FIRST for l in _LAST]
    random.shuffle(candidates)
    for c in candidates:
        if c not in used:
            return c
    return 'Mystery Player'
