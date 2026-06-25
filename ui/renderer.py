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
    """Draw a suit icon centered at (cx, cy); r is the half-height of the shape."""
    if r < 3:
        return
    if suit == 'D':
        # Rhombus — equal width and height
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surface, color, pts)

    elif suit == 'H':
        # Two circles at top, downward-pointing triangle at bottom
        cr  = max(1, r * 55 // 100)
        ox  = max(1, r * 42 // 100)
        top = cy - r * 20 // 100
        pygame.draw.circle(surface, color, (cx - ox, top), cr)
        pygame.draw.circle(surface, color, (cx + ox, top), cr)
        w = max(1, r * 95 // 100)
        pygame.draw.polygon(surface, color,
                            [(cx - w, top + cr * 40 // 100),
                             (cx,     cy + r),
                             (cx + w, top + cr * 40 // 100)])

    elif suit == 'S':
        # Upward-pointing triangle, two circles below, small stem
        cr  = max(1, r * 55 // 100)
        ox  = max(1, r * 42 // 100)
        bot = cy + r * 20 // 100
        # Triangle tip pointing up
        w = max(1, r * 95 // 100)
        pygame.draw.polygon(surface, color,
                            [(cx - w, bot - cr * 40 // 100),
                             (cx,     cy - r),
                             (cx + w, bot - cr * 40 // 100)])
        # Two shoulder circles
        pygame.draw.circle(surface, color, (cx - ox, bot), cr)
        pygame.draw.circle(surface, color, (cx + ox, bot), cr)
        # Stem
        sw = max(1, r // 3)
        sh = max(1, r // 2)
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - sw, bot + cr - 1, sw * 2, sh))

    elif suit == 'C':
        # Trefoil: three circles (top + bottom-left + bottom-right) + stem
        cr = max(1, r * 42 // 100)
        # Circle centers arranged so they just touch
        top_cy  = cy - cr
        side_cy = cy + cr // 2
        side_ox = cr
        pygame.draw.circle(surface, color, (cx,         top_cy),  cr)
        pygame.draw.circle(surface, color, (cx - side_ox, side_cy), cr)
        pygame.draw.circle(surface, color, (cx + side_ox, side_cy), cr)
        # Fill the triangular gap in the centre
        pygame.draw.polygon(surface, color,
                            [(cx, top_cy),
                             (cx - side_ox, side_cy),
                             (cx + side_ox, side_cy)])
        # Stem
        sw = max(1, r // 4)
        sh = max(1, r * 55 // 100)
        stem_y = side_cy + cr
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - sw, stem_y - 2, sw * 2, sh))


def draw_card(surface: pygame.Surface, card, x: int, y: int,
              font: pygame.font.Font, selected: bool = False) -> None:
    """Draw a face-up card. `card` is a core.cards.Card instance."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BG, rect, border_radius=6)
    border_color = _SELECTED_BORDER if selected else _UNSELECTED_BORDER
    pygame.draw.rect(surface, border_color, rect, 3 if selected else 1, border_radius=6)

    color = _RED if card.suit in ('H', 'D') else _BLACK
    rank_str = _RANK_NAMES.get(card.rank, str(card.rank))

    # Corner (top-left): rank text, then suit shape stacked below it
    rank_surf = font.render(rank_str, True, color)
    surface.blit(rank_surf, (x + 5, y + 5))
    fh = rank_surf.get_height()
    fw = rank_surf.get_width()
    sr = max(6, fh * 3 // 8)            # corner suit half-size
    suit_cx = x + 5 + max(fw, sr * 2) // 2
    _draw_suit_shape(surface, card.suit, suit_cx, y + 5 + fh + sr + 3, sr, color)

    # Centre: large suit shape
    _draw_suit_shape(surface, card.suit,
                     x + CARD_W // 2, y + CARD_H // 2, 16, color)


def draw_card_back(surface: pygame.Surface, x: int, y: int) -> None:
    """Draw a face-down card."""
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, _CARD_BACK, rect, border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=6)
    inner = pygame.Rect(x + 6, y + 6, CARD_W - 12, CARD_H - 12)
    pygame.draw.rect(surface, _CARD_BACK_INNER, inner, border_radius=4)
