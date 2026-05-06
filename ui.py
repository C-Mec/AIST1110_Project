import pygame
import config
import math
import random

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

def intxy(vec: Vec2) -> tuple[int, int]:
    return round(vec.x), round(vec.y)

class Color:
    border = "#FFFFFF"
    text = "#FFFFFF"
    background = "#4682C8"
    black = "#000000"
    greyed = "#808080"
    
    correct = "#3CB371"  # green
    wrong = "#DC143C"  # red
    
    timer = "#50C8C8"
    
    overlay = "#000000B4"
    
    palette = [
        "#4287F5", "#3CB371", "#DC143C", "#FFD700", "#FF69B4",
        "#8A2BE2", "#FF8C00", "#00CED1", "#ADFF2F", "#FF4500",
        "#7FFF00", "#FF1493", "#20B2AA", "#FF6347", "#9370DB",
        "#40E0D0", "#FFB6C1", "#6A5ACD", "#00FA9A", "#FF00FF"
    ]
    
    @staticmethod
    def assign_colors(players):
        """Randomly assign distinct colors from palette to players."""
        chosen = random.sample(Color.palette, len(players))
        for player, color in zip(players, chosen):
            player.color = color
    
class Font:
    title = pygame.font.Font(None, 32)
    option = pygame.font.Font(None, 28)

class Question:
    def __init__(self, problem: str, options: list[str], answer_ind: int, value: int):
        self.problem = problem
        self.answer = options
        self.answer_index = answer_ind
        self.value = value
        self.used = False

    def listAnswer(self):
        for i in range(len(self.answer)):
            print(f"{i+1}. {self.answer[i]}")
    
    @staticmethod
    def sample(col: int, row: int, value: int):
        return Question(
            problem=f"Category {col+1} Row {row+1}: What is the capital of France?",
            options=["Paris", "London", "Berlin"],
            answer_ind=0,
            value=value
        )

class Player:
    def __init__(self, name: str, color: tuple[int, int, int]):
        self.name = name
        self.score = 0
        self.color = color  # RGB tuple

    def add_score(self, amount: int):
        self.score += amount

class Base_Surface:
    def __init__(self, dimension: Vec2, pos: Vec2 = Vec2(0, 0)):
        self.pos = pos
        # Use SRCALPHA so transparency works
        self.surface = Surface(dimension, pygame.SRCALPHA)

        self.overshade = False
        self.dimension = dimension
        self.rect = self.surface.get_rect(topleft=pos)

        # Transparency and fade
        self.alpha = 255       # fully opaque by default
        self.fading = False    # fade disabled by default
        self.fade_speed = 10   # how fast alpha decreases per frame

    def draw(self, screen: Surface):
        # Apply alpha before blitting
        if self.alpha < 255:
            temp = self.surface.copy()
            temp.set_alpha(self.alpha)
            screen.blit(temp, self.pos)
        else:
            screen.blit(self.surface, self.pos)

        # Handle fade progression
        if self.fading and self.alpha > 0:
            self.alpha -= self.fade_speed
            if self.alpha <= 0:
                manager.remove_surface(self)

    def click_at(self, pos: Vec2, player: Player):
        pass

    def start_fade(self, speed: int = 10):
        """Begin fading out this surface."""
        self.fading = True
        self.fade_speed = speed

class Surface_Manager:
    def __init__(self):
        pass
    
    def init(self, main_screen: Surface):
        '''The runtime init.'''
        
        self.main_screen = main_screen

        # A stash in which index = z-axis
        self.layers: list[Base_Surface] = []
    
    def add_surface(self, base_surface: Base_Surface) -> None: 
        self.layers.append(base_surface)
   
    def remove_surface(self, base_surface: Base_Surface) -> None:
        self.layers.remove(base_surface)
    
    def get_top_collision(self, pos: Vec2) -> tuple[Base_Surface, Vec2]:
        for base_surface in reversed(self.layers):
            if base_surface.rect.collidepoint(pos):
                rpos = pos - base_surface.pos
                return base_surface, rpos
            
            # Overshade surface shades anything behind it
            if base_surface.overshade:
                return None, None
        
        return None, None
    
    def render(self) -> None:
        # fill the screen with a color to wipe away anything from last frame
        self.main_screen.fill("#121314")

        for base_surface in self.layers:
            base_surface.draw(self.main_screen)
        
        pygame.display.flip()

