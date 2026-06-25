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

_RANK_NAMES = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}


def _draw_suit_shape(surface: pygame.Surface, suit: str,
                     cx: int, cy: int, r: int, color: tuple) -> None:
    """Draw a suit icon centered at (cx, cy); r is approx half-width."""
    if r < 2:
        return
    if suit == 'D':
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surface, color, pts)
    elif suit == 'H':
        cr = max(1, r * 6 // 10)
        o  = max(1, r * 4 // 10)
        pygame.draw.circle(surface, color, (cx - o, cy - o), cr)
        pygame.draw.circle(surface, color, (cx + o, cy - o), cr)
        pygame.draw.polygon(surface, color,
                            [(cx - r, cy), (cx, cy + r), (cx + r, cy)])
    elif suit == 'S':
        cr = max(1, r * 6 // 10)
        o  = max(1, r * 4 // 10)
        pygame.draw.circle(surface, color, (cx - o, cy + o), cr)
        pygame.draw.circle(surface, color, (cx + o, cy + o), cr)
        pygame.draw.polygon(surface, color,
                            [(cx - r, cy), (cx, cy - r), (cx + r, cy)])
        sw = max(1, r // 3)
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - sw, cy + o, sw * 2, max(1, r // 2)))
    elif suit == 'C':
        cr = max(1, r * 5 // 10)
        pygame.draw.circle(surface, color, (cx, cy - cr // 2), cr)
        pygame.draw.circle(surface, color, (cx - cr, cy + cr // 2), cr)
        pygame.draw.circle(surface, color, (cx + cr, cy + cr // 2), cr)
        sw = max(1, r // 3)
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - sw, cy + cr // 2, sw * 2, max(1, r // 2)))


def draw_card(surface: pygame.Surface, card, x: int, y: int,
              font: pygame.font.Font, selected: bool = False) -> None:
    """Draw a face-up card. `card` is a core.cards.Card instance."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BG, rect, border_radius=6)
    border_color = _SELECTED_BORDER if selected else _UNSELECTED_BORDER
    pygame.draw.rect(surface, border_color, rect, 3 if selected else 1, border_radius=6)

    color = _RED if card.suit in ('H', 'D') else _BLACK
    rank_str = _RANK_NAMES.get(card.rank, str(card.rank))

    # Corner: rank text + small suit shape
    rank_surf = font.render(rank_str, True, color)
    surface.blit(rank_surf, (x + 5, y + 5))
    fh = rank_surf.get_height()
    fw = rank_surf.get_width()
    sr = max(4, fh // 4)
    _draw_suit_shape(surface, card.suit,
                     x + 5 + fw + sr + 2, y + 5 + fh // 2, sr, color)

    # Center: larger suit shape
    _draw_suit_shape(surface, card.suit,
                     x + CARD_W // 2, y + CARD_H // 2, 14, color)


def draw_card_back(surface: pygame.Surface, x: int, y: int) -> None:
    """Draw a face-down card."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BACK, rect, border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=6)
    inner = pygame.Rect(x + 6, y + 6, CARD_W - 12, CARD_H - 12)
    pygame.draw.rect(surface, _CARD_BACK_INNER, inner, border_radius=4)
