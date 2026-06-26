"""
Window management and global scale factor.

call init() once from main.py after determining target resolution.
All game files use S(n) to scale any pixel value.
F11 toggles between windowed (title bar) and fullscreen-windowed (borderless).
No exclusive fullscreen is used — other monitors are never disturbed.
"""
import pygame
import ctypes

SCALE: float = 1.0
_WIN_W: int  = 1280
_WIN_H: int  = 720
_borderless: bool = False


def S(n: int | float) -> int:
    return int(n * SCALE)


def init(win_w: int, win_h: int, scale: float) -> None:
    global SCALE, _WIN_W, _WIN_H
    SCALE  = scale
    _WIN_W = win_w
    _WIN_H = win_h


def toggle_borderless() -> None:
    """Switch between windowed (title bar) and fullscreen windowed (no border)."""
    global _borderless
    _borderless = not _borderless
    if _borderless:
        pygame.display.set_mode((_WIN_W, _WIN_H), pygame.NOFRAME)
        _move_to_origin()
    else:
        pygame.display.set_mode((_WIN_W, _WIN_H))
    pygame.display.set_caption('Single Player Poker')


def _move_to_origin() -> None:
    """Move the SDL window to (0,0) of the primary monitor without resizing."""
    try:
        hwnd = pygame.display.get_wm_info().get('window')
        if hwnd:
            # SWP_NOSIZE (0x0001) | SWP_NOZORDER (0x0004)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0004)
    except Exception:
        pass
