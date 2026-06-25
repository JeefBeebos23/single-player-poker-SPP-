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
import core.sound as sound

_GOLD  = (245, 200, 66)
_WHITE = (255, 255, 255)
_FELT  = (10, 46, 26)
_RED   = (220, 50, 50)
_GREEN = (50, 200, 100)
_GRAY  = (80, 80, 80)
_DARK  = (30, 30, 30)
_BOX   = (8, 30, 15)

_ANTE        = 10
_MIN_BET     = 10
_RAISE_STEP  = 10
_AI_ACTION_MS = 2000  # ms per AI action in sequential display

_ACTION_LABELS = {
    'fold':   'Folds',
    'check':  'Checks',
    'call':   'Calls',
    'raise':  'Raises',
    'all_in': 'All In!',
}


_DRAW_STEP_MS  = 800   # ms between each replacement card reveal


class FiveCardDraw:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet,
                 num_ai: int = 2):
        self.screen = screen
        self.clock  = clock
        self.balance = balance
        self.difficulty = difficulty
        self.modifiers = modifiers
        self._w, self._h = screen.get_size()
        self._font        = pygame.font.SysFont('Georgia', 24, bold=True)
        self._font_banner = pygame.font.SysFont('Georgia', 40, bold=True)
        self._small       = pygame.font.SysFont('Georgia', 18)

        self._num_ai    = num_ai
        self._opponents = generate_opponents(num_ai, difficulty)
        self._ai_hands: list[list[Card]] = [[] for _ in range(num_ai)]
        self._ai_active: list[bool]      = [True] * num_ai
        self._ai_stacks: list[int]       = [1000] * num_ai

        if num_ai == 1:
            self._opp_xs = [self._w // 2]
            bubble_xs    = [self._w // 2]
        else:
            self._opp_xs = [self._w // 4, 3 * self._w // 4]
            bubble_xs    = [self._w // 4, 3 * self._w // 4]
        self._bubbles = [SpeechBubble(x, 80, self._small) for x in bubble_xs]

        self._hand:   list[Card] = []
        self._marked: list[bool] = [False] * 5
        self._raise_amt = _RAISE_STEP

        self._pot      = 0
        self._cur_bet  = 0
        self._phase    = 'start'
        self._message  = ''
        self._result_msg        = ''
        self._result_hand_lines: list[str] = []

        # Draw animation state
        self._draw_indices:  list[int] = []   # card positions being replaced
        self._draw_revealed: int       = 0    # how many new cards shown so far
        self._draw_next_at:  int       = 0    # next reveal timestamp

        # AI sequential animation state
        self._ai_queue:        list = []
        self._ai_queue_idx:    int  = 0
        self._ai_action_start: int  = 0
        self._ai_prev_phase:   str  = ''

        # Transition / banner timers
        self._phase_banner_until: int = 0
        self._phase_banner_text:  str = ''
        self._your_turn_until:    int = 0

        card_start_x = (self._w - (5 * CARD_W + 4 * 12)) // 2
        self._card_xs = [card_start_x + i * (CARD_W + 12) for i in range(5)]
        self._card_y  = self._h // 2 + 20
        self._hold_rects = [
            pygame.Rect(self._card_xs[i], self._card_y + CARD_H + 8, CARD_W, 28)
            for i in range(5)
        ]
        self._card_rects = [
            pygame.Rect(self._card_xs[i], self._card_y, CARD_W, CARD_H)
            for i in range(5)
        ]

        cx = self._w // 2
        by = self._h - 70
        # Button layout: Fold | Check/Call | [-] Raise $X [+] | All In
        self._btn_fold  = pygame.Rect(cx - 290, by, 110, 40)
        self._btn_check = pygame.Rect(cx - 168, by, 115, 40)
        self._btn_call  = pygame.Rect(cx - 168, by, 115, 40)
        self._btn_minus = pygame.Rect(cx - 42,  by,  28, 40)
        self._btn_raise = pygame.Rect(cx - 6,   by, 110, 40)
        self._btn_plus  = pygame.Rect(cx + 112, by,  28, 40)
        self._btn_allin = pygame.Rect(cx + 148, by,  80, 40)
        self._btn_draw  = pygame.Rect(cx - 60,  by, 120, 40)
        self._btn_back  = pygame.Rect(30, 30, 100, 36)
        self._btn_next  = pygame.Rect(cx - 75, by, 150, 40)

        self._running = True
        self._start_round()

    # ------------------------------------------------------------------
    # Round lifecycle
    # ------------------------------------------------------------------

    def _start_round(self) -> None:
        sound.play_music('gameplay')
        self._pot = 0
        self._raise_amt = _RAISE_STEP
        ante = min(_ANTE, self.balance)
        self.balance -= ante
        self._pot += ante
        for i in range(self._num_ai):
            ai_ante = min(_ANTE, self._ai_stacks[i])
            self._ai_stacks[i] -= ai_ante
            self._pot += ai_ante
        sound.play('chip_bet')

        self._deck = Deck()
        self._deck.shuffle()
        self._ai_active = [True] * self._num_ai
        self._result_hand_lines = []
        self._draw_indices  = []
        self._draw_revealed = 0
        self._hand = self._deck.deal(5)
        sound.play('deal')
        self._marked = [False] * 5
        for i in range(self._num_ai):
            self._ai_hands[i] = self._deck.deal(5)
        self._cur_bet = 0
        self._phase   = 'bet1'
        self._message = 'Round 1 — Bet or check to continue'
        self._ai_queue = []
        self._ai_queue_idx    = 0
        self._phase_banner_until = 0
        self._phase_banner_text  = ''
        self._your_turn_until    = 0

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------

    def run(self) -> int:
        while self._running:
            for event in pygame.event.get():
                sound.handle_event(event)
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._phase not in ('ai_turn', 'drawing'):
                        self._handle_click(event.pos)

            now = pygame.time.get_ticks()
            if self._phase == 'ai_turn':
                if len(self._ai_queue) == 0:
                    self._apply_ai_pending()
                elif now - self._ai_action_start >= _AI_ACTION_MS:
                    self._ai_queue_idx += 1
                    if self._ai_queue_idx >= len(self._ai_queue):
                        self._apply_ai_pending()
                    else:
                        self._ai_action_start = now
                        self._play_ai_action_sound(self._ai_queue[self._ai_queue_idx][2])

            elif self._phase == 'drawing' and now >= self._draw_next_at:
                if self._draw_revealed < len(self._draw_indices):
                    sound.play('flip')
                    self._draw_revealed += 1
                    if self._draw_revealed < len(self._draw_indices):
                        self._draw_next_at = now + _DRAW_STEP_MS
                    else:
                        self._draw_next_at = now + 500  # pause after last card
                else:
                    # Animation done → advance to second betting round
                    self._marked = [False] * 5
                    self._cur_bet            = 0
                    self._phase              = 'bet2'
                    self._message            = 'Round 2 — Bet or check'
                    self._phase_banner_until = now + 600
                    self._phase_banner_text  = 'BET ROUND 2'
                    self._raise_amt          = _RAISE_STEP
                    self._your_turn_until    = now + 700

            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple) -> None:
        if self._btn_back.collidepoint(pos):
            self._running = False
            return

        if pygame.time.get_ticks() < self._phase_banner_until:
            return  # block clicks during phase banner

        if self._phase in ('bet1', 'bet2'):
            if self._btn_fold.collidepoint(pos):
                self._player_fold()
            elif self._cur_bet == 0 and self._btn_check.collidepoint(pos):
                self._player_check()
            elif self._cur_bet > 0 and self._btn_call.collidepoint(pos):
                self._player_call()
            elif self._btn_minus.collidepoint(pos):
                self._raise_amt = max(_RAISE_STEP, self._raise_amt - _RAISE_STEP)
            elif self._btn_plus.collidepoint(pos):
                self._raise_amt = min(self.balance, self._raise_amt + _RAISE_STEP)
            elif self._btn_raise.collidepoint(pos):
                self._player_raise()
            elif self._btn_allin.collidepoint(pos):
                self._player_all_in()

        elif self._phase == 'draw':
            for i in range(5):
                if self._hold_rects[i].collidepoint(pos) or self._card_rects[i].collidepoint(pos):
                    self._marked[i] = not self._marked[i]
                    sound.play('click')
            if self._btn_draw.collidepoint(pos):
                self._do_draw()

        elif self._phase == 'result':
            if self._btn_next.collidepoint(pos):
                if self.balance <= 0:
                    self._running = False
                else:
                    self._pot = 0
                    self._start_round()

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def _player_fold(self) -> None:
        sound.play('fold')
        sound.stop_music()
        active = [i for i in range(self._num_ai) if self._ai_active[i]]
        if active:
            share = self._pot // len(active)
            for i in active:
                self._ai_stacks[i] += share
        self._pot = 0
        self._result_msg = 'You folded.'
        self._phase = 'result'
        self._message = ''
        self._fire_dialogue('player_folds')

    def _player_check(self) -> None:
        sound.play('check')
        self._start_ai_turn()

    def _player_call(self) -> None:
        sound.play('chip_bet')
        cost = min(self._cur_bet, self.balance)
        self.balance -= cost
        self._pot += cost
        self._start_ai_turn()

    def _player_raise(self) -> None:
        sound.play('raise')
        total = self._cur_bet + self._raise_amt
        cost  = min(total, self.balance)
        self.balance -= cost
        self._pot    += cost
        self._cur_bet = total
        self._fire_dialogue('player_raises')
        self._start_ai_turn()

    def _player_all_in(self) -> None:
        sound.play('raise')
        cost = self.balance
        self.balance = 0
        self._pot    += cost
        self._cur_bet = self._cur_bet + cost
        self._fire_dialogue('player_raises')
        self._start_ai_turn()

    # ------------------------------------------------------------------
    # AI turn (sequential animation)
    # ------------------------------------------------------------------

    def _start_ai_turn(self) -> None:
        """Pre-compute AI decisions for this round and start sequential display."""
        self._ai_queue = []
        for i, p in enumerate(self._opponents):
            if not self._ai_active[i]:
                continue
            hs = evaluate(self._ai_hands[i])[0] / 9.0
            po = self._cur_bet / max(1, self._pot) if self._cur_bet > 0 else 0.0
            action = decide(hs, po, 'post_flop', self.difficulty, p)
            self._ai_queue.append((i, p, action))

        self._ai_prev_phase   = self._phase
        self._ai_queue_idx    = 0
        self._ai_action_start = pygame.time.get_ticks()
        self._phase           = 'ai_turn'

        if self._ai_queue:
            self._play_ai_action_sound(self._ai_queue[0][2])

    def _play_ai_action_sound(self, action: str) -> None:
        if action == 'fold':
            sound.play('fold')
        elif action == 'raise':
            sound.play('raise')
        elif action == 'call':
            sound.play('chip_bet')
        elif action == 'check':
            sound.play('check')

    def _apply_ai_pending(self) -> None:
        """Apply all pre-computed AI actions and advance the hand."""
        for i, p, action in self._ai_queue:
            if action == 'fold':
                self._ai_active[i] = False
                self._fire_dialogue_from('lose_big', i)
            elif action in ('call', 'check'):
                cost = min(self._cur_bet, self._ai_stacks[i])
                self._ai_stacks[i] -= cost
                self._pot += cost
            elif action in ('raise', 'all_in'):
                raise_amt = _RAISE_STEP if action == 'raise' else self._ai_stacks[i]
                new_bet   = self._cur_bet + raise_amt
                cost      = min(new_bet, self._ai_stacks[i])
                self._ai_stacks[i] -= cost
                self._pot     += cost
                self._cur_bet  = new_bet
                if action == 'raise':
                    sound.play('raise')

        # If all opponents have folded, player wins immediately
        active = [i for i in range(self._num_ai) if self._ai_active[i]]
        if not active:
            sound.stop_music()
            sound.play('win_big')
            self.balance     += self._pot
            self._result_msg  = f'All opponents folded!  You win ${self._pot}.'
            self._pot         = 0
            self._phase       = 'result'
            self._message     = ''
            return

        now = pygame.time.get_ticks()
        if self._ai_prev_phase == 'bet1':
            self._cur_bet             = 0
            self._phase               = 'draw'
            self._message             = 'Click cards to discard, then Draw'
            self._phase_banner_until  = now + 800
            self._phase_banner_text   = 'DRAW PHASE'
        elif self._ai_prev_phase == 'bet2':
            self._resolve_showdown()
            if self._phase != 'result':
                self._your_turn_until = now + 700

    # ------------------------------------------------------------------
    # Draw and showdown
    # ------------------------------------------------------------------

    def _do_draw(self) -> None:
        # Record which indices are being replaced for animation
        self._draw_indices = [i for i in range(5) if self._marked[i]]

        # Replace player cards now (shown face-down until animation reveals them)
        for i in self._draw_indices:
            if len(self._deck) > 0:
                self._hand[i] = self._deck.deal(1)[0]

        # AI draws
        for i, p in enumerate(self._opponents):
            if not self._ai_active[i]:
                continue
            hs = evaluate(self._ai_hands[i])[0] / 9.0
            n_discard = self._ai_draw_count(hs)
            for _ in range(n_discard):
                if len(self._deck) > 0:
                    worst = min(range(5), key=lambda j: self._ai_hands[i][j].rank)
                    self._ai_hands[i][worst] = self._deck.deal(1)[0]

        if not self._draw_indices:
            # Kept all 5 — no animation needed, go straight to bet2
            self._marked = [False] * 5
            now = pygame.time.get_ticks()
            self._cur_bet            = 0
            self._phase              = 'bet2'
            self._message            = 'Round 2 — Bet or check'
            self._phase_banner_until = now + 600
            self._phase_banner_text  = 'BET ROUND 2'
            self._raise_amt          = _RAISE_STEP
        else:
            # Start card-flip animation for replaced cards
            self._draw_revealed = 0
            self._draw_next_at  = pygame.time.get_ticks() + 300
            self._phase         = 'drawing'

    def _resolve_showdown(self) -> None:
        sound.stop_music()
        player_score = evaluate(self._hand)
        winner       = 'player'
        best_score   = player_score
        for i in range(self._num_ai):
            if not self._ai_active[i]:
                continue
            ai_score = evaluate(self._ai_hands[i])
            if ai_score > best_score:
                best_score = ai_score
                winner     = i

        # Build hand summary (item 1)
        self._result_hand_lines = [f'You: {HAND_NAMES[player_score[0]]}']
        for i in range(self._num_ai):
            if not self._ai_active[i]:
                self._result_hand_lines.append(f'{self._opponents[i].name}: (folded)')
            else:
                s = evaluate(self._ai_hands[i])
                self._result_hand_lines.append(
                    f'{self._opponents[i].name}: {HAND_NAMES[s[0]]}')

        if winner == 'player':
            self.balance     += self._pot
            self._result_msg  = f'You win!  {HAND_NAMES[player_score[0]]} — +${self._pot}'
            sound.play('win_big')
            self._fire_dialogue('lose_big')
        else:
            self._ai_stacks[winner] += self._pot
            ai_score = evaluate(self._ai_hands[winner])
            self._result_msg = (
                f'{self._opponents[winner].name} wins with '
                f'{HAND_NAMES[ai_score[0]]}!'
            )
            sound.play('lose')
            self._fire_dialogue_from('win_pot', winner)
        self._pot     = 0
        self._phase   = 'result'
        self._message = ''

    def _ai_draw_count(self, hs: float) -> int:
        if hs >= 0.6:
            return 0
        if hs >= 0.3:
            return 1
        return random.randint(2, 3)

    # ------------------------------------------------------------------
    # Dialogue helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        self.screen.fill(_FELT)
        title = self._font.render('5-CARD DRAW', True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, 40)))

        bal = self._small.render(
            f'Balance: ${self.balance:,}  Pot: ${self._pot:,}', True, _WHITE)
        self.screen.blit(bal, bal.get_rect(center=(self._w // 2, 75)))

        for i, p in enumerate(self._opponents):
            sx    = self._opp_xs[i]
            color = _WHITE if self._ai_active[i] else _GRAY
            name_t = self._small.render(p.name, True, color)
            self.screen.blit(name_t, name_t.get_rect(center=(sx, 110)))
            self.screen.blit(
                self._small.render(f'${self._ai_stacks[i]:,}', True, color),
                self._small.render(f'${self._ai_stacks[i]:,}', True, color)
                    .get_rect(center=(sx, 130)))
            if self._ai_active[i] and self._ai_hands[i]:
                if self._phase == 'result':
                    for j in range(5):
                        bx = sx - 2 * (CARD_W // 2 + 4) + j * (CARD_W // 2 + 4)
                        draw_card(self.screen, self._ai_hands[i][j], bx, 150, self._small)
                else:
                    for j in range(5):
                        bx = sx - 2 * (CARD_W // 2 + 4) + j * (CARD_W // 2 + 4)
                        draw_card_back(self.screen, bx, 150)
            # Hand name (or folded) below each AI's card area in result
            if self._phase == 'result':
                if self._ai_active[i] and self._ai_hands[i]:
                    ai_rank = evaluate(self._ai_hands[i])[0]
                    hl = self._small.render(HAND_NAMES[ai_rank], True, _WHITE)
                else:
                    hl = self._small.render('(folded)', True, _GRAY)
                self.screen.blit(hl, hl.get_rect(center=(sx, 150 + CARD_H + 16)))
            self._bubbles[i].draw(self.screen)

        # Player hand
        revealed_set = set(
            self._draw_indices[j] for j in range(self._draw_revealed)
        ) if self._phase == 'drawing' else set()

        for i, card in enumerate(self._hand):
            cx = self._card_xs[i]
            if self._phase == 'drawing':
                if i in self._draw_indices and i not in revealed_set:
                    draw_card_back(self.screen, cx, self._card_y)
                else:
                    draw_card(self.screen, card, cx, self._card_y, self._font)
            else:
                draw_card(self.screen, card, cx, self._card_y,
                          self._font, self._marked[i])

        if self._phase == 'draw':
            for i in range(5):
                label = 'DISCARD' if self._marked[i] else 'HOLD'
                color = _RED if self._marked[i] else _GREEN
                t = self._small.render(label, True, color)
                self.screen.blit(t, t.get_rect(center=self._hold_rects[i].center))

        # Live hand label below hold-rect row (all active phases except result/drawing)
        if self._hand and self._phase not in ('result', 'drawing'):
            rank = evaluate(self._hand)[0]
            ht = self._small.render(f'Your hand: {HAND_NAMES[rank]}', True, _GOLD)
            self.screen.blit(ht, ht.get_rect(
                center=(self._w // 2, self._card_y + CARD_H + 50)))

        # Back button
        pygame.draw.rect(self.screen, _GRAY, self._btn_back, border_radius=6)
        bt = self._small.render('← Menu', True, _WHITE)
        self.screen.blit(bt, bt.get_rect(center=self._btn_back.center))

        now = pygame.time.get_ticks()

        if self._phase in ('bet1', 'bet2'):
            self._draw_btn(self._btn_fold, 'Fold', _RED)
            if self._cur_bet == 0:
                self._draw_btn(self._btn_check, 'Check', _GREEN)
            else:
                self._draw_btn(self._btn_call, f'Call ${self._cur_bet}', _GREEN)
            self._draw_btn(self._btn_minus, '−', _GRAY)
            self._draw_btn(self._btn_raise, f'Raise ${self._raise_amt}', _GOLD)
            self._draw_btn(self._btn_plus,  '+', _GRAY)
            self._draw_btn(self._btn_allin, 'All In', _RED)

            if now < self._your_turn_until:
                self._draw_overlay_label('Your Turn', _GREEN, self._h // 2 - 20)
            if now < self._phase_banner_until:
                self._draw_phase_banner(self._phase_banner_text)

        elif self._phase == 'draw':
            self._draw_btn(self._btn_draw, 'Draw', _GREEN)
            if now < self._phase_banner_until:
                self._draw_phase_banner(self._phase_banner_text)

        elif self._phase == 'ai_turn':
            if self._ai_queue_idx < len(self._ai_queue):
                i, p, action = self._ai_queue[self._ai_queue_idx]
                elapsed = now - self._ai_action_start
                if elapsed < 500:
                    self._draw_overlay_label(f"{p.name}'s Turn", _WHITE, self._h // 2 - 20)
                else:
                    self._draw_overlay_label(
                        f'{p.name}: {_ACTION_LABELS.get(action, action)}',
                        _GOLD, self._h // 2 - 20)

        elif self._phase == 'result':
            # Player hand name below their cards
            if self._hand:
                player_rank = evaluate(self._hand)[0]
                ht = self._small.render(f'Your hand: {HAND_NAMES[player_rank]}', True, _GOLD)
                self.screen.blit(ht, ht.get_rect(
                    center=(self._w // 2, self._card_y + CARD_H + 18)))
            r = self._font.render(self._result_msg, True, _GOLD)
            r_rect = r.get_rect(center=(self._w // 2, self._card_y + CARD_H + 50))
            bg = r_rect.inflate(24, 12)
            pygame.draw.rect(self.screen, _BOX, bg, border_radius=8)
            pygame.draw.rect(self.screen, _GOLD, bg, 2, border_radius=8)
            self.screen.blit(r, r_rect)
            label = 'Game Over' if self.balance <= 0 else 'Next Hand'
            self._draw_btn(self._btn_next, label, _GRAY if self.balance <= 0 else _GREEN)

        if self._message and self._phase not in ('result',):
            msg_t = self._small.render(self._message, True, _WHITE)
            self.screen.blit(msg_t, msg_t.get_rect(center=(self._w // 2, self._h - 100)))

    def _draw_btn(self, rect: pygame.Rect, label: str, color: tuple) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        t = self._small.render(label, True, _WHITE if color != _GOLD else _DARK)
        self.screen.blit(t, t.get_rect(center=rect.center))

    def _draw_overlay_label(self, text: str, color: tuple, cy: int) -> None:
        t    = self._font.render(text, True, color)
        rect = t.get_rect(center=(self._w // 2, cy))
        bg   = rect.inflate(24, 10)
        pygame.draw.rect(self.screen, _BOX, bg, border_radius=8)
        pygame.draw.rect(self.screen, color, bg, 2, border_radius=8)
        self.screen.blit(t, rect)

    def _draw_phase_banner(self, text: str) -> None:
        t    = self._font_banner.render(text, True, _GOLD)
        rect = t.get_rect(center=(self._w // 2, self._h // 2))
        bg   = rect.inflate(60, 30)
        pygame.draw.rect(self.screen, _BOX, bg, border_radius=14)
        pygame.draw.rect(self.screen, _GOLD, bg, 3, border_radius=14)
        self.screen.blit(t, rect)