# The project-wise global instance of surface manager
# Needs to be set in main.py
manager = Surface_Manager()

class Grid_Surface(Base_Surface):
    def __init__(self, dimension: Vec2, pos: Vec2, grid_dimension: Vec2):
        super().__init__(dimension, pos)
        
        self.font = pygame.font.Font(None, 36)
        
        self.grid_dimension = grid_dimension
        
        g_width, g_height = intxy(grid_dimension)
        width, height = intxy(self.dimension)
        self.cell_dimension = Vec2(
            round(width / g_width),
            round(height / g_height)
        )

        self._grid_init()

    def _grid_init(self):
        g_width, g_height = intxy(self.grid_dimension)
        c_width, c_height = intxy(self.cell_dimension)
        
        self.grid = [[
            [] for col in range(g_width)
        ] for row in range(g_height)]
        
        for row in range(g_height):
            for col in range(g_width):
                rect = pygame.Rect(
                    round(col * c_width),
                    round(row * c_height),
                    round(c_width),
                    round(c_height)
                )
                
                value = (row + 1) * 200
            
                ques = Question.sample(col, row, value)
                used = False
                
                self.grid[row][col] = [rect, ques, used]
                
    def click_at(self, pos: Vec2, player: Player):
        row, col = self._get_rowcol(pos)
        rect, question, used = self.grid[row][col]

        if used:
            print("This question has already been answered.")
            return

        # Mark cell as used → will render grey next draw
        self.grid[row][col][2] = True

        popup = Question_Surface(question, player)
        manager.add_surface(popup)

    def _get_rowcol(self, rpos: Vec2):
        x, y = intxy(rpos)
        c_width, c_height = intxy(self.cell_dimension)
        
        col = x // c_width
        row = y // c_height
        
        return row, col
    
    def draw(self, screen: Surface):
        g_width, g_height = intxy(self.grid_dimension)

        for row in range(g_height):
            for col in range(g_width):
                rect, question, used = self.grid[row][col]

                # Fill background: grey if used, normal otherwise
                fill_color = Color.greyed if used else Color.background
                pygame.draw.rect(self.surface, fill_color, rect)

                if not used:
                    value = (row + 1) * 200
                    text = self.font.render(str(value), True, Color.text)
                    text_rect = text.get_rect(center=rect.center)
                    self.surface.blit(text, text_rect)

                # Draw border
                pygame.draw.rect(self.surface, Color.border, rect, 2)

        screen.blit(self.surface, self.pos)


