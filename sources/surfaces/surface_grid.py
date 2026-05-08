import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

from sources.util import intxy, Font, Color
from sources.manager import manager, Base_Surface
from sources.datatype.question import Question
from sources.datatype.player import Player
from sources.surfaces.surface_question import Question_Surface

from sources.llm.llm import LLMQuestionGenerator

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
        self.question_gen = LLMQuestionGenerator()   # Initialize LLM question generator
        self.multiplier = 1
        self._grid_init()

    def _grid_init(self):
        g_width, g_height = intxy(self.grid_dimension)
        c_width, c_height = intxy(self.cell_dimension)
        
        # First row is for category titles, so actual question rows = g_height - 1
        num_cols = g_width      # number of categories (columns)
        num_rows = g_height - 1 # number of question rows (e.g., 5)
        
        # Generate questions via LLM, returns board_data[question_row][category_col]
        board_data = self.question_gen.generate_board(self.categories, rows=num_rows)
        
        # Initialize grid: [row][col] where row=0 is category row (empty for questions)
        self.grid = [[None for _ in range(g_width)] for _ in range(g_height)]
        
        # Fill question cells (skip row 0)
        for row in range(num_rows):
            for col in range(num_cols):
                rect = pygame.Rect(
                    round(col * c_width),
                    round((row + 1) * c_height),   # shift one row down for category header
                    round(c_width),
                    round(c_height)
                )
                value = (row + 1) * 200
                q_data = board_data[row][col]       # get clue, correct_answer, options
                q = Question(
                    problem=q_data["clue"],
                    options=q_data["options"],
                    answer_ind=q_data["options"].index(q_data["correct_answer"]),
                    value=value
                )
                self.grid[row + 1][col] = [rect, q, False]   # store rectangle, question, used flag
                    
    def click_at(self, pos: Vec2, player: Player):
        row, col = self._get_rowcol(pos)
        
        if row < 0:
            print("Category row – not clickable.")
            return
        
        # Convert to actual grid row (row 0 is category header)
        actual_row = row + 1
        rect, question, used = self.grid[actual_row][col]

        if used:
            print("This question has already been answered.")
            return

        # Mark cell as used → will render grey next draw
        self.grid[actual_row][col][2] = True

        popup = Question_Surface(question, player, bots=self.players[1:], grid=self)
        manager.add_surface(popup)

    def _get_rowcol(self, rpos: Vec2):
        x, y = intxy(rpos)
        c_width, c_height = intxy(self.cell_dimension)
        
        col = x // c_width
        row = y // c_height - 1
        
        return row, col
    
    def draw(self, screen: Surface):
        # Draw category row (row 0)
        c_width, c_height = intxy(self.cell_dimension)
        for col, category in enumerate(self.categories):
            rect = pygame.Rect(
                round(col * c_width),
                0,
                round(c_width),
                round(c_height)
            )
            pygame.draw.rect(self.surface, Color.background, rect)
            pygame.draw.rect(self.surface, Color.border, rect, 2)
            text = self.font.render(category, True, Color.text)
            text_rect = text.get_rect(center=rect.center)
            self.surface.blit(text, text_rect)

        g_width, g_height = intxy(self.grid_dimension)
        # Draw question cells (skip row 0, start from row 1)
        for row in range(1, g_height):
            for col in range(g_width):
                rect, question, used = self.grid[row][col]

                fill_color = Color.greyed if used else Color.background
                pygame.draw.rect(self.surface, fill_color, rect)

                if not used:
                    question.value = row * 200 * self.multiplier
                    text = self.font.render(str(question.value), True, Color.text)
                    text_rect = text.get_rect(center=rect.center)
                    self.surface.blit(text, text_rect)

                pygame.draw.rect(self.surface, Color.border, rect, 2)

        screen.blit(self.surface, self.pos)