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

        title = self._font.render('VIDEO POKER — Jacks or Better', True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, 50)))
        bal = self._small.render(f'Balance: ${self.balance:,}', True, _WHITE)
        self.screen.blit(bal, (self._w - 200, 20))

        pygame.draw.rect(self.screen, (60, 60, 60), self._back_btn, border_radius=6)
        back_t = self._small.render('← Menu', True, _WHITE)
        self.screen.blit(back_t, back_t.get_rect(center=self._back_btn.center))

        for i, card in enumerate(self._hand):
            x = self._card_start_x + i * (CARD_W + 16)
            draw_card(self.screen, card, x, self._card_y, self._font, self._held[i])
            if self._phase == 'holding':
                label = 'HOLD' if self._held[i] else 'DISCARD'
                color = _GOLD if self._held[i] else (150, 150, 150)
                t = self._small.render(label, True, color)
                self.screen.blit(t, t.get_rect(center=self._hold_rects[i].center))

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
