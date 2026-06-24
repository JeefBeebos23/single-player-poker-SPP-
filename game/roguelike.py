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