class StartScreen(Base_Surface):
    def __init__(self):
        # Full screen overlay
        dimension = Vec2(*config.screen_dimension)
        pos = Vec2(0, 0)
        super().__init__(dimension, pos)

        self.overshade = True  # blocks interaction until dismissed
        self.title_font = pygame.font.Font(None, 72)
        self.info_font = pygame.font.Font(None, 36)

    def draw(self, screen: Surface):
        # Fill background
        self.surface.fill(Color.background)

        # Title
        title_text = self.title_font.render("JEOPARDY!", True, Color.text)
        title_rect = title_text.get_rect(center=(self.dimension.x // 2, self.dimension.y // 3))
        self.surface.blit(title_text, title_rect)

        # Info
        info_text = self.info_font.render("Press any key or click to start", True, Color.text)
        info_rect = info_text.get_rect(center=(self.dimension.x // 2, self.dimension.y // 2))
        self.surface.blit(info_text, info_rect)

        # Apply fade alpha
        fade_surface = self.surface.copy()
        fade_surface.set_alpha(self.alpha)
        screen.blit(fade_surface, self.pos)

        # Handle fade progression
        if self.fading and self.alpha > 0:
            self.alpha -= 10  # fade speed
            if self.alpha <= 0:
                manager.remove_surface(self)

    def click_at(self, pos: Vec2, player: Player):
        # Remove start screen when clicked
        manager.remove_surface(self)

    def handle_key(self, event):
        # Remove start screen when any key pressed
        manager.remove_surface(self)


# ----- Question_Surface: a modal window showing question and options -----
class Question_Surface(Base_Surface):
    def __init__(self, question: Question, player: Player):
        dimension = Vec2(config.screen_dimension[0] * 0.7,
                         config.screen_dimension[1] * 0.7)  # scale to window
        rect = Surface(dimension).get_rect(center=(config.screen_dimension[0]//2,
                                                   config.screen_dimension[1]//2))
        pos = rect.topleft
        super().__init__(dimension, pos)

        self.option_border_color = Color.border
        self.selected_option = None
        self.correct_option_index = None
        self.close_time = None

        self.overshade = True
        self.question = question
        self.player = player

        # Buzz button in upper third
        self.buzz_rect = pygame.Rect(dimension.x//2 - 100, dimension.y//3, 200, 60)
        self.buzzed = False

        # Timer
        self.timer_active = False
        self.start_time = None
        self.duration = 5

        # Options: compute dynamically
        self.option_rects = []
        button_height = 50
        margin = 20
        total_height = len(self.question.answer) * (button_height + margin) - margin
        start_y = dimension.y - total_height - 40  # 40px padding from bottom
        for i in range(len(self.question.answer)):
            rect = pygame.Rect(50, start_y + i * (button_height + margin),
                               dimension.x - 100, button_height)
            self.option_rects.append(rect)

    def draw(self, screen: Surface):
        self.surface.fill(Color.background)
        pygame.draw.rect(self.surface, Color.border, self.surface.get_rect(), 3)

        # Question text at top
        text = Font.title.render(self.question.problem, True, Color.text)
        self.surface.blit(text, (30, 30))

        if not self.buzzed:
            # Buzz button in player color
            pygame.draw.rect(self.surface, self.player.color, self.buzz_rect)
            pygame.draw.rect(self.surface, Color.border, self.buzz_rect, 2)
            buzz_text = Font.option.render("BUZZ!", True, Color.black)
            self.surface.blit(buzz_text, buzz_text.get_rect(center=self.buzz_rect.center))
        else:
            if self.timer_active:
                elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
                remaining = max(0, self.duration - elapsed)

                # Circle depletion in degrees
                center = (int(self.dimension.x//2), int(self.dimension.y//3))
                radius = 50
                pygame.draw.circle(self.surface, Color.border, center, radius, 2)

                # Draw filled arc (pie slice shrinking)
                angle = 360 * (remaining / self.duration)
                end_angle = -90 + angle
                pygame.draw.arc(
                    self.surface,
                    Color.timer,
                    pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2),
                    math.radians(-90),
                    math.radians(end_angle),
                    8
                )

                # Seconds remaining in middle
                sec_text = Font.option.render(str(int(remaining)), True, Color.text)
                self.surface.blit(sec_text, sec_text.get_rect(center=center))

                if remaining <= 0:
                    self.player.add_score(-self.question.value)
                    manager.remove_surface(self)
                    return

            # Options
            for i, rect in enumerate(self.option_rects):
                pygame.draw.rect(self.surface, Color.background, rect)

                if self.selected_option == i:
                    border_color = self.option_border_color
                elif self.correct_option_index == i:
                    border_color = Color.correct
                else:
                    border_color = Color.border

                pygame.draw.rect(self.surface, border_color, rect, 2)

                option_text = f"{chr(65+i)}. {self.question.answer[i]}"
                text = Font.option.render(option_text, True, (Color.text))
                self.surface.blit(text, text.get_rect(center=rect.center))

        # Kill surface after 1s delay
        if self.close_time and pygame.time.get_ticks() >= self.close_time:
            manager.remove_surface(self)

        screen.blit(self.surface, self.pos)

    def click_at(self, pos: Vec2, player: Player):
        if not self.buzzed and self.buzz_rect.collidepoint(pos):
            self.buzzed = True
            self.timer_active = True
            self.start_time = pygame.time.get_ticks()
            
            # Screen flash in player color
            manager.add_surface(BorderFlash(self.player))
        elif self.buzzed and self.selected_option is None:  # prevent multiple scoring
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    self.selected_option = i
                    self.timer_active = False
                    
                    if self.question.answer_index == i:
                        player.add_score(self.question.value)
                        print(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                        self.option_border_color = Color.correct
                    else:
                        player.add_score(-self.question.value)
                        print(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")
                        self.option_border_color = Color.wrong
                        self.correct_option_index = self.question.answer_index

                    # schedule surface removal after 1s
                    self.close_time = pygame.time.get_ticks() + 1000


class BorderFlash(Base_Surface):
    def __init__(self, player: Player, duration: int = 500):
        dimension = Vec2(*config.screen_dimension)
        pos = Vec2(0, 0)
        super().__init__(dimension, pos)

        self.overshade = False
        self.player = player
        self.start_time = pygame.time.get_ticks()
        self.duration = duration  # ms
        self.alpha = 0

    def draw(self, screen: Surface):
        elapsed = pygame.time.get_ticks() - self.start_time

        # Fade in/out logic
        cutoff = self.duration // 5
        if elapsed < cutoff:
            # Fade in
            self.alpha = int(255 * (elapsed / cutoff))
        elif elapsed < self.duration:
            # Fade out
            self.alpha = int(255 * (1 - (elapsed - cutoff) / cutoff))
        else:
            # End effect
            manager.remove_surface(self)
            return

        # Draw border flash
        flash_surface = Surface(config.screen_dimension, pygame.SRCALPHA)
        flash_surface.fill((0, 0, 0, 0))  # transparent

        rgb = self.player.color

        # Draw thick border rectangle
        border_rect = flash_surface.get_rect()
        pygame.draw.rect(flash_surface, rgb, border_rect, 40)

        # Apply alpha
        flash_surface.set_alpha(self.alpha)
        screen.blit(flash_surface, (0, 0))

class ScoreOverlay(Base_Surface):
    def __init__(self, players: list[Player]):
        dimension = Vec2(180, 110)  # size of the rectangle 
        pos = Vec2(config.screen_dimension[0] - dimension.x - 10, 10)

        # Important: create with SRCALPHA so alpha values are respected
        self.surface = Surface(dimension, pygame.SRCALPHA)
        self.pos = pos
        self.rect = self.surface.get_rect(topleft=pos)

        self.players = players
        self.font = pygame.font.Font(None, 28)
        self.overshade = False

    def draw(self, screen: Surface):
        # Clear surface each frame
        self.surface.fill((0, 0, 0, 0))

        # Semi-transparent background (alpha = 180)
        pygame.draw.rect(self.surface, (0, 0, 0, 180), self.surface.get_rect())
        
        # Player scores (right-aligned)
        for i, player in enumerate(self.players):
            text = f"{player.name}: ${player.score}"
            # Convert hex to RGB before rendering
            rendered = self.font.render(text, True, player.color)
            text_rect = rendered.get_rect()
            text_rect.top = 10 + i * 35
            text_rect.right = self.surface.get_rect().right - 10
            self.surface.blit(rendered, text_rect)


        # Blit overlay onto main screen
        screen.blit(self.surface, self.pos)


        