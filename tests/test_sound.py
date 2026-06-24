import pytest
import pygame

@pytest.fixture(scope='module', autouse=True)
def init_mixer():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    try:
        pygame.mixer.init()
    except Exception:
        pytest.skip('pygame.mixer not available in this environment')
    yield
    pygame.mixer.quit()

import core.sound as sound

def test_init_does_not_crash_with_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(sound, '_asset_path', lambda rel: str(tmp_path / rel))
    sound._SFX.clear()
    sound.init()
    assert True

def test_play_missing_name_does_not_crash():
    sound.play('this_does_not_exist')

def test_play_music_missing_context_does_not_crash():
    sound.play_music('this_does_not_exist')

def test_toggle_music_returns_bool():
    result = sound.toggle_music()
    assert isinstance(result, bool)
    sound.toggle_music()  # restore

def test_toggle_sfx_returns_bool():
    result = sound.toggle_sfx()
    assert isinstance(result, bool)
    sound.toggle_sfx()  # restore

def test_music_on_is_bool():
    assert isinstance(sound.music_on(), bool)

def test_sfx_on_is_bool():
    assert isinstance(sound.sfx_on(), bool)

def test_toggle_music_changes_state():
    before = sound.music_on()
    sound.toggle_music()
    assert sound.music_on() != before
    sound.toggle_music()
    assert sound.music_on() == before

def test_toggle_sfx_changes_state():
    before = sound.sfx_on()
    sound.toggle_sfx()
    assert sound.sfx_on() != before
    sound.toggle_sfx()
    assert sound.sfx_on() == before
