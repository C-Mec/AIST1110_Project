import pygame
import config

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

def intxy(vec: Vec2) -> tuple[int, int]:
    return round(vec.x), round(vec.y)

class Color:
    white = (255, 255, 255)
    blue = (70, 130, 200)
    black = (0, 0, 0)

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
        self.surface = Surface(dimension)
        self.pos = pos
    
    def draw(self, screen: Surface):
        screen.blit(self.surface, self.pos)
    
    def click_at(self, pos: Vec2):
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
        """Remove a surface from the manager."""
        
        # If what you are trying to remove is not here, it is not something we should just ignore
        try:
            self.layers.remove(base_surface)
        except Exception as err:
            print(err)
    
    def get_top_collision(self, pos: Vec2) -> tuple[Base_Surface, Vec2]:
        for base_surface in reversed(self.layers):
            rect = base_surface.surface.get_rect()
            rect.topleft = base_surface.pos

            if rect.collidepoint(pos):
                rpos = pos - base_surface.pos
                return base_surface, rpos
        
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
        
        # Value stored in Vec2 are floats
        self.grid_width, self.grid_height = intxy(grid_dimension)
        
        width, height = self.surface.get_size()
        self.cell_width = round(width / self.grid_width)
        self.cell_height = round(height / self.grid_height)

        self._active_popup = None       # Track currently open popup
        self._grid_init()

    def _grid_init(self):
        self.grid = [[
            [] for col in range(self.grid_width) 
        ] for row in range(self.grid_height)]
        
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                rect = pygame.Rect(
                    round(col * self.cell_width),
                    round(row * self.cell_height),
                    round(self.cell_width),
                    round(self.cell_height)
                )
                
                value = (row + 1) * 200
            
                ques = Question.sample(col, row, value)
                used = False
                
                self.grid[row][col] = [rect, ques, used]
                
    def click_at(self, pos: Vec2):
        row, col = self._get_rowcol(pos)
        rect, question, used = self.grid[row][col]
        print(used)
        if used:
            print("This question has already been answered.")
            return
        print(self.grid[row][col])
        self.grid[row][col][2] = True

        print("something")
        # Create and add popup
        popup = Question_Surface(question)
        manager.add_surface(popup)
        
        self._active_popup = popup
    
    def _get_rowcol(self, rpos: Vec2):
        x, y = intxy(rpos)
        
        col = x // self.cell_width
        row = y // self.cell_height
        
        return row, col
    
    def draw(self, screen: Surface):
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                rect, question, used = self.grid[row][col]

                # Draw cell background
                pygame.draw.rect(self.surface, Color.blue, rect)
                # Draw border
                pygame.draw.rect(self.surface, Color.white, rect, 2)

                # Draw dollar value
                value = (row + 1) * 200

                # What is this? I assume it works www
                text_surf = self.font.render(str(value), True, Color.white)
                text_rect = text_surf.get_rect(center=rect.center)

                self.surface.blit(text_surf, text_rect)
                pygame.draw.rect(self.surface, Color.white, rect, 1)

        screen.blit(self.surface, self.pos)

# ----- Question_Surface: a modal window showing question and options -----
class Question_Surface(Base_Surface):
    def __init__(self, question: Question):
        # Popup size and position (centered)
        dimension = Vec2(600, 400)
    
        pos = Rect(Vec2(0, 0), dimension)
        pos.center = config.screen_rect.center
        pos = pos.topleft
        
        super().__init__(dimension, pos)
        
        self.question = question
        
        # Create three option buttons
        button_height = 50
        margin = 20
        start_y = 150
        self.option_rects = []
        
        for i in range(3):
            rect = pygame.Rect(50, start_y + i * (button_height + margin), 500, button_height)
            self.option_rects.append(rect)
        
        self.selected = None

    def draw(self, screen: Surface):
        # Clear surface with transparent background
        self.surface.fill((0, 0, 0, 0))
        
        # Semi-transparent overlay
        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.surface.blit(overlay, (0, 0))
        
        # Border and background
        pygame.draw.rect(self.surface, Color.white, self.surface.get_rect(), 3)
        pygame.draw.rect(self.surface, Color.blue, self.surface.get_rect().inflate(-6, -6))
        
        # Wrap question text
        words = self.question.problem.split()
        lines = []
        line = ""
        for w in words:
            test_line = line + w + " "
            if Font.title.size(test_line)[0] < 540:
                line = test_line
            else:
                lines.append(line)
                line = w + " "
        lines.append(line)
        
        y_offset = 50
        for line in lines:
            text = Font.title.render(line, True, Color.white)
            self.surface.blit(text, (30, y_offset))
            y_offset += 30
        
        # Draw option buttons
        for i, rect in enumerate(self.option_rects):
            color = (80, 80, 200) if self.selected != i else (200, 200, 80)
            pygame.draw.rect(self.surface, color, rect)
            pygame.draw.rect(self.surface, Color.white, rect, 2)
            option_text = f"{chr(65+i)}. {self.question.answer[i]}"
            text_surf = Font.option.render(option_text, True, Color.white)
            text_rect = text_surf.get_rect(center=rect.center)
            self.surface.blit(text_surf, text_rect)
        
        screen.blit(self.surface, self.pos)

    def click_at(self, pos: Vec2, player: Player):
        for i, rect in enumerate(self.option_rects):
            if rect.collidepoint(pos):
                self.selected = i
                
                if self.question.answer_index == i:
                    player.add_score(self.question.value)
                    print(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                else:
                    player.add_score(-self.question.value)
                    print(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")
                
                # Remove popup from manager
                manager.remove_surface(self.surface)