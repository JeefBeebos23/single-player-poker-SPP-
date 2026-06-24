from dataclasses import dataclass

@dataclass(frozen=True)
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
