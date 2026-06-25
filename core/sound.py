import os
import sys
import pygame

_SFX: dict[str, pygame.mixer.Sound] = {}
_MUSIC_TRACKS: dict[str, str] = {}
_music_on      = True
_sfx_on        = True
_current_track = ''
_music_volume  = 0.3
_sfx_volume    = 0.7

# Debug tracking
_last_sfx_name = ''
_last_sfx_time = 0      # ms timestamp of last play() call
_debug_font    = None   # initialised lazily (needs pygame display)

_SFX_NAMES = [
    'deal', 'flip', 'check', 'chip_collect',
    'win_big', 'lose', 'click', 'fold', 'bubble_pop', 'startup',
    'raise',
]


def _asset_path(relative: str) -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def init() -> None:
    """Load all sounds. Call once after pygame.mixer.init()."""
    global _MUSIC_TRACKS
    sounds_dir = _asset_path(os.path.join('assets', 'sounds'))
    for name in _SFX_NAMES:
        path = os.path.join(sounds_dir, f'{name}.wav')
        if os.path.exists(path):
            try:
                _SFX[name] = pygame.mixer.Sound(path)
            except Exception:
                pass

    music_dir = _asset_path(os.path.join('assets', 'music'))
    _MUSIC_TRACKS = {
        'menu':        os.path.join(music_dir, 'menu.mp3'),
        'video_poker': os.path.join(music_dir, 'video_poker.mp3'),
        'gameplay':    os.path.join(music_dir, 'gameplay.mp3'),
        'win':         os.path.join(music_dir, 'win.mp3'),
    }

    try:
        pygame.mixer.music.set_volume(_music_volume)
    except Exception:
        pass
    for sfx in _SFX.values():
        sfx.set_volume(_sfx_volume)


def play(name: str) -> None:
    """Play a SFX by name. No-op if missing or SFX off."""
    global _last_sfx_name, _last_sfx_time
    if _sfx_on and name in _SFX:
        _SFX[name].play()
        _last_sfx_name = name
        _last_sfx_time = pygame.time.get_ticks()


def play_music(context: str) -> None:
    """Start looping music for given context. No-op if same track playing or music off."""
    global _current_track
    if not _music_on:
        return
    path = _MUSIC_TRACKS.get(context, '')
    if not path or not os.path.exists(path):
        return
    if path == _current_track:
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(_music_volume)
        pygame.mixer.music.play(-1)
        _current_track = path
    except Exception:
        pass


def stop_music() -> None:
    global _current_track
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    _current_track = ''


def set_music_volume(vol: float) -> None:
    global _music_volume
    _music_volume = max(0.0, min(1.0, vol))
    try:
        pygame.mixer.music.set_volume(_music_volume)
    except Exception:
        pass


def set_sfx_volume(vol: float) -> None:
    global _sfx_volume
    _sfx_volume = max(0.0, min(1.0, vol))
    for sfx in _SFX.values():
        sfx.set_volume(_sfx_volume)


def music_volume() -> float:
    return _music_volume


def sfx_volume() -> float:
    return _sfx_volume


def toggle_music() -> bool:
    """Toggle music on/off. Returns new state (True = on)."""
    global _music_on
    _music_on = not _music_on
    try:
        if not _music_on:
            pygame.mixer.music.pause()
        elif _current_track:
            pygame.mixer.music.unpause()
    except Exception:
        pass
    return _music_on


def toggle_sfx() -> bool:
    """Toggle SFX on/off. Returns new state (True = on)."""
    global _sfx_on
    _sfx_on = not _sfx_on
    return _sfx_on


def music_on() -> bool:
    return _music_on


def sfx_on() -> bool:
    return _sfx_on


def draw_debug_overlay(surface: pygame.Surface) -> None:
    """Draw a small debug overlay showing the last SFX and current music track.
    Visible for 4 seconds after each sound plays; always shows music track.
    """
    global _debug_font
    if _debug_font is None:
        try:
            _debug_font = pygame.font.SysFont('Consolas', 13)
        except Exception:
            return

    now = pygame.time.get_ticks()
    h   = surface.get_height()
    bg  = pygame.Surface((340, 36), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    surface.blit(bg, (0, h - 36))

    music_name = os.path.basename(_current_track) if _current_track else '(none)'
    music_t = _debug_font.render(f'Music : {music_name}', True, (160, 200, 255))
    surface.blit(music_t, (4, h - 34))

    if now - _last_sfx_time < 4000 and _last_sfx_name:
        age_ms  = now - _last_sfx_time
        sfx_col = (255, 255, 0) if age_ms < 500 else (200, 200, 120)
        sfx_t   = _debug_font.render(f'SFX   : {_last_sfx_name}.wav  ({age_ms} ms ago)',
                                     True, sfx_col)
        surface.blit(sfx_t, (4, h - 20))
    else:
        idle_t = _debug_font.render('SFX   : (silent)', True, (100, 100, 100))
        surface.blit(idle_t, (4, h - 20))
