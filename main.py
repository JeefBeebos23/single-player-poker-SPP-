import sys
import pygame
import core.bankroll as bankroll
from core.modifiers import EMPTY
import core.sound as sound
import core.window as window
import ui.renderer as renderer

_BASE_W, _BASE_H = 1280, 720
FPS = 60
FELT_GREEN = (10, 46, 26)


def _detect_scale() -> tuple[int, int, float]:
    """Return (win_w, win_h, scale) based on the primary monitor's height."""
    sizes = pygame.display.get_desktop_sizes()
    native_h = sizes[0][1] if sizes else _BASE_H
    if native_h >= 2160:
        scale = 3.0
    elif native_h >= 1440:
        scale = 2.0
    elif native_h >= 1080:
        scale = 1.5
    else:
        scale = 1.0
    return int(_BASE_W * scale), int(_BASE_H * scale), scale


def main():
    pygame.init()
    pygame.mixer.init()

    WIN_W, WIN_H, scale = _detect_scale()
    window.init(WIN_W, WIN_H, scale)
    renderer.init_scale(scale)

    sound.init()
    sound.play_music('menu')
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption('Single Player Poker')
    clock = pygame.time.Clock()

    balance = bankroll.load()
    difficulty = 1  # 0=Easy 1=Normal 2=Hard

    from menu import Menu
    menu = Menu(screen, WIN_W, WIN_H)

    running = True
    while running:
        action = None
        while action is None and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    window.toggle_borderless()
                else:
                    action = menu.handle_event(event)

            screen.fill(FELT_GREEN)
            menu.draw(balance, difficulty)
            pygame.display.flip()
            clock.tick(FPS)

        if not running:
            break

        kind, value = action
        if kind == 'quit':
            break
        if kind == 'difficulty':
            difficulty = value
            continue
        if kind == 'play':
            balance = _launch(value, screen, clock, balance, difficulty)
            sound.play_music('menu')
            bankroll.save(balance)

    pygame.quit()
    sys.exit()


def _launch(mode: str, screen, clock, balance: int, difficulty: int) -> int:
    if mode == 'video_poker':
        sound.play_music('video_poker')
        from game.video_poker import VideoPoker
        return VideoPoker(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'holdem':
        sound.play_music('gameplay')
        from game.holdem import HoldEm
        return HoldEm(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'five_card_draw':
        sound.play_music('gameplay')
        from game.five_card_draw import FiveCardDraw
        return FiveCardDraw(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'duel':
        sound.play_music('gameplay')
        from game.duel import Duel
        return Duel(screen, clock, balance, difficulty, EMPTY).run()
    return balance


if __name__ == '__main__':
    main()
