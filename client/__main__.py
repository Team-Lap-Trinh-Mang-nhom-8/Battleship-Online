from threading import Thread

import pygame

from client.interface.game import Game
from client.interface.menu import Menu, PlayerSetup
from client.misc.network import Network

# AI support
from client.misc.ai import create_ship_grid, Bot


class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((450, 740))
        pygame.display.set_caption("Battleship")

        self.running = True
        self.clock = pygame.time.Clock()
        self.menu = Menu(self.screen)
        self.player_setup = None
        self.game = None
        self.thread_started = False
        self.player_data = None

    def run(self):
        while self.running:
            if self.menu.show_menu:
                if (r := self.menu.run()) :
                    if r == "QUIT":
                        self.running = False
                        break
                    # SOLO mode
                    if isinstance(r, dict) and r.get("category") == "SOLO":
                        if not self.game:
                            # Create player and bot ship grids
                            player_grid = create_ship_grid(sx=50, ex=400, sy=390, ey=730)
                            bot_grid = create_ship_grid(sx=50, ex=400, sy=30, ey=370)
                            bot = Bot(grid=bot_grid)
                            self.game = Game(self.screen, None, ai=bot, player_grid=player_grid)
                        self.menu.show_menu = False
                        continue
                    # Online flow: go to player setup
                    self.player_setup = PlayerSetup(self.screen)
                    self.menu.show_menu = False
                    self.player_data = r  # Store the menu action (CREATE or JOIN)
            elif self.player_setup:
                if (setup_result := self.player_setup.run()):
                    if setup_result == "QUIT":
                        self.running = False
                        break
                    # Player setup complete, proceed to game
                    self.player_data.update(setup_result)  # Merge name and avatar
                    if not self.game:
                        self.game = Game(self.screen, Network())
                    self.game.n.send(self.player_data)
                    if not self.thread_started:
                        if self.player_data.get("category") == "CREATE":
                            self.recv_thread = Thread(
                                target=self.game.receiving_thread,
                                kwargs={"menu": self.menu},
                            )
                        elif (d := self.game.n.receive()) != "INVALID":
                            if d == "TAKEN":
                                self.menu.game_taken = True
                                self.menu.show_menu = True
                                self.player_setup = None
                                continue
                            else:
                                self.recv_thread = Thread(
                                    target=self.game.receiving_thread,
                                    args=(d, self.menu),
                                )
                        else:
                            self.menu.invalid_code = True
                            self.menu.show_menu = True
                            self.player_setup = None
                            continue
                        self.recv_thread.daemon = True
                        self.recv_thread.start()
                        self.thread_started = True
                    if not (self.menu.invalid_code or self.menu.game_taken):
                        self.player_setup = None
            elif self.game.run() == "MENU":
                self.menu.show_menu = True
                self.menu.reset()
                self.game.reset()
                self.player_setup = None
                self.player_data = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.game and not self.menu.show_menu and not self.player_setup:
                    self.game.handle_chat_input(event)
            pygame.display.flip()
            self.clock.tick(30)

        return pygame.quit()


if __name__ == "__main__":
    Main().run()