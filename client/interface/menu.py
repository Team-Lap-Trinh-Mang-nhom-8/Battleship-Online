import pygame
import random
from client.misc.colors import *


class PlayerSetup:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font("client/assets/retrofont.ttf", 36)
        self.small_font = pygame.font.Font("client/assets/retrofont.ttf", 25)
        self.name = ""
        self.selected_avatar = 0
        self.avatars = [
            pygame.image.load("client/assets/avatar1.jpg"),
            pygame.image.load("client/assets/avatar2.jpg"),
            pygame.image.load("client/assets/avatar3.jpg"),
            pygame.image.load("client/assets/avatar4.jpg"),
        ]
        # Initialize with screen dimensions for centering
        screen_width, screen_height = screen.get_size()
        center_x = screen_width // 2
        
        # Confirm button centered
        confirm_width = 200
        confirm_height = 50
        self.confirm_button = pygame.Rect(center_x - confirm_width // 2, screen_height - 100, confirm_width, confirm_height)
        
        # Avatar buttons centered horizontally
        avatar_size = 80
        avatar_spacing = 20
        total_avatar_width = (avatar_size * 4) + (avatar_spacing * 3)
        avatar_start_x = center_x - total_avatar_width // 2
        self.avatar_buttons = [pygame.Rect(avatar_start_x + i * (avatar_size + avatar_spacing), screen_height // 2 + 50, avatar_size, avatar_size) for i in range(4)]
        
        # Name input box centered
        input_width = 350
        input_height = 50
        self.name_input_box = pygame.Rect(center_x - input_width // 2, screen_height // 2 - 100, input_width, input_height)
        self.active_input = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def run(self):
        bg = pygame.image.load("client/assets/bg_ocean.jpg").convert()
        screen_width, screen_height = self.screen.get_size()
        bg = pygame.transform.scale(bg, (screen_width, screen_height))
        self.screen.blit(bg, (0, 0))

        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        
        # Title
        title = self.font.render("PLAYER SETUP", True, RED)
        title_y = screen_height // 6
        self.screen.blit(title, (center_x - title.get_width() // 2, title_y))

        # Name input
        name_label = self.small_font.render("Enter Name:", True, BLUE)
        label_y = self.name_input_box.y - 35
        self.screen.blit(name_label, (center_x - name_label.get_width() // 2, label_y))
        pygame.draw.rect(self.screen, BACKGROUND, self.name_input_box)
        pygame.draw.rect(self.screen, WHITE if self.active_input else BLUE, self.name_input_box, 2)
        name_text = self.small_font.render(self.name + ("|" if self.cursor_visible else ""), True, BLUE)
        self.screen.blit(name_text, (self.name_input_box.x + 10, self.name_input_box.y + 10))

        # Avatar selection
        avatar_label = self.small_font.render("Select Avatar:", True, BLUE)
        avatar_label_y = self.avatar_buttons[0].y - 35
        self.screen.blit(avatar_label, (center_x - avatar_label.get_width() // 2, avatar_label_y))
        for i, avatar in enumerate(self.avatars):
            button = self.avatar_buttons[i]
            color = HOVER if i == self.selected_avatar else BACKGROUND
            pygame.draw.rect(self.screen, color, button)
            pygame.draw.rect(self.screen, BLACK, button, 2)
            avatar_scaled = pygame.transform.scale(avatar, (70, 70))
            self.screen.blit(avatar_scaled, (button.x + 5, button.y + 5))

        # Confirm button
        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        pygame.draw.rect(self.screen, GREEN, self.confirm_button)
        pygame.draw.rect(self.screen, BLACK, self.confirm_button, 2)
        confirm_text = self.small_font.render("CONFIRM", True, BLACK)
        self.screen.blit(confirm_text, (center_x - confirm_text.get_width() // 2, self.confirm_button.centery - confirm_text.get_height() // 2))

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.name_input_box.collidepoint(event.pos):
                    self.active_input = True
                else:
                    self.active_input = False
                for i, button in enumerate(self.avatar_buttons):
                    if button.collidepoint(event.pos):
                        self.selected_avatar = i
                if self.confirm_button.collidepoint(event.pos) and self.name.strip():
                    return {"name": self.name.strip(), "avatar": self.selected_avatar}
            if event.type == pygame.KEYDOWN and self.active_input:
                if event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                elif event.key == pygame.K_RETURN and self.name.strip():
                    return {"name": self.name.strip(), "avatar": self.selected_avatar}
                elif len(self.name) < 20:
                    self.name += event.unicode

        # Cursor blinking
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        return None


class Particle:
    def __init__(self, location, velocity, time):
        self.location = location
        self.velocity = velocity
        self.time = time


class Ship:
    def __init__(self):
        self.image = pygame.image.load("client/assets/ship.png")
        self.dir = "<"
        if random.choice((True, False)) == True:
            self.image = pygame.transform.flip(self.image, True, False)
            self.dir = ">"
        self.x = 450 if self.dir == "<" else -self.image.get_width()
        self.y = random.choice((random.randint(250, 320), random.randint(510, 650)))
        self.visible = True

    def draw(self, screen):
        self.x = self.x + 3 if self.dir == ">" else self.x - 3
        if self.x < -self.image.get_width() or self.x > 750 + self.image.get_width():
            self.visible = False
        screen.blit(self.image, (self.x, self.y))


class Menu:
    def __init__(self, screen):
        self.font = pygame.font.Font("client/assets/retrofont.ttf", 36)
        self.small_font = pygame.font.Font("client/assets/retrofont.ttf", 25)
        self.screen = screen
        self.load_entities()
        self.invalid_code = False
        self.show_menu = True
        self.game_taken = False
        self.particles = []
        self.ships = [Ship() for _ in range(3)]

    def run(self):
        bg = pygame.image.load("client/assets/bg_ocean.jpg").convert()
        # Scale the background to match the screen size while maintaining aspect ratio
        screen_width, screen_height = self.screen.get_size()
        bg = pygame.transform.scale(bg, (screen_width, screen_height))
        self.screen.blit(bg, (0, 0))

        self.draw_ships()
        screen_width, screen_height = self.screen.get_size()
        title = self.font.render("BATTLESHIP", True, RED)
        online_text = self.small_font.render("ONLINE", True, RED)
        center_x = screen_width // 2
        title_y = screen_height // 4
        self.screen.blit(title, (center_x - title.get_width() // 2, title_y))
        self.screen.blit(online_text, (center_x - online_text.get_width() // 2, title_y + 50))

        pygame.draw.rect(self.screen, self.create_button_color, self.create_button)
        pygame.draw.rect(self.screen, BLACK, self.create_button, 4)
        pygame.draw.rect(self.screen, BACKGROUND, self.join_button)
        pygame.draw.rect(self.screen, BLACK, self.join_button, 4)
        pygame.draw.rect(self.screen, BACKGROUND, self.solo_button)
        pygame.draw.rect(self.screen, BLACK, self.solo_button, 4)

        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        self.screen.blit(
            self.create_text, (center_x - self.create_text.get_width() // 2, self.create_button.centery - self.create_text.get_height() // 2)
        )
        self.screen.blit(
            self.solo_text, (center_x - self.solo_text.get_width() // 2, self.solo_button.centery - self.solo_text.get_height() // 2)
        )
        if not self.join_hover:
            self.join_code = ""
            self.screen.blit(
                self.join_text, (center_x - self.join_text.get_width() // 2, self.join_button.centery - self.join_text.get_height() // 2)
            )
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.join_code = self.join_code[:-1]
                    if event.key == pygame.K_RETURN:
                        if len(self.join_code) == 6:
                            return {"category": "JOIN", "payload": self.join_code}
                    elif (t := event.unicode) in __import__("string").ascii_lowercase:
                        self.join_code += t
                    self.join_code = self.join_code[:6]
            if self.join_code == "" or self.join_code == "_":
                self.update_cursor()
                self.join_code = self.cursor
            else:
                self.join_code = self.join_code.strip("_")
            screen_width, screen_height = self.screen.get_size()
            center_x = screen_width // 2
            code_text = self.small_font.render(self.join_code, True, BLUE)
            self.screen.blit(code_text, (center_x - code_text.get_width() // 2, self.join_button.centery - code_text.get_height() // 2))
            if self.invalid_code:
                text = self.small_font.render("Invalid Code", True, RED)
                self.screen.blit(text, (center_x - text.get_width() // 2, self.solo_button.y + self.solo_button.height + 20))
            elif self.game_taken:
                text = self.small_font.render("Game Occupied", True, RED)
                self.screen.blit(text, (center_x - text.get_width() // 2, self.solo_button.y + self.solo_button.height + 20))
        m_x, m_y = pygame.mouse.get_pos()
        if self.create_button.collidepoint(m_x, m_y):
            if pygame.mouse.get_pressed(3)[0]:
                return {"category": "CREATE"}
            self.join_hover = False
            self.invalid_code = False
            self.game_taken = False
            self.create_button_color = HOVER
        elif self.join_button.collidepoint(m_x, m_y):
            self.join_hover = True
            self.create_button_color = BACKGROUND
        elif self.solo_button.collidepoint(m_x, m_y):
            if pygame.mouse.get_pressed(3)[0]:
                return {"category": "SOLO"}
            self.join_hover = False
            self.invalid_code = False
            self.game_taken = False
            self.create_button_color = BACKGROUND
        else:
            self.join_hover = False
            self.invalid_code = False
            self.game_taken = False
            self.create_button_color = BACKGROUND

        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        title_y = screen_height // 4
        # Particles on either side of title
        self.draw_particles([center_x - 200, title_y + 30])
        self.draw_particles([center_x + 200, title_y + 30])

    def update_cursor(self):
        self.blink_count += 1
        if self.blink_count > 15:
            self.cursor = "_" if self.cursor == "" else ""
            self.blink_count = 0

    def reset(self):
        self.join_hover = False
        self.join_code = ""
        self.invalid_code = False
        self.blink_count = 0
        self.cursor = "_"
        self.game_taken = False

    def load_entities(self):
        screen_width, screen_height = self.screen.get_size()
        self.create_text = self.small_font.render("NEW GAME", True, BLUE)
        self.join_text = self.small_font.render("JOIN GAME", True, BLUE)
        button_width = 250
        button_height = 60
        button_spacing = 20
        # Center buttons vertically and horizontally
        total_height = (button_height * 3) + (button_spacing * 2)
        start_y = screen_height // 2 - total_height // 2 + 50
        center_x = screen_width // 2
        self.create_button = pygame.Rect(center_x - button_width // 2, start_y, button_width, button_height)
        self.join_button = pygame.Rect(center_x - button_width // 2, start_y + button_height + button_spacing, button_width, button_height)
        self.solo_button = pygame.Rect(center_x - button_width // 2, start_y + (button_height + button_spacing) * 2, button_width, button_height)
        self.solo_text = self.small_font.render("PLAY SOLO", True, BLUE)
        self.join_hover = False
        self.join_code = ""
        self.blink_count = 0
        self.cursor = "_"
        self.create_button_color = BACKGROUND

    def draw_particles(self, loc):
        self.particles.append(
            Particle(loc, [random.randint(0, 14) / 9 - 1, -2.5], random.randint(4, 6))
        )
        for particle in self.particles:
            particle.location[0] += particle.velocity[0]
            particle.location[1] += particle.velocity[1]
            particle.time -= 0.1
            pygame.draw.circle(
                self.screen, (190, 220, 219), particle.location, particle.time
            )
            radius = particle.time * 2
            self.screen.blit(
                self.circle_surf(radius, (38, 67, 86)),
                [int(i - radius) for i in particle.location],
                special_flags=pygame.BLEND_RGB_ADD,
            )
            if particle.time <= 2:
                self.particles.remove(particle)

    @staticmethod
    def circle_surf(radius, color):
        surf = pygame.Surface((radius * 2, radius * 2))
        pygame.draw.circle(surf, color, (radius, radius), radius)
        surf.set_colorkey((0, 0, 0))
        return surf

    def draw_ships(self):
        self.ships = sorted(self.ships, key=lambda s: s.x)
        for ship in self.ships:
            if any(
                ship != s and ship.y >= s.y and ship.y <= s.y + s.image.get_width()
                for s in self.ships
            ):
                self.ships.remove(ship)
        for ship in self.ships:
            ship.draw(self.screen)
        self.ships = [ship for ship in self.ships if ship.visible]
        while len(self.ships) < 3:
            self.ships.append(Ship())