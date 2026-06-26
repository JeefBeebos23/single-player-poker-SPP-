import os
import sys
import pygame

CARD_W = 80
CARD_H = 110

_CARD_BG           = (255, 255, 255)
_CARD_BACK         = (0, 80, 160)
_CARD_BACK_INNER   = (0, 55, 110)
_RED               = (200, 0, 0)
_BLACK             = (20, 20, 20)
_SELECTED_BORDER   = (255, 215, 0)
_UNSELECTED_BORDER = (180, 180, 180)

_RANK_NAMES = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}

# Pre-scaled suit images.  Populated lazily on first draw_card call.
_SUIT_SMALL: dict[str, pygame.Surface] = {}
_SUIT_LARGE: dict[str, pygame.Surface] = {}
_SUITS_LOADED = False

_CORNER_BOX = 16   # px bounding box for corner suit
_CENTER_BOX = 32   # px bounding box for centre suit


def init_scale(scale: float) -> None:
    """Call once after main.py determines the window scale.  Forces suit reload."""
    global _CORNER_BOX, _CENTER_BOX, _SUITS_LOADED, _SUIT_SMALL, _SUIT_LARGE
    _CORNER_BOX = max(8,  int(16 * scale))
    _CENTER_BOX = max(16, int(32 * scale))
    _SUITS_LOADED = False
    _SUIT_SMALL.clear()
    _SUIT_LARGE.clear()


def _asset_path(relative: str) -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def _white_to_transparent(surf: pygame.Surface) -> pygame.Surface:
    try:
        import numpy as np
        raw = pygame.surfarray.array3d(surf)
        min_rgb = raw.min(axis=2).astype(np.int32)
        new_alpha = np.clip(255 - min_rgb, 0, 255).astype(np.uint8)
        result = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        rgb_ptr = pygame.surfarray.pixels3d(result)
        rgb_ptr[:] = raw
        del rgb_ptr
        alpha_ptr = pygame.surfarray.pixels_alpha(result)
        alpha_ptr[:] = new_alpha
        del alpha_ptr
        return result
    except Exception:
        return surf.copy()


def _fit_scale(surf: pygame.Surface, box: int) -> pygame.Surface:
    w, h = surf.get_size()
    scale = box / max(w, h, 1)
    nw = max(1, round(w * scale))
    nh = max(1, round(h * scale))
    return pygame.transform.smoothscale(surf, (nw, nh))


def _load_suits() -> None:
    global _SUITS_LOADED
    _SUITS_LOADED = True
    suits_dir = _asset_path(os.path.join('assets', 'suits'))
    mapping = {'D': 'diamond', 'H': 'heart', 'S': 'spade', 'C': 'club'}
    for code, name in mapping.items():
        path = os.path.join(suits_dir, f'{name}.png')
        if not os.path.exists(path):
            continue
        try:
            raw = pygame.image.load(path).convert_alpha()
            processed = _white_to_transparent(raw)
            _SUIT_SMALL[code] = _fit_scale(processed, _CORNER_BOX)
            _SUIT_LARGE[code] = _fit_scale(processed, _CENTER_BOX)
        except Exception:
            pass


