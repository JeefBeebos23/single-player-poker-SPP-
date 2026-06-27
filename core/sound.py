import os
import sys
import random
import pygame

_SFX: dict[str, pygame.mixer.Sound] = {}
_MUSIC_TRACKS: dict[str, str] = {}
_music_on      = True
_sfx_on        = True
_current_track = ''
_music_volume  = 0.3
_sfx_volume    = 0.7

# Playlist state for the gameplay shuffle pool
_playlist_paths:  list[str] = []   # all found tracks
_playlist_order:  list[str] = []   # current shuffled rotation
_playlist_idx:    int  = 0
_playlist_active: bool = False
_MUSIC_END = pygame.USEREVENT + 1

# Filenames (in assets/music/) that form the gameplay shuffle pool
_PLAYLIST_FILENAMES = [
    'ludwig_lullaby.mp3',
    'bach_cello.mp3',
    '10pm.mp3',
    '10am.mp3',
    '2am.mp3',
    '2pm.mp3',
]

_SFX_NAMES = [
    'deal', 'flip', 'check', 'chip_collect',
    'win_big', 'lose', 'click', 'fold', 'bubble_pop',
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
    global _MUSIC_TRACKS, _playlist_paths
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
        'win':         os.path.join(music_dir, 'win.mp3'),
    }

    # Scan for playlist tracks (only those that actually exist)
    _playlist_paths = [
        os.path.join(music_dir, fname)
        for fname in _PLAYLIST_FILENAMES
        if os.path.exists(os.path.join(music_dir, fname))
    ]

    pygame.mixer.music.set_endevent(_MUSIC_END)

    try:
        pygame.mixer.music.set_volume(_music_volume)
    except Exception:
        pass
    for sfx in _SFX.values():
        sfx.set_volume(_sfx_volume)


def play(name: str) -> None:
    """Play a SFX by name. No-op if missing or SFX off."""
    if _sfx_on and name in _SFX:
        _SFX[name].play()


def play_music(context: str) -> None:
    """Start music for the given context.

    'gameplay' starts a shuffled playlist through the 6 tracks.
    All other contexts play a single looping file.
    Repeated play_music('gameplay') calls while the playlist is running are
    no-ops so _start_hand() doesn't restart the playlist mid-game.
    """
    global _current_track, _playlist_active
    if not _music_on:
        return

    if context == 'gameplay':
        if _playlist_active:
            return  # already running — let it continue
        _start_playlist()
        return

    # Non-playlist context: deactivate playlist and switch to a looping file
    _playlist_active = False
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


def play_music_once(context: str) -> None:
    """Play a one-shot music track (not looped, doesn't activate the playlist)."""
    global _current_track, _playlist_active
    if not _music_on:
        return
    _playlist_active = False
    path = _MUSIC_TRACKS.get(context, '')
    if not path or not os.path.exists(path):
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(_music_volume)
        pygame.mixer.music.play(0)
        _current_track = path
    except Exception:
        pass


def _start_playlist() -> None:
    global _playlist_active, _playlist_idx, _playlist_order
    _playlist_order  = _playlist_paths[:]
    random.shuffle(_playlist_order)
    _playlist_idx    = 0
    _playlist_active = True
    _play_playlist_track()


def _play_playlist_track() -> None:
    global _current_track
    if not _playlist_order:
        return
    path = _playlist_order[_playlist_idx]
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(_music_volume)
        pygame.mixer.music.play(0)   # play once; end-event fires when done
        _current_track = path
    except Exception:
        pass


def handle_event(event: pygame.event.Event) -> None:
    """Call from each game's event loop to advance the playlist on track end."""
    global _playlist_idx, _playlist_order
    if event.type != _MUSIC_END or not _playlist_active or not _music_on:
        return
    _playlist_idx += 1
    if _playlist_idx >= len(_playlist_order):
        random.shuffle(_playlist_order)
        _playlist_idx = 0
    _play_playlist_track()


def stop_music() -> None:
    global _current_track, _playlist_active
    _playlist_active = False   # clear before stop() to ignore the end-event
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
