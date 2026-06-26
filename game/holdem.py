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
_BOX   = (8, 30, 15)

_SMALL_BLIND  = 5
_BIG_BLIND    = 10
_RAISE_STEP   = 10   # minimum / increment for raise
_N_AI         = 2
_AI_ACTION_MS = 2000  # ms to display each individual AI action

_PHASE_LABELS = {
    'pre_flop': 'Pre-Flop',
    'flop':     'Flop',
    'turn':     'Turn',
    'river':    'River',
}

_ACTION_LABELS = {
    'fold':   'Folds',
    'check':  'Checks',
    'call':   'Calls',
    'raise':  'Raises',
    'all_in': 'All In!',
}


class HoldEm:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 balance: int, difficulty: int, modifiers: ModifierSet,
                 num_ai: int = 2):
        self.screen = screen
        self.clock  = clock
        self.balance = balance
        self.difficulty = difficulty
        self._w, self._h = screen.get_size()
        self._font        = pygame.font.SysFont('Georgia', 24, bold=True)
        self._font_banner = pygame.font.SysFont('Georgia', 40, bold=True)
        self._small       = pygame.font.SysFont('Georgia', 18)

        self._num_ai    = num_ai
        self._opponents = generate_opponents(num_ai, difficulty)
        self._ai_stacks = [1000] * num_ai
        self._ai_active = [True]  * num_ai
        self._ai_hands: list[list[Card]] = [[] for _ in range(num_ai)]

        if num_ai == 1:
            self._opp_xs = [self._w // 2]
            bubble_xs    = [self._w // 2]
        else:
            self._opp_xs = [self._w // 4, 3 * self._w // 4]
            bubble_xs    = [self._w // 4, 3 * self._w // 4]
        self._bubbles = [SpeechBubble(x, 80, self._small) for x in bubble_xs]

        self._hole:      list[Card] = []
        self._community: list[Card] = []
        self._pot        = 0
        self._cur_bet    = 0
        self._hand_start_balance:    int       = 0
        self._hand_start_ai_stacks:  list[int] = [0] * num_ai
        self._raise_amt  = _RAISE_STEP
        self._phase      = 'pre_flop'
        self._phase_idx  = 0
        self._message    = ''
        self._result_msg        = ''
        self._result_hand_lines: list[str] = []
        self._game_phase = 'start'
        self._running    = True

        # AI sequential animation state
        self._ai_queue:        list = []
        self._ai_queue_idx:    int  = 0
        self._ai_action_start: int  = 0

        # Transition / banner timers
        self._phase_banner_until: int = 0   # show FLOP / TURN / RIVER label
        self._your_turn_until:    int = 0   # show "Your Turn" after AI acts

        # Raise-response state: player must respond to an AI raise
        self._player_must_respond: bool = False
        self._street_raise_count:  int  = 0

        # Raise amount typing state
        self._typing_raise: bool = False
        self._raise_input:  str  = ''

        # Layout
        comm_y = self._h // 2 - CARD_H // 2
        comm_x = (self._w - (5 * CARD_W + 4 * 10)) // 2
        self._comm_positions = [(comm_x + i * (CARD_W + 10), comm_y) for i in range(5)]
        self._hole_xs = [self._w // 2 - CARD_W - 5, self._w // 2 + 5]
        self._hole_y  = self._h // 2 + CARD_H // 2 + 30

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
        self._btn_back  = pygame.Rect(30, 30, 100, 36)
        self._btn_next  = pygame.Rect(cx - 75, by, 150, 40)

        self._start_hand()

    # ------------------------------------------------------------------
    # Hand lifecycle
    # ------------------------------------------------------------------

    def _start_hand(self) -> None:
        sound.play_music('gameplay')
        self._pot = 0
        self._ai_active = [True] * self._num_ai
        self._raise_amt = _RAISE_STEP
        self._result_hand_lines = []

        # Snapshot starting chips so we can display per-player bets
        self._hand_start_balance   = self.balance
        self._hand_start_ai_stacks = list(self._ai_stacks)

        self._deck = Deck()
        self._deck.shuffle()

        sb = min(_SMALL_BLIND, self._ai_stacks[0])
        self._ai_stacks[0] -= sb
        self._pot = sb
        if self._num_ai >= 2:
            bb = min(_BIG_BLIND, self._ai_stacks[1])
            self._ai_stacks[1] -= bb
            self._pot += bb
            self._cur_bet = _BIG_BLIND
        else:
            self._cur_bet = _SMALL_BLIND
        sound.play('chip_bet')

        self._hole = self._deck.deal(2)
        sound.play('deal')
        for i in range(self._num_ai):
            self._ai_hands[i] = self._deck.deal(2)

        self._community       = []
        self._phase_idx       = 0
        self._phase           = 'pre_flop'
        self._game_phase      = 'betting'
        self._message         = f'Pre-Flop — call ${_BIG_BLIND} or raise'
        self._ai_queue        = []
        self._ai_queue_idx    = 0
        self._phase_banner_until  = 0
        self._your_turn_until     = 0
        self._player_must_respond = False
        self._street_raise_count  = 0

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------

    def run(self) -> int:
        while self._running:
            for event in pygame.event.get():
                sound.handle_event(event)
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    elif self._typing_raise:
                        self._handle_raise_key(event)
                    elif (event.unicode.isdigit()
                          and self._game_phase == 'betting'):
                        self._typing_raise = True
                        self._raise_input = event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._game_phase != 'ai_turn':
                        self._handle_click(event.pos)

            # Advance sequential AI animation
            if self._game_phase == 'ai_turn':
                now = pygame.time.get_ticks()
                if len(self._ai_queue) == 0:
                    self._apply_ai_pending()
                elif now - self._ai_action_start >= _AI_ACTION_MS:
                    self._ai_queue_idx += 1
                    if self._ai_queue_idx >= len(self._ai_queue):
                        self._apply_ai_pending()
                    else:
                        self._ai_action_start = now
                        self._play_ai_action_sound(self._ai_queue[self._ai_queue_idx][2])

            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.balance

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _handle_raise_key(self, event: pygame.event.Event) -> None:
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._commit_raise_input()
        elif event.key == pygame.K_ESCAPE:
            self._typing_raise = False
            self._raise_input = ''
        elif event.key == pygame.K_BACKSPACE:
            self._raise_input = self._raise_input[:-1]
        elif event.unicode.isdigit():
            self._raise_input += event.unicode

    def _commit_raise_input(self) -> None:
        try:
            amount = int(self._raise_input)
            self._raise_amt = max(_RAISE_STEP, min(amount, self.balance))
        except ValueError:
            pass
        self._typing_raise = False
        self._raise_input = ''

    def _handle_click(self, pos: tuple) -> None:
        if self._typing_raise and not self._btn_raise.collidepoint(pos):
            self._commit_raise_input()

        if self._btn_back.collidepoint(pos):
            self._running = False
            return

        # Block clicks while a phase banner is animating
        if pygame.time.get_ticks() < self._phase_banner_until:
            return

        if self._game_phase == 'betting':
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
                if self._typing_raise:
                    self._commit_raise_input()
                self._player_raise()
            elif self._btn_allin.collidepoint(pos):
                self._player_all_in()

        elif self._game_phase == 'result':
            if self._btn_next.collidepoint(pos):
                if self.balance <= 0:
                    self._running = False
                else:
                    self._start_hand()

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def _player_fold(self) -> None:
        self._player_must_respond = False
        sound.play('fold')
        sound.stop_music()
        active = [i for i in range(self._num_ai) if self._ai_active[i]]
        if active:
            share = self._pot // len(active)
            for i in active:
                self._ai_stacks[i] += share
        self._pot = 0
        self._result_msg = 'You folded.'
        self._game_phase = 'result'
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
        if self._player_must_respond:
            # Calling an AI raise — the street ends here
            self._player_must_respond = False
            self._next_phase()
            if self._game_phase != 'result':
                self._game_phase      = 'betting'
                self._your_turn_until = pygame.time.get_ticks() + 700
        else:
            self._start_ai_turn()

    def _player_raise(self) -> None:
        self._player_must_respond = False  # AI will handle next
        sound.play('raise')
        new_bet = self._cur_bet + self._raise_amt
        cost = min(new_bet, self.balance)
        self.balance -= cost
        self._pot += cost
        self._cur_bet = new_bet
        self._fire_dialogue('player_raises')
        self._start_ai_turn()

    def _player_all_in(self) -> None:
        self._player_must_respond = False
        sound.play('raise')
        cost = self.balance
        self.balance = 0
        self._pot += cost
        self._cur_bet = self._cur_bet + cost
        self._fire_dialogue('player_raises')
        self._start_ai_turn()

    # ------------------------------------------------------------------
    # AI turn (sequential animation)
    # ------------------------------------------------------------------

    def _start_ai_turn(self) -> None:
        """Pre-compute all AI decisions for this round and start animation."""
        self._ai_queue = []
        for i, p in enumerate(self._opponents):
            if not self._ai_active[i]:
                continue
            all_cards = self._ai_hands[i] + self._community
            if len(all_cards) >= 5:
                hs = best_hand(all_cards)[0] / 9.0
            elif len(all_cards) >= 2:
                hs = max(c.rank for c in self._ai_hands[i]) / 14.0
            else:
                hs = 0.0
            po = self._cur_bet / max(1, self._pot) if self._cur_bet > 0 else 0.0
            action = decide(hs, po, self._phase, self.difficulty, p)
            if action == 'fold' and self._cur_bet == 0:
                action = 'check'  # can't fold for free
            self._ai_queue.append((i, p, action))

        self._ai_queue_idx    = 0
        self._ai_action_start = pygame.time.get_ticks()
        self._game_phase      = 'ai_turn'

        if self._ai_queue:
            self._play_ai_action_sound(self._ai_queue[0][2])

    def _play_ai_action_sound(self, action: str) -> None:
        if action == 'fold':
            sound.play('fold')
        elif action == 'raise':
            sound.play('raise')
        elif action in ('call',):
            sound.play('chip_bet')
        elif action == 'check':
            sound.play('check')

    def _apply_ai_pending(self) -> None:
        """Apply all pre-computed AI actions and advance the hand."""
        bet_before = self._cur_bet
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
                self._pot  += cost
                self._cur_bet = new_bet

        active = [i for i in range(self._num_ai) if self._ai_active[i]]
        if not active:
            sound.stop_music()
            sound.play('win_big')
            sound.play_music_once('celebration')
            self.balance += self._pot
            self._result_msg = f'All opponents folded!  You win ${self._pot}.'
            self._pot = 0
            self._game_phase = 'result'
            self._message = ''
            return

        # If AI raised and player hasn't had a response chance this street yet
        # Skip if player is already all-in (balance=0) — they can't respond
        if self._cur_bet > bet_before and self._street_raise_count == 0 and self.balance > 0:
            self._street_raise_count  = 1
            self._player_must_respond = True
            self._game_phase      = 'betting'
            self._message         = f'Raised to ${self._cur_bet} — call, raise, or fold'
            self._your_turn_until = pygame.time.get_ticks() + 700
            return

        self._next_phase()
        # Only switch to betting if _next_phase didn't end the hand
        if self._game_phase != 'result':
            self._game_phase      = 'betting'
            self._your_turn_until = pygame.time.get_ticks() + 700

    # ------------------------------------------------------------------
    # Phase transitions
    # ------------------------------------------------------------------

    def _next_phase(self) -> None:
        self._street_raise_count  = 0
        self._player_must_respond = False
        self._raise_amt  = _RAISE_STEP
        self._phase_idx += 1
        self._cur_bet    = 0
        now              = pygame.time.get_ticks()
        if self._phase_idx == 1:
            self._community = self._deck.deal(3)
            self._phase     = 'flop'
            self._phase_banner_until = now + 1100
        elif self._phase_idx == 2:
            self._community += self._deck.deal(1)
            self._phase      = 'turn'
            self._phase_banner_until = now + 900
        elif self._phase_idx == 3:
            self._community += self._deck.deal(1)
            self._phase      = 'river'
            self._phase_banner_until = now + 900
        else:
            self._showdown()
            return
        self._message = f'{_PHASE_LABELS[self._phase]} — check or bet'

    def _showdown(self) -> None:
        sound.stop_music()
        player_all   = self._hole + self._community
        player_score = best_hand(player_all)
        winner       = 'player'
        best_score   = player_score

        for i in range(self._num_ai):
            if not self._ai_active[i]:
                continue
            ai_score = best_hand(self._ai_hands[i] + self._community)
            if ai_score > best_score:
                best_score = ai_score
                winner     = i

        # Build per-player hand summary for result display (item 1)
        self._result_hand_lines = []
        player_hand_name = HAND_NAMES[player_score[0]]
        self._result_hand_lines.append(f'You: {player_hand_name}')
        for i in range(self._num_ai):
            if not self._ai_active[i]:
                self._result_hand_lines.append(f'{self._opponents[i].name}: (folded)')
            else:
                s = best_hand(self._ai_hands[i] + self._community)
                self._result_hand_lines.append(
                    f'{self._opponents[i].name}: {HAND_NAMES[s[0]]}')

        if winner == 'player':
            self.balance    += self._pot
            self._result_msg = f'You win!  {player_hand_name} — +${self._pot}'
            sound.play('win_big')
            sound.play_music_once('celebration')
            self._fire_dialogue('lose_big')
        else:
            self._ai_stacks[winner] += self._pot
            ai_score = best_hand(self._ai_hands[winner] + self._community)
            self._result_msg = (
                f'{self._opponents[winner].name} wins with '
                f'{HAND_NAMES[ai_score[0]]}!'
            )
            self._fire_dialogue_from('win_pot', winner)

        self._pot        = 0
        self._game_phase = 'result'
        self._message    = ''

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
        title = self._font.render("TEXAS HOLD'EM", True, _GOLD)
        self.screen.blit(title, title.get_rect(center=(self._w // 2, 40)))

        player_bet = self._hand_start_balance - self.balance
        bal = self._small.render(
            f'Balance: ${self.balance:,}   Pot: ${self._pot:,}   Bet: ${player_bet:,}',
            True, _WHITE)
        self.screen.blit(bal, bal.get_rect(center=(self._w // 2, 75)))

        # Opponents
        for i, p in enumerate(self._opponents):
            sx    = self._opp_xs[i]
            color = _WHITE if self._ai_active[i] else _GRAY
            ai_bet = self._hand_start_ai_stacks[i] - self._ai_stacks[i]
            self.screen.blit(
                self._small.render(p.name, True, color),
                self._small.render(p.name, True, color).get_rect(center=(sx, 110)))
            self.screen.blit(
                self._small.render(f'${self._ai_stacks[i]:,}  (Bet: ${ai_bet:,})', True, color),
                self._small.render(f'${self._ai_stacks[i]:,}  (Bet: ${ai_bet:,})', True, color)
                    .get_rect(center=(sx, 130)))
            if self._ai_active[i] and self._ai_hands[i]:
                for j in range(2):
                    bx = sx - CARD_W - 4 + j * (CARD_W + 8)
                    if self._game_phase == 'result':
                        draw_card(self.screen, self._ai_hands[i][j], bx, 148, self._font)
                    else:
                        draw_card_back(self.screen, bx, 148)
            self._bubbles[i].draw(self.screen)

        # Community cards
        for idx, (x, y) in enumerate(self._comm_positions):
            if idx < len(self._community):
                draw_card(self.screen, self._community[idx], x, y, self._font)

        # Hole cards
        for i, card in enumerate(self._hole):
            draw_card(self.screen, card, self._hole_xs[i], self._hole_y, self._font)

        # Live hand label — always visible once ≥5 cards are available
        if self._hole and self._game_phase not in ('result',) and \
                len(self._hole + self._community) >= 5:
            rank, _ = best_hand(self._hole + self._community)
            ht = self._small.render(f'Your hand: {HAND_NAMES[rank]}', True, _GOLD)
            self.screen.blit(ht, ht.get_rect(
                center=(self._w // 2, self._hole_y + CARD_H + 18)))

        # Phase label (above community cards)
        phase_label = _PHASE_LABELS.get(self._phase, '')
        if phase_label and self._game_phase in ('betting', 'ai_turn'):
            pt = self._small.render(phase_label, True, _GOLD)
            self.screen.blit(
                pt,
                pt.get_rect(center=(self._w // 2,
                                    self._h // 2 - CARD_H // 2 - 25)))

        # Back button
        pygame.draw.rect(self.screen, _GRAY, self._btn_back, border_radius=6)
        self.screen.blit(
            self._small.render('← Menu', True, _WHITE),
            self._small.render('← Menu', True, _WHITE)
                .get_rect(center=self._btn_back.center))

        # ---- game-phase-specific UI ----
        now = pygame.time.get_ticks()

        if self._game_phase == 'betting':
            self._draw_btn(self._btn_fold, 'Fold', _RED)
            if self._cur_bet == 0:
                self._draw_btn(self._btn_check, 'Check', _GREEN)
            else:
                self._draw_btn(self._btn_call, f'Call ${self._cur_bet}', _GREEN)
            self._draw_btn(self._btn_minus, '−', _GRAY)
            if self._typing_raise:
                self._draw_btn(self._btn_raise,
                               f'${self._raise_input}|' if self._raise_input else '$|',
                               _GOLD)
            else:
                self._draw_btn(self._btn_raise, f'Raise ${self._raise_amt}', _GOLD)
            self._draw_btn(self._btn_plus,  '+', _GRAY)
            self._draw_btn(self._btn_allin, 'All In', _RED)

            # "Your Turn" flash after AI acts
            if now < self._your_turn_until:
                self._draw_overlay_label('Your Turn', _GREEN, self._h // 2 - 20)

            # Phase transition banner (FLOP / TURN / RIVER)
            if now < self._phase_banner_until:
                self._draw_phase_banner(_PHASE_LABELS.get(self._phase, '').upper())

        elif self._game_phase == 'ai_turn':
            if self._ai_queue_idx < len(self._ai_queue):
                i, p, action = self._ai_queue[self._ai_queue_idx]
                elapsed = now - self._ai_action_start
                if elapsed < 500:
                    label = f"{p.name}'s Turn"
                    self._draw_overlay_label(label, _WHITE, self._h // 2 - 20)
                else:
                    label = f'{p.name}: {_ACTION_LABELS.get(action, action)}'
                    self._draw_overlay_label(label, _GOLD, self._h // 2 - 20)

        elif self._game_phase == 'result':
            r_y = self._hole_y + CARD_H + 30
            r   = self._font.render(self._result_msg, True, _GOLD)
            r_rect = r.get_rect(center=(self._w // 2, r_y))
            bg = r_rect.inflate(24, 12)
            pygame.draw.rect(self.screen, _BOX, bg, border_radius=8)
            pygame.draw.rect(self.screen, _GOLD, bg, 2, border_radius=8)
            self.screen.blit(r, r_rect)

            # Per-player hand list (item 1)
            for k, line in enumerate(self._result_hand_lines):
                ht = self._small.render(line, True, _WHITE)
                self.screen.blit(ht, ht.get_rect(
                    center=(self._w // 2, r_y + 30 + k * 22)))

            label = 'Game Over' if self.balance <= 0 else 'Next Hand'
            col   = _GRAY if self.balance <= 0 else _GREEN
            self._draw_btn(self._btn_next, label, col)

        # Bottom message (only during active play)
        if self._game_phase not in ('result',) and self._message:
            msg_t = self._small.render(self._message, True, _WHITE)
            self.screen.blit(msg_t,
                             msg_t.get_rect(center=(self._w // 2, self._h - 100)))


    def _draw_btn(self, rect: pygame.Rect, label: str, color: tuple) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        t = self._small.render(label, True, _WHITE if color != _GOLD else _DARK)
        self.screen.blit(t, t.get_rect(center=rect.center))

    def _draw_overlay_label(self, text: str, color: tuple, cy: int) -> None:
        """Draw a text label with a dark backing box centered at (cx, cy)."""
        t    = self._font.render(text, True, color)
        rect = t.get_rect(center=(self._w // 2, cy))
        bg   = rect.inflate(24, 10)
        pygame.draw.rect(self.screen, _BOX, bg, border_radius=8)
        pygame.draw.rect(self.screen, color, bg, 2, border_radius=8)
        self.screen.blit(t, rect)

    def _draw_phase_banner(self, text: str) -> None:
        """Draw a large centred phase transition banner."""
        t    = self._font_banner.render(text, True, _GOLD)
        rect = t.get_rect(center=(self._w // 2, self._h // 2))
        bg   = rect.inflate(60, 30)
        pygame.draw.rect(self.screen, _BOX, bg, border_radius=14)
        pygame.draw.rect(self.screen, _GOLD, bg, 3, border_radius=14)
        self.screen.blit(t, rect)
