import pygame

CARD_W = 80
CARD_H = 110

_CARD_BG = (255, 255, 255)
_CARD_BACK = (0, 80, 160)
_CARD_BACK_INNER = (0, 55, 110)
_RED = (200, 0, 0)
_BLACK = (20, 20, 20)
_SELECTED_BORDER = (255, 215, 0)
_UNSELECTED_BORDER = (180, 180, 180)

_SUIT_SYMBOLS = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}
_RANK_NAMES = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}


def draw_card(surface: pygame.Surface, card, x: int, y: int,
              font: pygame.font.Font, selected: bool = False) -> None:
    """Draw a face-up card. `card` is a core.cards.Card instance."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BG, rect, border_radius=6)
    border_color = _SELECTED_BORDER if selected else _UNSELECTED_BORDER
    pygame.draw.rect(surface, border_color, rect, 3 if selected else 1, border_radius=6)

    color = _RED if card.suit in ('H', 'D') else _BLACK
    rank_str = _RANK_NAMES.get(card.rank, str(card.rank))
    suit_str = _SUIT_SYMBOLS[card.suit]

    corner = font.render(f'{rank_str}{suit_str}', True, color)
    surface.blit(corner, (x + 5, y + 5))

    center_suit = font.render(suit_str, True, color)
    surface.blit(center_suit, center_suit.get_rect(center=(x + CARD_W // 2, y + CARD_H // 2)))


def draw_card_back(surface: pygame.Surface, x: int, y: int) -> None:
    """Draw a face-down card."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BACK, rect, border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=6)
    inner = pygame.Rect(x + 6, y + 6, CARD_W - 12, CARD_H - 12)
    pygame.draw.rect(surface, _CARD_BACK_INNER, inner, border_radius=4)
