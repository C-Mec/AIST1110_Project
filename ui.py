import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

class Color:
    white = (255, 255, 255)
    blue = (70, 130, 200)
    black = (0, 0, 0)

class Vecc2(pygame.Vector2):
    # To be continued
    pass

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
    def sample():
        return Question(
            "Sample Question?",
            ["Option A", "Option B", "Option C"],
            0,
            200
        )
    
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
    def __init__(self, main_screen: Surface):
        self.main_screen = main_screen

        # A stash in which index = z-axis
        self.layers: list[Base_Surface] = []
    
    def add_surface(self, base_surface: Base_Surface) -> None: 
        self.layers.append(base_surface)
    
    def get_top_collision(self, pos: Vec2) -> tuple[Base_Surface, Vec2]:
        for base_surface in reversed(self.layers):
            rect = base_surface.surface.get_rect()
            rect.topleft = base_surface.pos

            if rect.collidepoint(pos):
                rpos = pos - base_surface.pos
                return (base_surface, rpos)
    
    def render(self) -> None:
        # fill the screen with a color to wipe away anything from last frame
        self.main_screen.fill("#121314")

        for base_surface in self.layers:
            base_surface.draw(self.main_screen)
        
        pygame.display.flip()

class Grid_Surface(Base_Surface):
    def __init__(self, dimension: Vec2, pos: Vec2, grid_dimension: Vec2):
        super().__init__(dimension, pos)
        
        self.font = pygame.font.Font(None, 36)
        
        # Value stored in Vec2 are floats
        grid_width, grid_height = grid_dimension
        self.grid_width = round(grid_width)
        self.grid_height = round(grid_height)
        
        width, height = self.surface.get_size()
        self.cell_width = round(width / self.grid_width)
        self.cell_height = round(height / self.grid_height)

        self.grid = [[
            () for col in range(self.grid_width) 
        ] for row in range(self.grid_height)]

        self._grid_init()

    def _grid_init(self):
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                rect = pygame.Rect(
                    round(col * self.cell_width),
                    round(row * self.cell_height),
                    round(self.cell_width),
                    round(self.cell_height)
                )

                self.grid[row][col] = (rect, Question.sample())

    def click_at(self, pos: Vec2):
        rect, question = self.get_cell_at_pos(pos)

        print(f"Question at {pos}: {question.problem}")
        question.listAnswer()
    
    def get_cell_at_pos(self, rpos: Vec2) -> tuple[Rect, Question]:
        x, y = rpos
        col = round(x) // self.cell_width
        row = round(y) // self.cell_height

        print(x, y, col, row)

        return self.grid[row][col]
    
    def draw(self, screen: Surface):
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                rect, question = self.grid[row][col]

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

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
    
    def add_score(self, points):
        self.score += points

'''
class question_screen(Grid_Surface):
    def __init__(self, width, height, question):
        super().__init__(width, height)
        self.question = question
    
    def draw(self):
        print(self.question.question)
        self.question.listAnswer()
'''