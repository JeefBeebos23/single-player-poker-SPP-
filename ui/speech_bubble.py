import time
import pygame

_GOLD  = (245, 200, 66)
_DARK  = (30, 30, 30)
_DURATION = 3.0  # seconds a bubble stays visible

class SpeechBubble:
    """
    Renders a speech bubble above a fixed (x, y) seat position.
    Call show(text) to display; call draw(surface) each frame.
    Automatically fades out after _DURATION seconds.
    """
    def __init__(self, x: int, y: int, font: pygame.font.Font):
        self._x = x
        self._y = y
        self._font = font
        self._text = ''
        self._expires = 0.0

    def show(self, text: str) -> None:
        self._text = text
        self._expires = time.monotonic() + _DURATION

    def draw(self, surface: pygame.Surface) -> None:
        if not self._text or time.monotonic() >= self._expires:
            return
        remaining = self._expires - time.monotonic()
        alpha = min(255, int(255 * remaining / 0.5)) if remaining < 0.5 else 255

        text_surf = self._font.render(self._text, True, _DARK)
        pad = 8
        w = text_surf.get_width() + pad * 2
        h = text_surf.get_height() + pad * 2
        bx = self._x - w // 2
        by = self._y - h - 10

        bubble = pygame.Surface((w, h), pygame.SRCALPHA)
        bubble.fill((255, 255, 220, alpha))
        pygame.draw.rect(bubble, (*_GOLD, alpha), bubble.get_rect(), 2, border_radius=6)
        bubble.blit(text_surf, (pad, pad))
        surface.blit(bubble, (bx, by))

    @property
    def active(self) -> bool:
        return bool(self._text) and time.monotonic() < self._expires
