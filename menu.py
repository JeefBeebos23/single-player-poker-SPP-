import pygame
from ui.components import Button, VolumeSlider
from core.window import S
import core.sound as sound

_GOLD = (245, 200, 66)
_WHITE = (255, 255, 255)


class Menu:
    def __init__(self, screen: pygame.Surface, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height

        font_title = pygame.font.SysFont('Georgia', S(56), bold=True)
        font_btn   = pygame.font.SysFont('Georgia', S(26))
        font_small = pygame.font.SysFont('Georgia', S(20))
        self._font_small = font_small

        self._title = font_title.render('SINGLE PLAYER POKER', True, _GOLD)
        self._title_rect = self._title.get_rect(center=(width // 2, S(110)))

        cx = width // 2
        self._buttons = {
            'video_poker':    Button((cx - S(160), S(230), S(320), S(52)), 'Video Poker',    font_btn),
            'holdem':         Button((cx - S(160), S(298), S(320), S(52)), "Texas Hold'em",  font_btn),
            'five_card_draw': Button((cx - S(160), S(366), S(320), S(52)), '5-Card Draw',    font_btn),
            'duel':           Button((cx - S(160), S(434), S(320), S(52)), '1v1 Duel',       font_btn),
            'quit':           Button((cx - S(160), S(522), S(320), S(52)), 'Quit',           font_btn),
        }

        self._diff_buttons = [
            Button((cx - S(160), S(616), S(100), S(36)), 'Easy',   font_small),
            Button((cx - S(50),  S(616), S(100), S(36)), 'Normal', font_small),
            Button((cx + S(60),  S(616), S(100), S(36)), 'Hard',   font_small),
        ]

        self._slider_music = VolumeSlider(
            (S(40), height - S(46), S(220), S(16)),
            sound.music_volume(), font_small, 'Music'
        )
        self._slider_sfx = VolumeSlider(
            (width - S(260), height - S(46), S(220), S(16)),
            sound.sfx_volume(), font_small, 'SFX'
        )

    def handle_event(self, event: pygame.event.Event):
        self._slider_music.handle_event(event)
        if self._slider_music.changed:
            self._slider_music.changed = False
            sound.set_music_volume(self._slider_music.value)

        self._slider_sfx.handle_event(event)
        if self._slider_sfx.changed:
            self._slider_sfx.changed = False
            sound.set_sfx_volume(self._slider_sfx.value)

        for i, btn in enumerate(self._diff_buttons):
            if btn.handle_event(event):
                sound.play('click')
                return ('difficulty', i)

        for name, btn in self._buttons.items():
            if btn.handle_event(event):
                sound.play('click')
                if name == 'quit':
                    return ('quit', None)
                return ('play', name)
        return None

    def draw(self, balance: int, difficulty: int) -> None:
        self.screen.blit(self._title, self._title_rect)

        bal_text = self._font_small.render(f'Balance: ${balance:,}', True, _GOLD)
        self.screen.blit(bal_text, bal_text.get_rect(center=(self.width // 2, S(175))))

        for btn in self._buttons.values():
            btn.draw(self.screen)

        diff_label = self._font_small.render('Difficulty:', True, _WHITE)
        self.screen.blit(diff_label, diff_label.get_rect(
            center=(self.width // 2, S(596))))
        for i, btn in enumerate(self._diff_buttons):
            btn.draw(self.screen, selected=(i == difficulty))

        self._slider_music.draw(self.screen)
        self._slider_sfx.draw(self.screen)
