import pygame

_BUTTON_COLOR = (30, 100, 60)
_BUTTON_HOVER = (45, 140, 80)
_BUTTON_TEXT = (255, 255, 255)
_GOLD = (245, 200, 66)
_SLIDER_BG = (20, 70, 40)

class Button:
    def __init__(self, rect: tuple, label: str, font: pygame.font.Font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True on left-click."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface, selected: bool = False) -> None:
        if selected:
            color = _GOLD
            text_color = (20, 20, 20)
        else:
            color = _BUTTON_HOVER if self._hovered else _BUTTON_COLOR
            text_color = _BUTTON_TEXT
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, _GOLD, self.rect, 2, border_radius=8)
        text = self.font.render(self.label, True, text_color)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Slider:
    """Integer-step slider. Snaps to nearest integer on release."""

    def __init__(self, rect: tuple, min_val: int, max_val: int,
                 initial: int, font: pygame.font.Font, labels: list[str]):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self._value = float(initial)
        self.font = font
        self.labels = labels
        self._dragging = False
        self.changed = False  # Set True when snapped value changes; caller clears it

    @property
    def value(self) -> int:
        return round(self._value)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            if self._dragging:
                self._dragging = False
                self.changed = True
        if event.type == pygame.MOUSEMOTION and self._dragging:
            ratio = (event.pos[0] - self.rect.x) / max(self.rect.width, 1)
            ratio = max(0.0, min(1.0, ratio))
            self._value = self.min_val + ratio * (self.max_val - self.min_val)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, _SLIDER_BG, self.rect, border_radius=4)
        ratio = (self._value - self.min_val) / max(self.max_val - self.min_val, 1)
        hx = int(self.rect.x + ratio * self.rect.width)
        handle = pygame.Rect(hx - 10, self.rect.y - 6, 20, self.rect.height + 12)
        pygame.draw.rect(surface, _GOLD, handle, border_radius=4)
        label = self.labels[self.value] if self.labels else str(self.value)
        text = self.font.render(f'Difficulty: {label}', True, (255, 255, 255))
        surface.blit(text, (self.rect.x, self.rect.y - 28))


class VolumeSlider:
    """Continuous float slider (0.0–1.0) for volume control."""

    def __init__(self, rect: tuple, initial: float, font: pygame.font.Font, label: str):
        self.rect = pygame.Rect(rect)
        self._value = max(0.0, min(1.0, float(initial)))
        self.font = font
        self.label = label
        self._dragging = False
        self.changed = False

    @property
    def value(self) -> float:
        return self._value

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
                self._set_from_x(event.pos[0])
        if event.type == pygame.MOUSEBUTTONUP:
            self._dragging = False
        if event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_from_x(event.pos[0])

    def _set_from_x(self, mouse_x: int) -> None:
        ratio = (mouse_x - self.rect.x) / max(self.rect.width, 1)
        self._value = max(0.0, min(1.0, ratio))
        self.changed = True

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, _SLIDER_BG, self.rect, border_radius=4)
        hx = int(self.rect.x + self._value * self.rect.width)
        handle = pygame.Rect(hx - 10, self.rect.y - 6, 20, self.rect.height + 12)
        pygame.draw.rect(surface, _GOLD, handle, border_radius=4)
        pct = int(self._value * 100)
        text = self.font.render(f'{self.label}: {pct}%', True, (255, 255, 255))
        surface.blit(text, (self.rect.x, self.rect.y - 28))
