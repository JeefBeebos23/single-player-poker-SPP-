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
