import sys
import pygame
import core.bankroll as bankroll
from core.modifiers import EMPTY

WIDTH, HEIGHT = 1280, 720
FPS = 60
FELT_GREEN = (10, 46, 26)

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Single Player Poker')
    clock = pygame.time.Clock()

    balance = bankroll.load()
    difficulty = 1  # 0=Easy 1=Normal 2=Hard

    from menu import Menu
    menu = Menu(screen, WIDTH, HEIGHT)

    running = True
    while running:
        action = None
        while action is None and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
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
            bankroll.save(balance)

    pygame.quit()
    sys.exit()

def _launch(mode: str, screen, clock, balance: int, difficulty: int) -> int:
    if mode == 'video_poker':
        from game.video_poker import VideoPoker
        return VideoPoker(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'holdem':
        from game.holdem import HoldEm
        return HoldEm(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'five_card_draw':
        from game.five_card_draw import FiveCardDraw
        return FiveCardDraw(screen, clock, balance, difficulty, EMPTY).run()
    if mode == 'duel':
        from game.duel import Duel
        return Duel(screen, clock, balance, difficulty, EMPTY).run()
    return balance

if __name__ == '__main__':
    main()
