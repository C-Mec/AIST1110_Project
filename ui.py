import pygame
import config

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
    wrong = "#50C8C8"
    correct = "#C8C850"
    overlay = "#000000B4"

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
    def __init__(self, name):
        self.name = name
        self.score = 0
    
    def add_score(self, points):
        self.score += points
    
class Base_Surface:
    def __init__(self, dimension: Vec2, pos: Vec2 = Vec2(0, 0)):
        # Assume screen = main screen
        
        # Relative position on screen
        self.pos = pos
        self.surface = Surface(dimension)
        
        self.overshade = False
        self.dimension = dimension
        
        # The rect on the screen
        self.rect = self.surface.get_rect(topleft=pos)
    
    def draw(self, screen: Surface):
        screen.blit(self.surface, self.pos)
    
    def click_at(self, pos: Vec2, player: Player):
        # Has no reaction by default
        pass

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
        
        self.grid[row][col][2] = True

        # Create and add popup
        popup = Question_Surface(question)
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

                # Draw cell background
                pygame.draw.rect(self.surface, Color.background, rect)

                # Draw dollar value
                value = (row + 1) * 200

                # Font.render returns a surface with text
                text = self.font.render(str(value), True, Color.border)
                text_rect = text.get_rect(center=rect.center)

                self.surface.blit(text, text_rect)
                
                # Draw border
                pygame.draw.rect(self.surface, Color.border, rect, 2)

        screen.blit(self.surface, self.pos)

# ----- Question_Surface: a modal window showing question and options -----
class Question_Surface(Base_Surface):
    def __init__(self, question: Question):
        # Popup size and position (centered)
        dimension = Vec2(600, 400)
        
        rect = Surface(dimension).get_rect(center=config.screen_rect.center)
        pos = rect.topleft
        
        super().__init__(dimension, pos)
        
        self.overshade = True
        self.question = question
        
        # Create three option buttons
        self.option_rects = []
        
        button_height = 50
        margin = 20
        
        option_rect = pygame.Rect(50, 150, 500, button_height)
        
        for i in range(3):
            self.option_rects.append(option_rect.move(0, i * (button_height + margin)))
        
        self.selected_option = None

    def draw(self, screen: Surface):
        # Semi-transparent overlay
        overlay = Surface(config.screen_dimension, pygame.SRCALPHA)
        overlay.fill(Color.overlay)
        screen.blit(overlay, Vec2(0, 0))
        
        # Border and background
        border_rect = Rect(Vec2(0, 0), self.dimension)
        
        pygame.draw.rect(self.surface, Color.border, border_rect, 3)
        pygame.draw.rect(self.surface, Color.background, border_rect.inflate(-6, -6))
        
        def wrap_text(text: str, font: Font, width: int):
            words = text.split()
            lines = []
            
            start = 0
            for end in range(len(words)):
                line = " ".join(words[start:end+1])
                
                if font.size(line)[0] >= width or end == len(words) - 1:
                    lines.append(line)
                    start = end+1
            
            return lines
        
        # Wrap question text
        lines = wrap_text(self.question.problem, Font.title, 540)
        
        for row, line in enumerate(lines):
            text = Font.title.render(line, True, Color.text)
            self.surface.blit(text, (30, 50 + row * 30))
        
        # Draw option buttons
        for i, rect in enumerate(self.option_rects):
            # Right now when answered the surface is immediately removed so it 
            #   never shows the color of correct
            color = Color.wrong if self.selected_option != i else Color.correct
            
            pygame.draw.rect(self.surface, color, rect)
            pygame.draw.rect(self.surface, Color.border, rect, 2)
            
            option_text = f"{chr(65+i)}. {self.question.answer[i]}"
            
            text = Font.option.render(option_text, True, Color.text)
            text_rect = text.get_rect(center=rect.center)
            
            self.surface.blit(text, text_rect)
        
        screen.blit(self.surface, self.pos)

    def click_at(self, pos: Vec2, player: Player):
        for i, rect in enumerate(self.option_rects):
            if rect.collidepoint(pos):
                self.selected_option = i
                
                if self.question.answer_index == i:
                    player.add_score(self.question.value)
                    print(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                else:
                    player.add_score(-self.question.value)
                    print(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")
                
                # Remove popup from manager
                manager.remove_surface(self)