def _blit_suit(surface: pygame.Surface, code: str,
               cx: int, cy: int, use_large: bool) -> bool:
    if not _SUITS_LOADED:
        _load_suits()
    imgs = _SUIT_LARGE if use_large else _SUIT_SMALL
    img = imgs.get(code)
    if img is None:
        return False
    sw, sh = img.get_size()
    surface.blit(img, (cx - sw // 2, cy - sh // 2))
    return True


def _draw_suit_shape(surface: pygame.Surface, suit: str,
                     cx: int, cy: int, r: int, color: tuple) -> None:
    if r < 3:
        return
    if suit == 'D':
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surface, color, pts)
    elif suit == 'H':
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
        cr  = max(1, r * 55 // 100)
        ox  = max(1, r * 42 // 100)
        bot = cy + r * 20 // 100
        w   = max(1, r * 95 // 100)
        pygame.draw.polygon(surface, color,
                            [(cx - w, bot - cr * 40 // 100),
                             (cx,     cy - r),
                             (cx + w, bot - cr * 40 // 100)])
        pygame.draw.circle(surface, color, (cx - ox, bot), cr)
        pygame.draw.circle(surface, color, (cx + ox, bot), cr)
        sw = max(1, r // 3)
        sh = max(1, r // 2)
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - sw, bot + cr - 1, sw * 2, sh))
    elif suit == 'C':
        cr      = max(1, r * 42 // 100)
        top_cy  = cy - cr
        side_cy = cy + cr // 2
        side_ox = cr
        pygame.draw.circle(surface, color, (cx, top_cy), cr)
        pygame.draw.circle(surface, color, (cx - side_ox, side_cy), cr)
        pygame.draw.circle(surface, color, (cx + side_ox, side_cy), cr)
        pygame.draw.polygon(surface, color,
                            [(cx, top_cy),
                             (cx - side_ox, side_cy),
                             (cx + side_ox, side_cy)])
        sw     = max(1, r // 4)
        sh     = max(1, r * 55 // 100)
        stem_y = side_cy + cr
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - sw, stem_y - 2, sw * 2, sh))


# ---------------------------------------------------------------------------
# Public drawing functions
# cw / ch default to module constants (scale=1.0 baseline).
# Pass scaled values (e.g. self._cw, self._ch) for higher-DPI rendering.
# ---------------------------------------------------------------------------

def draw_card(surface: pygame.Surface, card, x: int, y: int,
              font: pygame.font.Font, selected: bool = False,
              cw: int = CARD_W, ch: int = CARD_H) -> None:
    pad    = max(2, cw // 16)
    radius = max(4, cw // 13)
    rect   = pygame.Rect(x, y, cw, ch)
    pygame.draw.rect(surface, _CARD_BG, rect, border_radius=radius)
    border_color = _SELECTED_BORDER if selected else _UNSELECTED_BORDER
    border_w = max(1, cw // 40)
    pygame.draw.rect(surface, border_color, rect, border_w if not selected else border_w + 1,
                     border_radius=radius)

    color    = _RED if card.suit in ('H', 'D') else _BLACK
    rank_str = _RANK_NAMES.get(card.rank, str(card.rank))

    rank_surf = font.render(rank_str, True, color)
    surface.blit(rank_surf, (x + pad, y + pad))
    fh = rank_surf.get_height()
    fw = rank_surf.get_width()
    sr      = max(6, fh * 3 // 8)
    suit_cx = x + pad + max(fw, _CORNER_BOX) // 2
    suit_cy = y + pad + fh + sr + max(2, cw // 40)

    if not _blit_suit(surface, card.suit, suit_cx, suit_cy, use_large=False):
        _draw_suit_shape(surface, card.suit, suit_cx, suit_cy, sr, color)

    center_r = max(8, cw // 5)
    if not _blit_suit(surface, card.suit, x + cw // 2, y + ch // 2, use_large=True):
        _draw_suit_shape(surface, card.suit, x + cw // 2, y + ch // 2, center_r, color)


def draw_card_back(surface: pygame.Surface, x: int, y: int,
                   cw: int = CARD_W, ch: int = CARD_H) -> None:
    radius = max(4, cw // 13)
    inner_pad = max(4, cw // 13)
    rect = pygame.Rect(x, y, cw, ch)
    pygame.draw.rect(surface, _CARD_BACK, rect, border_radius=radius)
    pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=radius)
    inner = pygame.Rect(x + inner_pad, y + inner_pad,
                        cw - 2 * inner_pad, ch - 2 * inner_pad)
    pygame.draw.rect(surface, _CARD_BACK_INNER, inner,
                     border_radius=max(3, cw // 16))
