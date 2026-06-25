import pygame
from core.modifiers import ModifierSet

_GOLD  = (245, 200, 66)
_WHITE = (255, 255, 255)
_FELT  = (10, 46, 26)
_GREEN = (50, 200, 100)
_GRAY  = (80, 80, 80)


class Duel:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock  = clock
        self.balance = balance
        self.difficulty = difficulty
        self.modifiers = modifiers
        self._w, self._h = screen.get_size()
        self._font  = pygame.font.SysFont('Georgia', 36, bold=True)
        self._small = pygame.font.SysFont('Georgia', 22)
        cx = self._w // 2
        self._btn_holdem = pygame.Rect(cx - 160, self._h // 2 - 30, 320, 56)
        self._btn_draw   = pygame.Rect(cx - 160, self._h // 2 + 50, 320, 56)
        self._btn_back   = pygame.Rect(30, 30, 100, 36)

    def run(self) -> int:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if self._btn_back.collidepoint(pos):
                        running = False
                    elif self._btn_holdem.collidepoint(pos):
                        from game.holdem import HoldEm
                        self.balance = HoldEm(self.screen, self.clock,
                                              self.balance, self.difficulty, self.modifiers,
                                              num_ai=1).run()
                        running = False
                    elif self._btn_draw.collidepoint(pos):
                        from game.five_card_draw import FiveCardDraw
                        self.balance = FiveCardDraw(self.screen, self.clock,
                                                    self.balance, self.difficulty, self.modifiers,
                                                    num_ai=1).run()
                        running = False
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance

    def _draw(self) -> None:
        self.screen.fill(_FELT)
        title = self._font.render('1v1 DUEL MODE', True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, self._h // 2 - 110)))
        sub = self._small.render('Choose your variant:', True, (200, 200, 200))
        self.screen.blit(sub, sub.get_rect(center=(self._w // 2, self._h // 2 - 65)))

        for rect, label, color in [
            (self._btn_holdem, "Texas Hold'em", _GREEN),
            (self._btn_draw,   '5-Card Draw',   _GREEN),
            (self._btn_back,   '← Menu',        _GRAY),
        ]:
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            t = self._small.render(label, True, _WHITE)
            self.screen.blit(t, t.get_rect(center=rect.center))
