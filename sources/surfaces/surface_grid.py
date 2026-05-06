import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

from sources.util import intxy, Font, Color
from sources.manager import manager, Base_Surface
from sources.datatype.question import Question
from sources.datatype.player import Player
from sources.surfaces.surface_question import Question_Surface

class Grid_Surface(Base_Surface):
    def __init__(self, dimension: Vec2, pos: Vec2, grid_dimension: Vec2, players: list[Player]):
        super().__init__(dimension, pos)
        
        self.players = players
        self.font = Font.large
        self.grid_dimension = grid_dimension
        self.categories = ["History", "Science", "Literature", "Sports", "Music", "IDK"]
        
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
                    round((row + 1) * c_height),
                    round(c_width),
                    round(c_height)
                )
                
                value = (row + 1) * 200
                ques = Question.sample(col, row, value)
                used = False
                
                self.grid[row][col] = [rect, ques, used]
                
    def click_at(self, pos: Vec2, player: Player):
        row, col = self._get_rowcol(pos)
        
        if row < 0:
            print("Category row – not clickable.")
            return
        
        rect, question, used = self.grid[row][col]

        if used:
            print("This question has already been answered.")
            return

        # Mark cell as used → will render grey next draw
        self.grid[row][col][2] = True

        popup = Question_Surface(question, player, bots=self.players[1:])
        manager.add_surface(popup)

    def _get_rowcol(self, rpos: Vec2):
        x, y = intxy(rpos)
        c_width, c_height = intxy(self.cell_dimension)
        
        col = x // c_width
        row = y // c_height - 1
        
        return row, col
    
    def draw(self, screen: Surface):
        # Draw category row
        c_width, c_height = intxy(self.cell_dimension)
        for col, category in enumerate(self.categories):
            rect = pygame.Rect(
                round(col * c_width),
                0,   # ✅ top row
                round(c_width),
                round(c_height)
            )
            pygame.draw.rect(self.surface, Color.background, rect)
            pygame.draw.rect(self.surface, Color.border, rect, 2)

            text = self.font.render(category, True, Color.text)
            text_rect = text.get_rect(center=rect.center)
            self.surface.blit(text, text_rect)

        
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