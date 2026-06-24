import pygame
import random
from core.cards import Deck, Card
from core.hand_evaluator import evaluate, HAND_NAMES, ONE_PAIR
from core.modifiers import ModifierSet
from ai.personality import generate_opponents, Personality
from ai.engine import decide
from ai.dialogue import get_line
from ui.renderer import draw_card, draw_card_back, CARD_W, CARD_H
from ui.speech_bubble import SpeechBubble

_GOLD  = (245, 200, 66)
_WHITE = (255, 255, 255)
_FELT  = (10, 46, 26)
_RED   = (220, 50, 50)
_GREEN = (50, 200, 100)
_GRAY  = (80, 80, 80)
_DARK  = (30, 30, 30)

_ANTE       = 10
_MIN_BET    = 10
_RAISE_STEP = 10


class FiveCardDraw:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock  = clock
        self.balance = balance
        self.difficulty = difficulty
        self.modifiers = modifiers
        self._w, self._h = screen.get_size()
        self._font  = pygame.font.SysFont('Georgia', 24, bold=True)
        self._small = pygame.font.SysFont('Georgia', 18)

        self._opponents: list[Personality] = generate_opponents(2, difficulty)
        self._ai_hands:  list[list[Card]]  = [[], []]
        self._ai_active: list[bool]        = [True, True]
        self._ai_stacks: list[int]         = [1000, 1000]

        self._bubbles = [
            SpeechBubble(self._w // 4,     80, self._small),
            SpeechBubble(3 * self._w // 4, 80, self._small),
        ]

        self._hand:   list[Card] = []
        self._marked: list[bool] = [False] * 5

        self._pot      = 0
        self._cur_bet  = 0
        self._phase    = 'start'
        self._message  = ''
        self._result_msg = ''

        card_start_x = (self._w - (5 * CARD_W + 4 * 12)) // 2
        self._card_xs = [card_start_x + i * (CARD_W + 12) for i in range(5)]
        self._card_y  = self._h // 2 + 20
        self._hold_rects = [
            pygame.Rect(self._card_xs[i], self._card_y + CARD_H + 8, CARD_W, 28)
            for i in range(5)
        ]

        cx = self._w // 2
        self._btn_fold  = pygame.Rect(cx - 195, self._h - 70, 120, 40)
        self._btn_check = pygame.Rect(cx - 65,  self._h - 70, 120, 40)
        self._btn_call  = pygame.Rect(cx - 65,  self._h - 70, 120, 40)
        self._btn_raise = pygame.Rect(cx + 75,  self._h - 70, 120, 40)
        self._btn_draw  = pygame.Rect(cx - 60,  self._h - 70, 120, 40)
        self._btn_back  = pygame.Rect(30, 30, 100, 36)
        self._btn_next  = pygame.Rect(cx - 75, self._h - 70, 150, 40)

        self._running = True
        self._start_round()

    def _start_round(self) -> None:
        ante = min(_ANTE, self.balance)
        self.balance -= ante
        self._pot = ante
        for i in range(2):
            ai_ante = min(_ANTE, self._ai_stacks[i])
            self._ai_stacks[i] -= ai_ante
            self._pot += ai_ante

        self._deck = Deck()
        self._deck.shuffle()
        self._hand = self._deck.deal(5)
        self._marked = [False] * 5
        for i in range(2):
            self._ai_hands[i] = self._deck.deal(5) if self._ai_active[i] else []
        self._ai_active = [True, True]
        self._cur_bet = 0
        self._phase = 'bet1'
        self._message = 'Round 1 — Bet or check to continue'

    def run(self) -> int:
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance

    def _handle_click(self, pos: tuple) -> None:
        if self._btn_back.collidepoint(pos):
            self._running = False
            return

        if self._phase in ('bet1', 'bet2'):
            if self._btn_fold.collidepoint(pos):
                self._player_fold()
            elif self._cur_bet == 0 and self._btn_check.collidepoint(pos):
                self._player_check()
            elif self._cur_bet > 0 and self._btn_call.collidepoint(pos):
                self._player_call()
            elif self._btn_raise.collidepoint(pos):
                self._player_raise()

        elif self._phase == 'draw':
            for i, rect in enumerate(self._hold_rects):
                if rect.collidepoint(pos):
                    self._marked[i] = not self._marked[i]
            if self._btn_draw.collidepoint(pos):
                self._do_draw()

        elif self._phase == 'result':
            if self._btn_next.collidepoint(pos):
                if self.balance <= 0:
                    self._running = False
                else:
                    self._pot = 0
                    self._start_round()

    def _player_fold(self) -> None:
        active = [i for i in range(2) if self._ai_active[i]]
        if active:
            share = self._pot // len(active)
            for i in active:
                self._ai_stacks[i] += share
        self._pot = 0
        self._result_msg = 'You folded.'
        self._phase = 'result'
        self._fire_dialogue('player_folds')

    def _player_check(self) -> None:
        self._ai_betting_round()

    def _player_call(self) -> None:
        cost = min(self._cur_bet, self.balance)
        self.balance -= cost
        self._pot += cost
        self._ai_betting_round()

    def _player_raise(self) -> None:
        total = self._cur_bet + _RAISE_STEP
        cost = min(total, self.balance)
        self.balance -= cost
        self._pot += cost
        self._cur_bet = total
        self._fire_dialogue('player_raises')
        self._ai_betting_round()

    def _ai_betting_round(self) -> None:
        for i, p in enumerate(self._opponents):
            if not self._ai_active[i]:
                continue
            hs = evaluate(self._ai_hands[i])[0] / 9.0
            po = self._cur_bet / max(1, self._pot) if self._cur_bet > 0 else 0.0
            action = decide(hs, po, 'post_flop', self.difficulty, p)
            if action == 'fold':
                self._ai_active[i] = False
                self._fire_dialogue_from('lose_big', i)
            elif action in ('call', 'check'):
                cost = min(self._cur_bet, self._ai_stacks[i])
                self._ai_stacks[i] -= cost
                self._pot += cost
            elif action in ('raise', 'all_in'):
                raise_amt = _RAISE_STEP if action == 'raise' else self._ai_stacks[i]
                cost = min(self._cur_bet + raise_amt, self._ai_stacks[i])
                self._cur_bet = cost
                self._ai_stacks[i] -= cost
                self._pot += cost

        if self._phase == 'bet1':
            self._phase = 'draw'
            self._message = 'Click cards to mark for discard, then Draw'
        elif self._phase == 'bet2':
            self._resolve_showdown()

    def _do_draw(self) -> None:
        for i in range(5):
            if self._marked[i] and len(self._deck) > 0:
                self._hand[i] = self._deck.deal(1)[0]
        self._marked = [False] * 5

        for i, p in enumerate(self._opponents):
            if not self._ai_active[i]:
                continue
            hs = evaluate(self._ai_hands[i])[0] / 9.0
            n_discard = self._ai_draw_count(hs)
            for _ in range(n_discard):
                if len(self._deck) > 0:
                    worst = min(range(5), key=lambda j: self._ai_hands[i][j].rank)
                    self._ai_hands[i][worst] = self._deck.deal(1)[0]

        self._cur_bet = 0
        self._phase = 'bet2'
        self._message = 'Round 2 — Bet or check'

    def _resolve_showdown(self) -> None:
        player_rank, _ = evaluate(self._hand)
        winner = 'player'
        best_rank = player_rank
        for i in range(2):
            if not self._ai_active[i]:
                continue
            ai_rank, _ = evaluate(self._ai_hands[i])
            if ai_rank > best_rank:
                best_rank = ai_rank
                winner = i

        if winner == 'player':
            self.balance += self._pot
            self._result_msg = f'You win! {HAND_NAMES[player_rank]} — +${self._pot}'
            self._fire_dialogue('lose_big')
        else:
            self._ai_stacks[winner] += self._pot
            ai_rank, _ = evaluate(self._ai_hands[winner])
            self._result_msg = f'{self._opponents[winner].name} wins with {HAND_NAMES[ai_rank]}!'
            self._fire_dialogue_from('win_pot', winner)
        self._pot = 0
        self._phase = 'result'

    def _ai_draw_count(self, hs: float) -> int:
        if hs >= 0.6:
            return 0
        if hs >= 0.3:
            return 1
        return random.randint(2, 3)

    def _fire_dialogue(self, trigger: str) -> None:
        for i, p in enumerate(self._opponents):
            if self._ai_active[i]:
                line = get_line(trigger, self.difficulty, p)
                if line:
                    self._bubbles[i].show(line)
                    break

    def _fire_dialogue_from(self, trigger: str, idx: int) -> None:
        line = get_line(trigger, self.difficulty, self._opponents[idx])
        if line:
            self._bubbles[idx].show(line)

    def _draw(self) -> None:
        self.screen.fill(_FELT)
        title = self._font.render('5-CARD DRAW', True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, 40)))

        bal = self._small.render(f'Balance: ${self.balance:,}  Pot: ${self._pot:,}', True, _WHITE)
        self.screen.blit(bal, bal.get_rect(center=(self._w // 2, 75)))

        for i, p in enumerate(self._opponents):
            sx = self._w // 4 if i == 0 else 3 * self._w // 4
            color = _WHITE if self._ai_active[i] else _GRAY
            name_t = self._small.render(p.name, True, color)
            self.screen.blit(name_t, name_t.get_rect(center=(sx, 110)))
            if self._ai_active[i] and self._ai_hands[i]:
                for j in range(5):
                    cx_card = sx - 2 * (CARD_W // 2 + 4) + j * (CARD_W // 2 + 4)
                    draw_card_back(self.screen, cx_card, 130)
            self._bubbles[i].draw(self.screen)

        for i, card in enumerate(self._hand):
            draw_card(self.screen, card, self._card_xs[i], self._card_y, self._font, self._marked[i])

        if self._phase == 'draw':
            for i in range(5):
                if self._marked[i]:
                    t = self._small.render('DISCARD', True, _RED)
                    self.screen.blit(t, t.get_rect(center=self._hold_rects[i].center))

        pygame.draw.rect(self.screen, _GRAY, self._btn_back, border_radius=6)
        bt = self._small.render('← Menu', True, _WHITE)
        self.screen.blit(bt, bt.get_rect(center=self._btn_back.center))

        if self._phase in ('bet1', 'bet2'):
            self._draw_btn(self._btn_fold, 'Fold', _RED)
            if self._cur_bet == 0:
                self._draw_btn(self._btn_check, 'Check', _GREEN)
            else:
                self._draw_btn(self._btn_call, f'Call ${self._cur_bet}', _GREEN)
            self._draw_btn(self._btn_raise, f'Raise +${_RAISE_STEP}', _GOLD)
        elif self._phase == 'draw':
            self._draw_btn(self._btn_draw, 'Draw', _GREEN)
        elif self._phase == 'result':
            r = self._font.render(self._result_msg, True, _GOLD)
            self.screen.blit(r, r.get_rect(center=(self._w // 2, self._h // 2 - 80)))
            label = 'Game Over' if self.balance <= 0 else 'Next Hand'
            self._draw_btn(self._btn_next, label, _GRAY if self.balance <= 0 else _GREEN)

        msg_t = self._small.render(self._message, True, _WHITE)
        self.screen.blit(msg_t, msg_t.get_rect(center=(self._w // 2, self._h - 100)))

    def _draw_btn(self, rect: pygame.Rect, label: str, color: tuple) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        t = self._small.render(label, True, _WHITE if color != _GOLD else _DARK)
        self.screen.blit(t, t.get_rect(center=rect.center))
