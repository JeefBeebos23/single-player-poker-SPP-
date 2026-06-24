import os
import sys
import pygame

_SFX: dict[str, pygame.mixer.Sound] = {}
_MUSIC_TRACKS: dict[str, str] = {}
_music_on = True
_sfx_on   = True
_current_track = ''

_SFX_NAMES = [
    'deal', 'flip', 'check', 'chip_bet', 'chip_collect',
    'win_big', 'lose', 'click', 'fold', 'bubble_pop', 'startup',
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


def play(name: str) -> None:
    """Play a SFX by name. No-op if missing or SFX off."""
    if _sfx_on and name in _SFX:
        _SFX[name].play()


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
