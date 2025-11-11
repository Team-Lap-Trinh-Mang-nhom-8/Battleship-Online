import pygame
from client.interface.player_opponent import *
from client.misc.colors import *


class Game:
    def __init__(self, screen, network):
        self.screen = screen
        self.game_over = False
        self.waiting = True
        self.opp_disconnected = False
        self.room_id = ""
        self.sent_over = False

        self.player = Player()
        self.opponent = Opponent()
        self.n = network

        self.sent = set()
        self.final_text = ""
        self.big_font = pygame.font.Font("client/assets/retrofont.ttf", 34)
        self.menu_button = pygame.Rect(125, 0, 200, 28)
        
        # Chat functionality
        self.chat_messages = []
        self.chat_input = ""
        self.chat_active = False
        self.chat_visible = False
        self.small_font = pygame.font.Font("client/assets/retrofont.ttf", 12)
        self.chat_toggle_button = pygame.Rect(350, 0, 95, 28)
        self.chat_box = pygame.Rect(10, 30, 430, 100)
        self.chat_input_box = pygame.Rect(15, 135, 350, 20)
        self.send_button = pygame.Rect(370, 135, 65, 20)

    @staticmethod
    def check_game_over(grid):
        return all(sq[aimed] for x in grid for sq in x if sq[ship])

    def receiving_thread(self, board=None, menu=None):
        while 1:
            if not board:
                received = self.n.receive()
            else:
                received = board
                board = None
            if received:
                if menu:
                    if received == "TAKEN":
                        menu.game_taken = True
                        menu.show_menu = True
                    elif received == "INVALID":
                        menu.invalid_code = True
                        menu.show_menu = True
                if received == "END" and not menu.show_menu and not self.waiting:
                    self.opp_disconnected = True
                    break
                if isinstance(received, dict):
                    if received["category"] == "BOARD":
                        received = received["payload"]
                        self.waiting = False
                        self.player.is_turn = received[0]
                        self.player.grid = received[1]
                        for xi, yi, ship_ in received[2]:
                            self.opponent.grid[xi][yi][ship] = ship_
                    elif received["category"] == "ID":
                        self.room_id = received["payload"]
                    elif received["category"] == "POSITION":
                        rx, ry = received["payload"]
                        self.player.is_turn = True
                        self.player.grid[rx][ry][aimed] = True
                    elif received["category"] == "CHAT":
                        self.chat_messages.append(f"Opponent: {received['payload']}")
                        if len(self.chat_messages) > 8:
                            self.chat_messages.pop(0)

    def render(self):
        pygame.draw.line(self.screen, BLACK, (0, 384), (450, 384), 10)
        self.player.draw_grid(self.screen)
        for ex, sx in enumerate(self.opponent.grid):
            for es, square in enumerate(sx):
                if (
                    Opponent.is_hovered(
                        pygame.mouse.get_pos(), pygame.Rect(square[rect])
                    )
                    and pygame.mouse.get_pressed(3)[0]
                    and self.player.is_turn
                ):
                    self.opponent.grid[ex][es][aimed] = True
                    if (x := (ex, es)) not in self.sent:
                        if square[ship]:
                            self.opponent.grid[ex][es][perma_color] = RED
                            while self.opponent.sound_counter < 1:
                                self.opponent.explosion_sound.play()
                                self.opponent.sound_counter += 1
                            self.opponent.sound_counter = 0
                        else:
                            self.opponent.grid[ex][es][perma_color] = WHITE
                            while self.opponent.sound_counter < 1:
                                self.opponent.miss_sound.play()
                                self.opponent.sound_counter += 1
                            self.opponent.sound_counter = 0
                        self.player.is_turn = False
                        self.sent.add(x)
                        self.n.send({"category": "POSITION", "payload": x})
        self.opponent.draw_grid(self.screen)
        self.draw_chat()

    def game_over_screen(self):
        if self.final_text == "You Lost!":
            for ex, sx in enumerate(self.player.grid):
                for es, square in enumerate(sx):
                    if square[ship]:
                        r = pygame.Rect(square[rect])
                        r.y += 10
                        self.screen.blit(self.player.ship_destroyed_img, r)
                        break
        pygame.draw.rect(self.screen, BACKGROUND, (0, 0, 450, 20))
        pygame.draw.rect(self.screen, BLACK, self.menu_button, 2)
        font = pygame.font.Font("client/assets/retrofont.ttf", 14)
        menu_text = font.render("Return To Menu", True, BLUE)
        self.screen.blit(menu_text, (225 - menu_text.get_width() // 2, 6))

        txt = self.big_font.render(self.final_text, True, GREEN)
        self.screen.blit(
            txt,
            (225 - txt.get_width() // 2, 370 - txt.get_height() // 2),
        )
        if (
            self.menu_button.collidepoint(*pygame.mouse.get_pos())
            and pygame.mouse.get_pressed(3)[0]
        ):
            return "MENU"

    def run(self):
        if not self.waiting:
            if self.check_game_over(self.opponent.grid):
                self.game_over = True
                self.final_text = "You Won!"
            elif self.check_game_over(self.player.grid):
                self.game_over = True
                self.final_text = "You Lost!"
            if not self.game_over:
                self.screen.fill(BACKGROUND)
                if self.opp_disconnected:
                    txt = self.big_font.render("Opponent Has Left", True, RED)
                    self.screen.blit(
                        txt, (225 - txt.get_width() // 2, 370 - txt.get_height() // 2)
                    )
                else:
                    self.render()
                    font = pygame.font.Font("client/assets/retrofont.ttf", 14)
                    if self.player.is_turn:
                        text = font.render("Your turn", True, WHITE)
                    else:
                        text = font.render("Opponent's turn", True, WHITE)
                    self.screen.blit(text, (0, 0))
                self.draw_chat()
            else:
                if not self.sent_over:
                    self.n.send({"category": "OVER"})
                    self.sent_over = True
                return self.game_over_screen()
        else:
            self.screen.fill(BACKGROUND)
            txt = self.big_font.render("Waiting For Player", True, GREEN)
            font = pygame.font.Font("client/assets/retrofont.ttf", 24)
            roomid_text = font.render(self.room_id, True, GREEN)
            self.screen.blit(
                txt, (225 - txt.get_width() // 2, 370 - txt.get_height() // 2)
            )
            self.screen.blit(
                roomid_text,
                (
                    225 - roomid_text.get_width() // 2,
                    (370 - txt.get_height() // 2) + 100,
                ),
            )

    def draw_chat(self):
        # Chat toggle button
        pygame.draw.rect(self.screen, (0, 0, 100) if self.chat_visible else (100, 100, 100), self.chat_toggle_button)
        pygame.draw.rect(self.screen, WHITE, self.chat_toggle_button, 2)
        toggle_text = self.small_font.render("Chat", True, WHITE)
        self.screen.blit(toggle_text, (self.chat_toggle_button.x + 30, self.chat_toggle_button.y + 8))
        
        if not self.chat_visible:
            return
            
        # Chat box background
        pygame.draw.rect(self.screen, (50, 50, 50), self.chat_box)
        pygame.draw.rect(self.screen, WHITE, self.chat_box, 2)
        
        # Display messages
        y_offset = 35
        for msg in self.chat_messages[-6:]:
            text_surface = self.small_font.render(msg, True, WHITE)
            self.screen.blit(text_surface, (15, y_offset))
            y_offset += 15
        
        # Input box
        color = WHITE if self.chat_active else (100, 100, 100)
        pygame.draw.rect(self.screen, (30, 30, 30), self.chat_input_box)
        pygame.draw.rect(self.screen, color, self.chat_input_box, 2)
        
        # Input text
        input_surface = self.small_font.render(self.chat_input, True, WHITE)
        self.screen.blit(input_surface, (self.chat_input_box.x + 5, self.chat_input_box.y + 3))
        
        # Send button
        pygame.draw.rect(self.screen, (0, 100, 0), self.send_button)
        pygame.draw.rect(self.screen, WHITE, self.send_button, 2)
        send_text = self.small_font.render("Send", True, WHITE)
        self.screen.blit(send_text, (self.send_button.x + 20, self.send_button.y + 3))
    
    def handle_chat_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.chat_active and self.chat_visible:
                if event.key == pygame.K_RETURN:
                    if self.chat_input.strip():
                        self.chat_messages.append(f"You: {self.chat_input}")
                        self.n.send({"category": "CHAT", "payload": self.chat_input})
                        if len(self.chat_messages) > 6:
                            self.chat_messages.pop(0)
                        self.chat_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.chat_input = self.chat_input[:-1]
                elif len(self.chat_input) < 40:
                    self.chat_input += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.chat_toggle_button.collidepoint(event.pos):
                self.chat_visible = not self.chat_visible
                self.chat_active = False
            elif self.chat_visible:
                if self.chat_input_box.collidepoint(event.pos):
                    self.chat_active = True
                elif self.send_button.collidepoint(event.pos):
                    if self.chat_input.strip():
                        self.chat_messages.append(f"You: {self.chat_input}")
                        self.n.send({"category": "CHAT", "payload": self.chat_input})
                        if len(self.chat_messages) > 6:
                            self.chat_messages.pop(0)
                        self.chat_input = ""
                else:
                    self.chat_active = False

    def reset(self):
        self.game_over = False
        self.waiting = True
        self.opp_disconnected = False
        self.room_id = ""
        self.sent_over = False

        self.player = Player()
        self.opponent = Opponent()

        self.sent = set()
        self.final_text = ""
        self.chat_messages = []
        self.chat_input = ""
        self.chat_active = False
        self.chat_visible = False
