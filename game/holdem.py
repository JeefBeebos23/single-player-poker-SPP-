import pygame
from core.cards import Deck, Card
from core.hand_evaluator import best_hand, HAND_NAMES
from core.modifiers import ModifierSet
from ai.personality import generate_opponents, Personality
from ai.engine import decide
from ai.dialogue import get_line
from ui.renderer import draw_card, draw_card_back, CARD_W, CARD_H
from ui.speech_bubble import SpeechBubble
import core.sound as sound

_GOLD  = (245, 200, 66)
_WHITE = (255, 255, 255)
_FELT  = (10, 46, 26)
_RED   = (220, 50, 50)
_GREEN = (50, 200, 100)
_GRAY  = (80, 80, 80)
_DARK  = (30, 30, 30)

_SMALL_BLIND = 5
_BIG_BLIND   = 10
_RAISE_STEP  = 10
_N_AI        = 2

_PHASE_LABELS = {
    'pre_flop': 'Pre-Flop',
    'flop':     'Flop',
    'turn':     'Turn',
    'river':    'River',
}


class HoldEm:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet):
        self.screen = screen
        self.clock  = clock
        self.balance = balance
        self.difficulty = difficulty
        self._w, self._h = screen.get_size()
        self._font  = pygame.font.SysFont('Georgia', 24, bold=True)
        self._small = pygame.font.SysFont('Georgia', 18)

        self._opponents = generate_opponents(_N_AI, difficulty)
        self._ai_stacks = [1000] * _N_AI
        self._ai_active = [True] * _N_AI
        self._ai_hands: list[list[Card]] = [[] for _ in range(_N_AI)]

        self._bubbles = [
            SpeechBubble(self._w // 4,     80, self._small),
            SpeechBubble(3 * self._w // 4, 80, self._small),
        ]

        self._hole:      list[Card] = []
        self._community: list[Card] = []
        self._pot        = 0
        self._cur_bet    = 0
        self._phase      = 'pre_flop'
        self._phase_idx  = 0
        self._message    = ''
        self._result_msg = ''
        self._game_phase = 'start'
        self._running    = True

        # Layout
        comm_y = self._h // 2 - CARD_H // 2
        comm_x = (self._w - (5 * CARD_W + 4 * 10)) // 2
        self._comm_positions = [(comm_x + i * (CARD_W + 10), comm_y) for i in range(5)]
        hole_y = self._h // 2 + CARD_H // 2 + 30
        self._hole_xs = [self._w // 2 - CARD_W - 5, self._w // 2 + 5]

        cx = self._w // 2
        self._btn_fold  = pygame.Rect(cx - 195, self._h - 70, 120, 40)
        self._btn_check = pygame.Rect(cx - 65,  self._h - 70, 120, 40)
        self._btn_call  = pygame.Rect(cx - 65,  self._h - 70, 120, 40)
        self._btn_raise = pygame.Rect(cx + 75,  self._h - 70, 120, 40)
        self._btn_back  = pygame.Rect(30, 30, 100, 36)
        self._btn_next  = pygame.Rect(cx - 75, self._h - 70, 150, 40)

        self._start_hand()

    def _start_hand(self) -> None:
        sound.play_music('gameplay')
        self._pot = 0
        self._ai_active = [True] * _N_AI

        self._deck = Deck()
        self._deck.shuffle()

        # Post blinds
        sb = min(_SMALL_BLIND, self._ai_stacks[0])
        bb = min(_BIG_BLIND,   self._ai_stacks[1])
        self._ai_stacks[0] -= sb
        self._ai_stacks[1] -= bb
        self._pot = sb + bb
        sound.play('chip_bet')
        self._cur_bet = _BIG_BLIND

        # Deal hole cards
        self._hole = self._deck.deal(2)
        sound.play('deal')
        for i in range(_N_AI):
            self._ai_hands[i] = self._deck.deal(2)

        self._community = []
        self._phase_idx = 0
        self._phase     = 'pre_flop'
        self._game_phase = 'betting'
        self._message = f'Pre-Flop — call ${_BIG_BLIND} or raise'

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

        if self._game_phase == 'betting':
            if self._btn_fold.collidepoint(pos):
                self._player_fold()
            elif self._cur_bet == 0 and self._btn_check.collidepoint(pos):
                self._player_check()
            elif self._cur_bet > 0 and self._btn_call.collidepoint(pos):
                self._player_call()
            elif self._btn_raise.collidepoint(pos):
                self._player_raise()

        elif self._game_phase == 'result':
            if self._btn_next.collidepoint(pos):
                if self.balance <= 0:
                    self._running = False
                else:
                    self._start_hand()

    def _player_fold(self) -> None:
        sound.play('fold')
        active = [i for i in range(_N_AI) if self._ai_active[i]]
        if active:
            share = self._pot // len(active)
            for i in active:
                self._ai_stacks[i] += share
        self._pot = 0
        self._result_msg = 'You folded.'
        self._game_phase = 'result'
        self._fire_dialogue('player_folds')

    def _player_check(self) -> None:
        sound.play('check')
        self._advance_after_player()

    def _player_call(self) -> None:
        sound.play('chip_bet')
        cost = min(self._cur_bet, self.balance)
        self.balance -= cost
        self._pot += cost
        self._advance_after_player()

    def _player_raise(self) -> None:
        sound.play('chip_bet')
        new_bet = self._cur_bet + _RAISE_STEP
        cost = min(new_bet, self.balance)
        self.balance -= cost
        self._pot += cost
        self._cur_bet = new_bet
        self._fire_dialogue('player_raises')
        self._advance_after_player()

    def _advance_after_player(self) -> None:
        self._ai_betting_round()
        active = [i for i in range(_N_AI) if self._ai_active[i]]
        if not active:
            self.balance += self._pot
            self._result_msg = f'All opponents folded! You win ${self._pot}.'
            self._pot = 0
            self._game_phase = 'result'
            return
        self._next_phase()

    def _ai_betting_round(self) -> None:
        for i, p in enumerate(self._opponents):
            if not self._ai_active[i]:
                continue
            all_cards = self._ai_hands[i] + self._community
            if len(all_cards) >= 5:
                score = best_hand(all_cards)
                hs = score[0] / 9.0
            elif len(all_cards) >= 2:
                # Pre-flop: use highest hole card rank as rough strength proxy
                hs = max(c.rank for c in self._ai_hands[i]) / 14.0
            else:
                hs = 0.0
            po = self._cur_bet / max(1, self._pot) if self._cur_bet > 0 else 0.0
            action = decide(hs, po, self._phase, self.difficulty, p)
            if action == 'fold' and self._cur_bet > 0:
                self._ai_active[i] = False
                self._fire_dialogue_from('lose_big', i)
            elif action in ('call', 'check'):
                cost = min(self._cur_bet, self._ai_stacks[i])
                self._ai_stacks[i] -= cost
                self._pot += cost
            elif action in ('raise', 'all_in'):
                raise_amt = _RAISE_STEP if action == 'raise' else self._ai_stacks[i]
                new_bet = self._cur_bet + raise_amt
                cost = min(new_bet, self._ai_stacks[i])
                self._ai_stacks[i] -= cost
                self._pot += cost
                self._cur_bet = new_bet

    def _next_phase(self) -> None:
        self._phase_idx += 1
        self._cur_bet = 0
        if self._phase_idx == 1:
            self._community = self._deck.deal(3)
            self._phase = 'flop'
        elif self._phase_idx == 2:
            self._community += self._deck.deal(1)
            self._phase = 'turn'
        elif self._phase_idx == 3:
            self._community += self._deck.deal(1)
            self._phase = 'river'
        else:
            self._showdown()
            return
        self._message = f'{_PHASE_LABELS[self._phase]} — check or bet'

    def _showdown(self) -> None:
        player_all = self._hole + self._community
        player_score = best_hand(player_all)
        winner = 'player'
        best_score = player_score
        for i in range(_N_AI):
            if not self._ai_active[i]:
                continue
            ai_all = self._ai_hands[i] + self._community
            ai_score = best_hand(ai_all)
            if ai_score > best_score:
                best_score = ai_score
                winner = i

        if winner == 'player':
            self.balance += self._pot
            self._result_msg = f'You win! {HAND_NAMES[player_score[0]]} — +${self._pot}'
            sound.play('chip_collect')
            self._fire_dialogue('lose_big')
        else:
            self._ai_stacks[winner] += self._pot
            ai_all = self._ai_hands[winner] + self._community
            ai_score = best_hand(ai_all)
            self._result_msg = f'{self._opponents[winner].name} wins with {HAND_NAMES[ai_score[0]]}!'
            sound.play('lose')
            self._fire_dialogue_from('win_pot', winner)
        self._pot = 0
        self._game_phase = 'result'

    def _fire_dialogue(self, trigger: str) -> None:
        for i, p in enumerate(self._opponents):
            if self._ai_active[i]:
                line = get_line(trigger, self.difficulty, p)
                if line:
                    self._bubbles[i].show(line)
                    sound.play('bubble_pop')
                    break

    def _fire_dialogue_from(self, trigger: str, idx: int) -> None:
        line = get_line(trigger, self.difficulty, self._opponents[idx])
        if line:
            self._bubbles[idx].show(line)
            sound.play('bubble_pop')

    def _draw(self) -> None:
        self.screen.fill(_FELT)
        title = self._font.render("TEXAS HOLD'EM", True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, 40)))

        bal = self._small.render(f'Balance: ${self.balance:,}  Pot: ${self._pot:,}', True, _WHITE)
        self.screen.blit(bal, bal.get_rect(center=(self._w // 2, 75)))

        for i, p in enumerate(self._opponents):
            sx = self._w // 4 if i == 0 else 3 * self._w // 4
            color = _WHITE if self._ai_active[i] else _GRAY
            name_t = self._small.render(p.name, True, color)
            self.screen.blit(name_t, name_t.get_rect(center=(sx, 110)))
            stack_t = self._small.render(f'${self._ai_stacks[i]:,}', True, color)
            self.screen.blit(stack_t, stack_t.get_rect(center=(sx, 130)))
            if self._ai_active[i] and self._ai_hands[i]:
                for j in range(2):
                    bx = sx - CARD_W - 4 + j * (CARD_W + 8)
                    if self._game_phase == 'result':
                        draw_card(self.screen, self._ai_hands[i][j], bx, 148, self._font)
                    else:
                        draw_card_back(self.screen, bx, 148)
            self._bubbles[i].draw(self.screen)

        for idx, (x, y) in enumerate(self._comm_positions):
            if idx < len(self._community):
                draw_card(self.screen, self._community[idx], x, y, self._font)

        hole_y = self._h // 2 + CARD_H // 2 + 30
        for i, card in enumerate(self._hole):
            draw_card(self.screen, card, self._hole_xs[i], hole_y, self._font)

        phase_label = _PHASE_LABELS.get(self._phase, '')
        if phase_label:
            pt = self._small.render(phase_label, True, _GOLD)
            self.screen.blit(pt, pt.get_rect(center=(self._w // 2, self._h // 2 - CARD_H // 2 - 25)))

        pygame.draw.rect(self.screen, _GRAY, self._btn_back, border_radius=6)
        bt = self._small.render('← Menu', True, _WHITE)
        self.screen.blit(bt, bt.get_rect(center=self._btn_back.center))

        if self._game_phase == 'betting':
            self._draw_btn(self._btn_fold, 'Fold', _RED)
            if self._cur_bet == 0:
                self._draw_btn(self._btn_check, 'Check', _GREEN)
            else:
                self._draw_btn(self._btn_call, f'Call ${self._cur_bet}', _GREEN)
            self._draw_btn(self._btn_raise, f'Raise +${_RAISE_STEP}', _GOLD)

        elif self._game_phase == 'result':
            r = self._font.render(self._result_msg, True, _GOLD)
            self.screen.blit(r, r.get_rect(center=(self._w // 2, self._h // 2 - 20)))
            label = 'Game Over' if self.balance <= 0 else 'Next Hand'
            col   = _GRAY if self.balance <= 0 else _GREEN
            self._draw_btn(self._btn_next, label, col)

        msg_t = self._small.render(self._message, True, _WHITE)
        self.screen.blit(msg_t, msg_t.get_rect(center=(self._w // 2, self._h - 100)))

    def _draw_btn(self, rect: pygame.Rect, label: str, color: tuple) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        t = self._small.render(label, True, _WHITE if color != _GOLD else _DARK)
        self.screen.blit(t, t.get_rect(center=rect.center))
