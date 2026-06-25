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
import core.sound as sound

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

_GOLD      = (245, 200, 66)
_WHITE     = (255, 255, 255)
_FELT      = (10, 46, 26)
_RED_WIN   = (220, 50, 50)
_GREEN_WIN = (50, 200, 100)
_GRAY      = (80, 80, 80)

# Timing for card-flip animations
_DEAL_DELAY_MS  = 300   # gap before first card appears
_DEAL_STEP_MS   = 900   # gap between subsequent card reveals (~5 s for 5 cards)
_DRAW_DELAY_MS  = 300
_DRAW_STEP_MS   = 800   # gap between each replacement reveal


def is_jacks_or_better(hand: list[Card]) -> bool:
    rank_val, _ = evaluate(hand)
    if rank_val != ONE_PAIR:
        return False
    counts = Counter(c.rank for c in hand)
    pair_ranks = [r for r, cnt in counts.items() if cnt == 2]
    return max(pair_ranks) >= 11


def payout(hand: list[Card], bet: int) -> int:
    rank_val, _ = evaluate(hand)
    if rank_val == ONE_PAIR and not is_jacks_or_better(hand):
        return 0
    return _PAYTABLE.get(rank_val, 0) * bet


class VideoPoker:
    _MIN_BET  = 5
    _MAX_BET  = 100
    _BET_STEP = 5
    _CARD_GAP = 16

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock  = clock
        self.balance = balance
        self.modifiers = modifiers

        self._font  = pygame.font.SysFont('Georgia', 24, bold=True)
        self._small = pygame.font.SysFont('Georgia', 18)
        self._w, self._h = screen.get_size()

        self._bet  = self._MIN_BET
        self._hand: list[Card] = []
        self._held = [False] * 5

        # phase: 'betting' | 'dealing' | 'holding' | 'drawing' | 'result'
        self._phase      = 'betting'
        self._result_msg = ''
        self._win_amount = 0

        # Animation state
        self._anim_count    = 0   # cards revealed so far
        self._anim_next_at  = 0   # timestamp to reveal next card
        self._draw_indices: list[int] = []  # indices being replaced in draw phase
        self._result_sound  = ''  # sound to play when draw animation finishes

        card_start_x = (self._w - (5 * CARD_W + 4 * self._CARD_GAP)) // 2
        card_y       = self._h // 2 - CARD_H // 2
        self._hold_rects = [
            pygame.Rect(card_start_x + i * (CARD_W + self._CARD_GAP),
                        card_y + CARD_H + 10, CARD_W, 30)
            for i in range(5)
        ]
        self._card_rects = [
            pygame.Rect(card_start_x + i * (CARD_W + self._CARD_GAP),
                        card_y, CARD_W, CARD_H)
            for i in range(5)
        ]
        cx = self._w // 2
        self._deal_btn = pygame.Rect(cx - 55, card_y + CARD_H + 55, 110, 40)
        self._bet_up   = pygame.Rect(cx + 90, self._h - 80, 40, 36)
        self._bet_dn   = pygame.Rect(cx + 140, self._h - 80, 40, 36)
        self._back_btn = pygame.Rect(30, 30, 100, 36)
        self._card_start_x = card_start_x
        self._card_y = card_y

        sound.play_music('video_poker')

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------

    def run(self) -> int:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._back_btn.collidepoint(event.pos):
                        running = False
                    elif self._phase not in ('dealing', 'drawing'):
                        self._handle_click(event.pos)

            now = pygame.time.get_ticks()

            if self._phase == 'dealing' and now >= self._anim_next_at:
                self._anim_count += 1
                sound.play('flip')
                if self._anim_count >= 5:
                    self._phase = 'holding'
                else:
                    self._anim_next_at = now + _DEAL_STEP_MS

            elif self._phase == 'drawing' and now >= self._anim_next_at:
                if self._anim_count < len(self._draw_indices):
                    sound.play('flip')
                    self._anim_count += 1
                    if self._anim_count < len(self._draw_indices):
                        self._anim_next_at = now + _DRAW_STEP_MS
                    else:
                        # All new cards revealed — play result sound after brief pause
                        self._anim_next_at = now + 600
                elif now >= self._anim_next_at:
                    sound.stop_music()
                    if self._result_sound:
                        sound.play(self._result_sound)
                    self._phase = 'result'

            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

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
            for i in range(5):
                if self._hold_rects[i].collidepoint(pos) or \
                   self._card_rects[i].collidepoint(pos):
                    self._held[i] = not self._held[i]
                    sound.play('click')
            if self._deal_btn.collidepoint(pos):
                self._start_draw()

        elif self._phase == 'result':
            if self._deal_btn.collidepoint(pos):
                self._phase = 'betting'
                self._hand  = []
                self._held  = [False] * 5
                sound.play_music('video_poker')

    # ------------------------------------------------------------------
    # Deal + draw logic
    # ------------------------------------------------------------------

    def _deal_initial(self) -> None:
        self.balance -= self._bet
        self._deck   = Deck()
        self._deck.shuffle()
        self._hand   = self._deck.deal(5)
        self._held   = [False] * 5
        sound.play('deal')
        # Start deal animation: reveal cards one at a time
        self._anim_count   = 0
        self._anim_next_at = pygame.time.get_ticks() + _DEAL_DELAY_MS
        self._phase        = 'dealing'

    def _start_draw(self) -> None:
        """Replace non-held cards and start the draw animation."""
        self._draw_indices = [i for i in range(5) if not self._held[i]]
        for i in self._draw_indices:
            if self._deck:
                self._hand[i] = self._deck.deal(1)[0]

        # Evaluate result now (will be revealed when animation finishes)
        won = payout(self._hand, self._bet)
        self.balance += won
        rank_val, _  = evaluate(self._hand)
        self._win_amount = won
        if won == 0:
            self._result_msg = 'No Win' if rank_val == ONE_PAIR else HAND_NAMES[rank_val]
        else:
            self._result_msg = HAND_NAMES[rank_val]
        if won > 0:
            self._result_sound = 'win_big' if rank_val == ROYAL_FLUSH else 'chip_collect'
        else:
            self._result_sound = 'lose'

        if not self._draw_indices:
            # Held all 5 — skip animation, go straight to result
            sound.stop_music()
            if self._result_sound:
                sound.play(self._result_sound)
            self._phase = 'result'
            return

        self._anim_count   = 0
        self._anim_next_at = pygame.time.get_ticks() + _DRAW_DELAY_MS
        self._phase        = 'drawing'

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        self.screen.fill(_FELT)

        title = self._font.render('VIDEO POKER — Jacks or Better', True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, 50)))

        bal = self._small.render(f'Balance: ${self.balance:,}', True, _WHITE)
        self.screen.blit(bal, (self._w - 200, 20))

        pygame.draw.rect(self.screen, _GRAY, self._back_btn, border_radius=6)
        back_t = self._small.render('← Menu', True, _WHITE)
        self.screen.blit(back_t, back_t.get_rect(center=self._back_btn.center))

        # Cards
        revealed_draw = set(
            self._draw_indices[i] for i in range(self._anim_count)
        ) if self._phase == 'drawing' else set()

        for i, card in enumerate(self._hand):
            x = self._card_start_x + i * (CARD_W + self._CARD_GAP)
            if self._phase == 'dealing':
                if i < self._anim_count:
                    draw_card(self.screen, card, x, self._card_y, self._font)
                else:
                    draw_card_back(self.screen, x, self._card_y)
            elif self._phase == 'drawing':
                if self._held[i] or i in revealed_draw:
                    draw_card(self.screen, card, x, self._card_y,
                              self._font, self._held[i])
                else:
                    draw_card_back(self.screen, x, self._card_y)
            elif self._phase in ('holding', 'result'):
                draw_card(self.screen, card, x, self._card_y,
                          self._font, self._held[i])
            # 'betting': no cards

            # Hold/Discard labels (holding phase only)
            if self._phase == 'holding':
                label = 'HOLD' if self._held[i] else 'DISCARD'
                color = _GOLD if self._held[i] else _GRAY
                t = self._small.render(label, True, color)
                self.screen.blit(t, t.get_rect(center=self._hold_rects[i].center))

        cx = self._w // 2

        # Bet display
        bet_t = self._font.render(f'Bet: ${self._bet}', True, _GOLD)
        self.screen.blit(bet_t, bet_t.get_rect(center=(cx, self._h - 65)))

        # Phase buttons
        if self._phase == 'betting':
            can_deal  = self.balance >= self._bet
            btn_color = (30, 100, 60) if can_deal else _GRAY
            pygame.draw.rect(self.screen, btn_color, self._deal_btn, border_radius=8)
            t = self._font.render('DEAL', True, _WHITE)
            self.screen.blit(t, t.get_rect(center=self._deal_btn.center))
            if not can_deal:
                msg = self._small.render('Insufficient funds', True, _RED_WIN)
                self.screen.blit(msg, msg.get_rect(
                    center=(cx, self._deal_btn.bottom + 18)))
            pygame.draw.rect(self.screen, (30, 100, 60), self._bet_up, border_radius=4)
            self.screen.blit(self._small.render('+', True, _WHITE), self._bet_up.move(12, 8))
            pygame.draw.rect(self.screen, (30, 100, 60), self._bet_dn, border_radius=4)
            self.screen.blit(self._small.render('-', True, _WHITE), self._bet_dn.move(14, 8))

        elif self._phase in ('dealing', 'drawing'):
            pass  # no buttons during animation

        elif self._phase == 'holding':
            pygame.draw.rect(self.screen, (80, 30, 30), self._deal_btn, border_radius=8)
            t = self._font.render('DRAW', True, _WHITE)
            self.screen.blit(t, t.get_rect(center=self._deal_btn.center))

        elif self._phase == 'result':
            color  = _GREEN_WIN if self._win_amount > 0 else _RED_WIN
            prefix = f'{self._result_msg}  +${self._win_amount}' \
                     if self._win_amount > 0 else self._result_msg
            result_t = self._font.render(prefix, True, color)
            self.screen.blit(result_t,
                             result_t.get_rect(center=(cx, self._card_y - 40)))
            pygame.draw.rect(self.screen, (30, 100, 60), self._deal_btn, border_radius=8)
            t = self._font.render('PLAY AGAIN', True, _WHITE)
            self.screen.blit(t, t.get_rect(center=self._deal_btn.center))
