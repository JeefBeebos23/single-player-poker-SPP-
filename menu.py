import pygame
from ui.components import Button, Slider, VolumeSlider
import core.sound as sound

_GOLD = (245, 200, 66)
_WHITE = (255, 255, 255)


class Menu:
    def __init__(self, screen: pygame.Surface, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height

        font_title = pygame.font.SysFont('Georgia', 56, bold=True)
        font_btn = pygame.font.SysFont('Georgia', 26)
        font_small = pygame.font.SysFont('Georgia', 20)
        self._font_small = font_small

        self._title = font_title.render('SINGLE PLAYER POKER', True, _GOLD)
        self._title_rect = self._title.get_rect(center=(width // 2, 110))

        cx = width // 2
        self._buttons = {
            'video_poker':    Button((cx - 160, 230, 320, 52), 'Video Poker',    font_btn),
            'holdem':         Button((cx - 160, 298, 320, 52), "Texas Hold'em",  font_btn),
            'five_card_draw': Button((cx - 160, 366, 320, 52), '5-Card Draw',    font_btn),
            'duel':           Button((cx - 160, 434, 320, 52), '1v1 Duel',       font_btn),
            'quit':           Button((cx - 160, 522, 320, 52), 'Quit',           font_btn),
        }
        self._slider = Slider(
            (cx - 160, 624, 320, 16), 0, 2, 1,
            font_small, ['Easy', 'Normal', 'Hard']
        )
        self._slider_music = VolumeSlider(
            (40, height - 46, 220, 16),
            sound.music_volume(), font_small, 'Music'
        )
        self._slider_sfx = VolumeSlider(
            (width - 260, height - 46, 220, 16),
            sound.sfx_volume(), font_small, 'SFX'
        )

    def handle_event(self, event: pygame.event.Event):
        """Returns (kind, value) tuple or None."""
        self._slider_music.handle_event(event)
        if self._slider_music.changed:
            self._slider_music.changed = False
            sound.set_music_volume(self._slider_music.value)

        self._slider_sfx.handle_event(event)
        if self._slider_sfx.changed:
            self._slider_sfx.changed = False
            sound.set_sfx_volume(self._slider_sfx.value)

        self._slider.handle_event(event)
        if self._slider.changed:
            self._slider.changed = False
            return ('difficulty', self._slider.value)

        for name, btn in self._buttons.items():
            if btn.handle_event(event):
                sound.play('click')
                if name == 'quit':
                    return ('quit', None)
                return ('play', name)
        return None

    def draw(self, balance: int, difficulty: int) -> None:
        if not self._slider._dragging:
            self._slider._value = float(difficulty)
        self.screen.blit(self._title, self._title_rect)

        bal_text = self._font_small.render(f'Balance: ${balance:,}', True, _GOLD)
        self.screen.blit(bal_text, bal_text.get_rect(center=(self.width // 2, 175)))

        for btn in self._buttons.values():
            btn.draw(self.screen)
        self._slider.draw(self.screen)
        self._slider_music.draw(self.screen)
        self._slider_sfx.draw(self.screen)
        sound.draw_debug_overlay(self.screen)
