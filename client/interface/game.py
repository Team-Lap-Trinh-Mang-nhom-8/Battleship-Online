import pygame
from client.interface.player_opponent import *
from client.misc.colors import *


class Game:
    def __init__(self, screen, network, ai=None, player_grid=None):
        self.screen = screen
        self.game_over = False
        self.waiting = True
        self.opp_disconnected = False
        self.room_id = ""
        self.sent_over = False

        # Load and prepare background image (use ocean background)
        self.background = pygame.image.load("client/assets/bg_ocean.jpg").convert()
        screen_width, screen_height = self.screen.get_size()
        self.background = pygame.transform.scale(self.background, (screen_width, screen_height))

        self.player = Player()
        self.opponent = Opponent()
        self.n = network
        
        # Layout cache for dynamic positioning (must be initialized before update_board_positions)
        self.layout_cache = {}
        
        # AI (solo) support
        self.ai = ai
        if self.ai:
            # Initial solo setup
            self.init_solo_boards(player_grid)

        self.sent = set()
        self.final_text = ""
        self.big_font = pygame.font.Font("client/assets/retrofont.ttf", 34)
        # Compute top UI button positions based on screen size
        sw, sh = self.screen.get_size()
        self.menu_button = pygame.Rect(10, 10, 160, 35)
        self.surrender_button = pygame.Rect(sw - 130, 10, 120, 28)
        # Place chat toggle next to menu by default
        self.chat_toggle_button = pygame.Rect(self.menu_button.right + 10, 10, 95, 28)
        # Confirmation state for surrender popup
        self.surrender_confirm = False
        # Rematch state
        self.rematch_offered = False
        self.waiting_rematch = False
        self.opponent_offered = False
        # Mouse click debounce (track previous pressed state)
        self._mouse_last_pressed = False

        # Chat functionality
        self.chat_messages = []
        self.chat_input = ""
        self.chat_active = False
        self.chat_visible = False
        self.small_font = pygame.font.Font("client/assets/retrofont.ttf", 12)
        # chat_toggle_button already positioned relative to menu in initializer
        self.chat_box = pygame.Rect(10, 30, 430, 100)
        self.chat_input_box = pygame.Rect(15, 135, 350, 20)
        self.send_button = pygame.Rect(370, 135, 65, 20)

        # Player info
        self.player_name = ""
        self.player_avatar = 0
        self.opponent_name = ""
        self.opponent_avatar = 0
        self.avatars = [
            pygame.image.load("client/assets/avatar1.jpg"),
            pygame.image.load("client/assets/avatar2.jpg"),
            pygame.image.load("client/assets/avatar3.jpg"),
            pygame.image.load("client/assets/avatar4.jpg"),
        ]
        # Calculate and store board positions (layout_cache already initialized above)
        self.update_board_positions()

    def update_board_positions(self):
        """Calculate board positions relative to avatar panels"""
        screen_width, screen_height = self.screen.get_size()
        # Grid size calculations
        grid_size = 35
        grid_cells = 10
        grid_total_size = grid_cells * grid_size

        # Place boards side-by-side: player on the left, opponent on the right
        margin_x = 30
        left_board_x = margin_x
        right_board_x = screen_width - margin_x - grid_total_size

        # Vertically center boards
        board_y = (screen_height - grid_total_size) // 2

        # Avatar panels above each board
        panel_w, panel_h = 180, 80
        player_panel = pygame.Rect(left_board_x + (grid_total_size - panel_w) // 2, board_y - panel_h - 16, panel_w, panel_h)
        opponent_panel = pygame.Rect(right_board_x + (grid_total_size - panel_w) // 2, board_y - panel_h - 16, panel_w, panel_h)

        # Store positions
        self.layout_cache["player_board_pos"] = (left_board_x, board_y)
        self.layout_cache["opponent_board_pos"] = (right_board_x, board_y)
        self.layout_cache["player_panel"] = player_panel
        self.layout_cache["opponent_panel"] = opponent_panel
        # Update top-right/inline UI positions (surrender, chat toggle) in case of resize
        try:
            sw, _ = self.screen.get_size()
            self.surrender_button.topleft = (sw - self.surrender_button.width - 10, 10)
            self.chat_toggle_button.topleft = (self.menu_button.right + 10, 10)
        except Exception:
            pass

    def init_solo_boards(self, player_grid=None):
        """(Re)initialize boards for solo (AI) play."""
        if not self.ai:
            return
        self.update_board_positions()
        grid_size = 35
        grid_cells = 10
        player_board_x, player_board_y = self.layout_cache.get("player_board_pos", (210, 500))
        opponent_board_x, opponent_board_y = self.layout_cache.get("opponent_board_pos", (200, 100))
        from client.misc.utils import make_grid
        from client.misc.ai import create_ship_grid
        # Opponent (AI) grid shell
        self.opponent.grid = make_grid(
            opponent_board_x,
            opponent_board_x + (grid_cells * grid_size),
            opponent_board_y,
            opponent_board_y + (grid_cells * grid_size),
            BLACK,
        )
        # Generate AI ships and copy to opponent grid
        ai_grid = create_ship_grid(
            sx=opponent_board_x,
            ex=opponent_board_x + (grid_cells * grid_size),
            sy=opponent_board_y,
            ey=opponent_board_y + (grid_cells * grid_size),
        )
        self.ai.grid = ai_grid
        for i in range(min(len(ai_grid), len(self.opponent.grid))):
            for j in range(min(len(ai_grid[i]), len(self.opponent.grid[i]))):
                if ai_grid[i][j].get("ship"):
                    self.opponent.grid[i][j]["ship"] = ai_grid[i][j]["ship"]
        # Player grid
        if player_grid:
            self.player.grid = player_grid
        else:
            self.player.grid = create_ship_grid(
                sx=player_board_x,
                ex=player_board_x + (grid_cells * grid_size),
                sy=player_board_y,
                ey=player_board_y + (grid_cells * grid_size),
            )
        # Activate play state
        self.waiting = False
        self.player.is_turn = True
        # Clear game-over state if coming from previous game
        self.game_over = False
        self.final_text = ""
        self.sent_over = False

    def draw_avatar_panels(self, player_panel, opponent_panel):
        """Draw avatar panels with names"""
        # Enhanced panel styling
        panel_color = (10, 14, 40, 240)
        surface = pygame.Surface((player_panel.width, player_panel.height), pygame.SRCALPHA)
        surface.fill(panel_color)
        self.screen.blit(surface, player_panel.topleft)
        self.screen.blit(surface, opponent_panel.topleft)
        
        # Draw borders
        pygame.draw.rect(self.screen, WHITE, player_panel, 3)
        pygame.draw.rect(self.screen, WHITE, opponent_panel, 3)
        pygame.draw.rect(self.screen, (100, 150, 255), player_panel, 1)
        pygame.draw.rect(self.screen, (255, 100, 100), opponent_panel, 1)
        
        # Avatars
        avatar_size = (55, 55)
        player_index = max(0, min(len(self.avatars) - 1, self.player_avatar))
        opponent_index = max(0, min(len(self.avatars) - 1, self.opponent_avatar))
        
        player_avatar = pygame.transform.scale(self.avatars[player_index], avatar_size)
        opponent_avatar = pygame.transform.scale(self.avatars[opponent_index], avatar_size)
        
        # Draw circular background for avatars
        avatar_border_radius = 28
        player_avatar_pos = (player_panel.x + 15, player_panel.y + 12)
        opponent_avatar_pos = (opponent_panel.x + 15, opponent_panel.y + 12)
        
        pygame.draw.circle(self.screen, (50, 50, 80), 
                          (player_avatar_pos[0] + avatar_size[0]//2, player_avatar_pos[1] + avatar_size[1]//2), 
                          avatar_border_radius)
        pygame.draw.circle(self.screen, (80, 50, 50), 
                          (opponent_avatar_pos[0] + avatar_size[0]//2, opponent_avatar_pos[1] + avatar_size[1]//2), 
                          avatar_border_radius)
        
        self.screen.blit(player_avatar, player_avatar_pos)
        self.screen.blit(opponent_avatar, opponent_avatar_pos)
        
        # Names
        name_font = pygame.font.Font("client/assets/retrofont.ttf", 16)
        player_label = name_font.render(self.player_name or "You", True, WHITE)
        opponent_label = name_font.render(self.opponent_name or "Opponent", True, WHITE)
        
        self.screen.blit(player_label, (player_panel.x + 80, player_panel.y + 25))
        self.screen.blit(opponent_label, (opponent_panel.x + 80, opponent_panel.y + 25))
        
        # Turn indicator
        turn_font = pygame.font.Font("client/assets/retrofont.ttf", 12)
        if hasattr(self, 'player') and self.player.is_turn:
            turn_text = turn_font.render("Your Turn", True, GREEN)
            self.screen.blit(turn_text, (player_panel.x + 80, player_panel.y + 50))
        else:
            turn_text = turn_font.render("Waiting...", True, (150, 150, 150))
            self.screen.blit(turn_text, (player_panel.x + 80, player_panel.y + 50))

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
                    if received.get("category") == "GAME_OVER":
                        payload = received.get("payload", {})
                        by = payload.get("by")
                        # If 'by' equals our player name, we won; otherwise we lost
                        if by and by == self.player_name:
                            self.final_text = "You Won!"
                        else:
                            # If reason is surrender and 'by' refers to opponent, we won
                            self.final_text = "You Lost!"
                        self.game_over = True
                        # Ensure any active surrender confirmation popup is closed
                        self.surrender_confirm = False
                        # do NOT auto-send OVER; wait for player to return to menu
                        continue
                    elif received.get("category") == "REMATCH_STATUS":
                        payload = received.get("payload", {})
                        offers = payload.get("offers", [])
                        # If opponent's name in offers, flag opponent_offered
                        try:
                            opp_name = self.opponent_name
                            self.opponent_offered = any(o == opp_name for o in offers)
                        except Exception:
                            self.opponent_offered = False
                        continue
                    elif received.get("category") == "REMATCH_START":
                        # Server indicates rematch is starting; wait for BOARD which will reset states
                        self.waiting_rematch = True
                        continue
                    if received["category"] == "BOARD":
                        received = received["payload"]
                        self.waiting = False
                        self.player.is_turn = received[0]
                        
                        # Recreate grids at correct positions
                        self.update_board_positions()
                        grid_size = 35
                        grid_cells = 10
                        
                        player_board_x, player_board_y = self.layout_cache.get("player_board_pos", (210, 500))
                        opponent_board_x, opponent_board_y = self.layout_cache.get("opponent_board_pos", (200, 100))
                        
                        from client.misc.utils import make_grid
                        # Create new grids at correct positions
                        new_player_grid = make_grid(
                            player_board_x,
                            player_board_x + (grid_cells * grid_size),
                            player_board_y,
                            player_board_y + (grid_cells * grid_size),
                            BLACK
                        )
                        new_opponent_grid = make_grid(
                            opponent_board_x,
                            opponent_board_x + (grid_cells * grid_size),
                            opponent_board_y,
                            opponent_board_y + (grid_cells * grid_size),
                            BLACK
                        )
                        
                        # Copy ship data from received grids
                        old_player_grid = received[1]
                        for i in range(min(len(old_player_grid), len(new_player_grid))):
                            for j in range(min(len(old_player_grid[i]), len(new_player_grid[i]))):
                                if old_player_grid[i][j].get("ship"):
                                    new_player_grid[i][j]["ship"] = old_player_grid[i][j]["ship"]
                                if old_player_grid[i][j].get("aimed"):
                                    new_player_grid[i][j]["aimed"] = old_player_grid[i][j]["aimed"]
                                if old_player_grid[i][j].get("perma_color"):
                                    new_player_grid[i][j]["perma_color"] = old_player_grid[i][j]["perma_color"]
                        
                        self.player.grid = new_player_grid
                        
                        for xi, yi, ship_ in received[2]:
                            if xi < len(new_opponent_grid) and yi < len(new_opponent_grid[xi]):
                                new_opponent_grid[xi][yi][ship] = ship_
                        self.opponent.grid = new_opponent_grid
                        
                        if len(received) > 3:
                            self.opponent_name = received[3]
                            self.opponent_avatar = received[4]
                        # Reset rematch and game state when a new board arrives
                        self.rematch_offered = False
                        self.waiting_rematch = False
                        self.opponent_offered = False
                        # Clear game-over flags so UI switches back to play
                        self.game_over = False
                        self.final_text = ""
                        self.sent_over = False
                    elif received["category"] == "ID":
                        self.room_id = received["payload"]
                    elif received["category"] == "POSITION":
                        rx, ry = received["payload"]
                        self.player.is_turn = True
                        self.player.grid[rx][ry][aimed] = True
                    elif received["category"] == "CHAT":
                        self.chat_messages.append(f"{self.opponent_name}: {received['payload']}")
                        if len(self.chat_messages) > 8:
                            self.chat_messages.pop(0)

    def render(self):
        # Get screen dimensions
        screen_width, screen_height = self.screen.get_size()
        # Mouse debounce: detect rising edge (pressed now, not pressed previously)
        pressed = pygame.mouse.get_pressed(3)[0]
        rising = pressed and not self._mouse_last_pressed
        
        # Scale background to fill the entire screen without changing aspect ratio
        bg_width, bg_height = self.background.get_size()
        screen_ratio = screen_width / screen_height
        bg_ratio = bg_width / bg_height
        
        if screen_ratio > bg_ratio:
            # Screen is wider than background (relative to height)
            new_width = int(screen_height * bg_ratio)
            new_height = screen_height
            self.background = pygame.transform.scale(self.background, (new_width, new_height))
            # Center the background horizontally
            x_offset = (screen_width - new_width) // 2
            self.screen.blit(self.background, (x_offset, 0))
        else:
            # Screen is taller than background (relative to width)
            new_width = screen_width
            new_height = int(screen_width / bg_ratio)
            self.background = pygame.transform.scale(self.background, (new_width, new_height))
            # Center the background vertically
            y_offset = (screen_height - new_height) // 2
            self.screen.blit(self.background, (0, y_offset))
        
        # Update board positions (in case screen size changed)
        self.update_board_positions()
        
        # Get positions from cache
        player_panel = self.layout_cache.get("player_panel")
        opponent_panel = self.layout_cache.get("opponent_panel")
        player_board_x, player_board_y = self.layout_cache.get("player_board_pos", (210, 500))
        opponent_board_x, opponent_board_y = self.layout_cache.get("opponent_board_pos", (200, 100))
        
        # Grid size calculations
        grid_size = 35
        grid_cells = 10
        grid_total_size = grid_cells * grid_size
        
        # Create highlighted background panels for boards
        board_padding = 15
        board_bg_width = grid_total_size + (board_padding * 2)
        board_bg_height = grid_total_size + (board_padding * 2)
        
        # Player board background (highlighted with blue theme)
        player_bg_rect = pygame.Rect(
            player_board_x - board_padding,
            player_board_y - board_padding,
            board_bg_width,
            board_bg_height
        )
        player_bg_surface = pygame.Surface((board_bg_width, board_bg_height), pygame.SRCALPHA)
        player_bg_surface.fill((20, 40, 80, 240))  # Semi-transparent blue background
        self.screen.blit(player_bg_surface, player_bg_rect.topleft)
        pygame.draw.rect(self.screen, (100, 150, 255), player_bg_rect, 3)  # Blue border
        pygame.draw.rect(self.screen, (150, 200, 255), player_bg_rect, 1)  # Light blue inner border
        
        # Opponent board background (highlighted with red theme)
        opponent_bg_rect = pygame.Rect(
            opponent_board_x - board_padding,
            opponent_board_y - board_padding,
            board_bg_width,
            board_bg_height
        )
        opponent_bg_surface = pygame.Surface((board_bg_width, board_bg_height), pygame.SRCALPHA)
        opponent_bg_surface.fill((80, 20, 40, 240))  # Semi-transparent red background
        self.screen.blit(opponent_bg_surface, opponent_bg_rect.topleft)
        pygame.draw.rect(self.screen, (255, 100, 100), opponent_bg_rect, 3)  # Red border
        pygame.draw.rect(self.screen, (255, 150, 150), opponent_bg_rect, 1)  # Light red inner border
        
        # Draw avatar panels
        self.draw_avatar_panels(player_panel, opponent_panel)

        # Draw surrender button
        pygame.draw.rect(self.screen, (120, 20, 20), self.surrender_button)
        pygame.draw.rect(self.screen, WHITE, self.surrender_button, 2)
        s_font = pygame.font.Font("client/assets/retrofont.ttf", 14)
        s_text = s_font.render("Surrender", True, WHITE)
        self.screen.blit(s_text, (self.surrender_button.x + (self.surrender_button.width - s_text.get_width()) // 2, self.surrender_button.y + 6))
        # Handle surrender click -> send immediately (no confirmation popup)
        if (
            self.surrender_button.collidepoint(*pygame.mouse.get_pos())
            and rising
            and not self.waiting
            and not self.game_over
        ):
            if self.ai:
                # Local solo surrender: immediate loss
                self.game_over = True
                self.final_text = "You Lost!"
            else:
                # Network surrender
                if self.n:
                    try:
                        self.n.send({"category": "SURRENDER"})
                        self.sent_over = True
                    except Exception:
                        pass
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
                        self.sent.add(x)
                        # Solo mode: let AI take a move locally
                        if self.ai:
                            # process AI choice against player grid
                            rx, ry = self.ai.choose_move(self.player.grid)
                            self.player.grid[rx][ry][aimed] = True
                            if self.player.grid[rx][ry][ship]:
                                self.player.grid[rx][ry][perma_color] = RED
                            else:
                                self.player.grid[rx][ry][perma_color] = WHITE
                            # player remains with turn after AI move
                            self.player.is_turn = True
                        else:
                            self.player.is_turn = False
                            if self.n:
                                self.n.send({"category": "POSITION", "payload": x})
        self.opponent.draw_grid(self.screen)
        self.draw_chat()
        # Update last mouse state for debounce
        self._mouse_last_pressed = pressed

    

    def game_over_screen(self):
        if self.final_text == "You Lost!":
            for ex, sx in enumerate(self.player.grid):
                for es, square in enumerate(sx):
                    if square[ship]:
                        r = pygame.Rect(square[rect])
                        # Keep fire effect within the cell bounds
                        self.screen.blit(self.player.ship_destroyed_img, r)
                        break
        screen_width, screen_height = self.screen.get_size()
        # Draw menu button (fixed top-left)
        menu_surface = pygame.Surface((self.menu_button.width, self.menu_button.height), pygame.SRCALPHA)
        menu_surface.fill((50, 50, 80, 200))
        self.screen.blit(menu_surface, self.menu_button.topleft)
        pygame.draw.rect(self.screen, WHITE, self.menu_button, 2)
        font = pygame.font.Font("client/assets/retrofont.ttf", 16)
        menu_text = font.render("Return To Menu", True, WHITE)
        self.screen.blit(menu_text, (self.menu_button.x + (self.menu_button.width - menu_text.get_width()) // 2, self.menu_button.y + (self.menu_button.height - menu_text.get_height()) // 2))

        center_x = screen_width // 2
        center_y = screen_height // 2
        txt = self.big_font.render(self.final_text, True, GREEN)
        self.screen.blit(
            txt,
            (center_x - txt.get_width() // 2, center_y - txt.get_height() // 2),
        )
        # Mouse debounce for game over buttons
        pressed = pygame.mouse.get_pressed(3)[0]
        rising = pressed and not self._mouse_last_pressed
        # Play Again button
        play_rect = pygame.Rect(center_x - 100, center_y + 60, 200, 40)
        if not self.waiting_rematch:
            pygame.draw.rect(self.screen, (0, 120, 0), play_rect)
            pygame.draw.rect(self.screen, WHITE, play_rect, 2)
            play_text = font.render("Play Again", True, WHITE)
            self.screen.blit(play_text, (play_rect.centerx - play_text.get_width() // 2, play_rect.centery - play_text.get_height() // 2))
        else:
            # If opponent already offered, show small hint
            if self.opponent_offered and not self.rematch_offered:
                hint = self.small_font.render("Opponent offered rematch", True, WHITE)
                self.screen.blit(hint, (center_x - hint.get_width() // 2, center_y + 105))
            # Waiting for opponent message
            waiting_text = self.small_font.render("Waiting for opponent...", True, WHITE)
            self.screen.blit(waiting_text, (center_x - waiting_text.get_width() // 2, center_y + 70))

        # Handle Play Again click
        if not self.waiting_rematch and play_rect.collidepoint(*pygame.mouse.get_pos()) and rising:
            if self.ai:
                # Solo replay: regenerate boards
                self.player = Player()
                self.opponent = Opponent()
                self.init_solo_boards()
            else:
                if self.n:
                    try:
                        self.n.send({"category": "REMATCH_OFFER"})
                        self.rematch_offered = True
                        self.waiting_rematch = True
                    except Exception:
                        pass
        if (
            self.menu_button.collidepoint(*pygame.mouse.get_pos())
            and rising
        ):
            # Notify server we're leaving the room/menu
            if self.n:
                try:
                    self.n.send({"category": "OVER"})
                except Exception:
                    pass
            # update mouse last state before returning
            self._mouse_last_pressed = pressed
            return "MENU"
        # update mouse last state when staying on game over screen
        self._mouse_last_pressed = pressed

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
                    screen_width, screen_height = self.screen.get_size()
                    txt = self.big_font.render("Opponent Has Left", True, RED)
                    center_x = screen_width // 2
                    center_y = screen_height // 2
                    self.screen.blit(
                        txt, (center_x - txt.get_width() // 2, center_y - txt.get_height() // 2)
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
                # Keep showing the game over screen; do not auto-send OVER or return to menu.
                return self.game_over_screen()
        else:
            # Show background image behind waiting text
            screen_width, screen_height = self.screen.get_size()
            self.background = pygame.transform.scale(self.background, (screen_width, screen_height))
            self.screen.blit(self.background, (0, 0))
            txt = self.big_font.render("Waiting For Player", True, GREEN)
            font = pygame.font.Font("client/assets/retrofont.ttf", 24)
            roomid_text = font.render(self.room_id, True, GREEN)
            center_x = screen_width // 2
            center_y = screen_height // 2
            self.screen.blit(
                txt, (center_x - txt.get_width() // 2, center_y - txt.get_height() // 2)
            )
            self.screen.blit(
                roomid_text,
                (
                    center_x - roomid_text.get_width() // 2,
                    center_y - txt.get_height() // 2 + 60,
                ),
            )
            
            # Draw menu button
            pygame.draw.rect(self.screen, BACKGROUND, self.menu_button)
            pygame.draw.rect(self.screen, BLACK, self.menu_button, 2)
            menu_font = pygame.font.Font("client/assets/retrofont.ttf", 14)
            menu_text = menu_font.render("Return To Menu", True, BLUE)
            self.screen.blit(menu_text, (self.menu_button.x + (self.menu_button.width - menu_text.get_width()) // 2, self.menu_button.y + (self.menu_button.height - menu_text.get_height()) // 2))
            
            # Check for menu button click
            if (
                self.menu_button.collidepoint(*pygame.mouse.get_pos())
                and pygame.mouse.get_pressed(3)[0]
            ):
                return "MENU"

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
        # If solo mode, immediately reinitialize boards (prevent waiting screen)
        if self.ai:
            self.init_solo_boards()
