import pygame
import random

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

from sources.util import intxy, blit_text, Font, Color
from sources.manager import manager, Base_Surface
from sources.datatype.question import Question
from sources.datatype.player import Player
from sources.surfaces.surface_question import Question_Surface
from sources.surfaces.surface_final import FinalJeopardy
from sources.surfaces.visual import Cutscene_Surface, Transition_Surface

from sources.llm.llm import LLMQuestionGenerator

class Grid_Surface(Base_Surface):
    def __init__(self, dimension: Vec2, pos: Vec2, grid_dimension: Vec2, players: list[Player]):
        super().__init__(dimension, pos)

        self.players = players
        self.bot_wait_until = None
        self.turn_index = 0

        self.grid_dimension = grid_dimension
        self.categories = ["History", "Science", "Literature", "Sports", "Music", "IDK"]
        
        self.current_popup: Question_Surface = None
        self.current_cell: tuple[int, int] = None # row, col

        self.screen_w, self.screen_h = intxy(dimension)

        # Load and scale background to full window
        self.background = pygame.image.load("assets/Jeopardy-BoardAlt.webp").convert()
        self.background = pygame.transform.smoothscale(self.background, (self.screen_w, self.screen_h))

        # Define margins so grid sits inside the board frame
        margin_x = int(self.screen_w * 0.175)
        margin_y = int(self.screen_h * 0.19)

        grid_w = self.screen_w - 2 * margin_x
        grid_h = self.screen_h - 1.75 * margin_y
        self.grid_area = pygame.Rect(margin_x, margin_y, grid_w, grid_h)

        # Cell dimensions based on inner grid area
        g_width, g_height = intxy(grid_dimension)
        self.cell_dimension = Vec2(
            round(self.grid_area.width / g_width),
            round(self.grid_area.height / g_height)
        )

        self.question_gen = LLMQuestionGenerator()
        self.multiplier = 1
        self._grid_init()

    def _grid_init(self):
        g_width, g_height = intxy(self.grid_dimension)
        c_width, c_height = intxy(self.cell_dimension)

        num_cols = g_width
        num_rows = g_height - 1

        board_data = self.question_gen.generate_board(self.categories, rows=num_rows)
        while len(board_data) < num_rows:
            board_data.append([{"clue":"Placeholder","options":["A"],"correct_answer":"A"} for _ in range(num_cols)])
        for r in range(num_rows):
            while len(board_data[r]) < num_cols:
                board_data[r].append({"clue":"Placeholder","options":["A"],"correct_answer":"A"})

        self.grid = [[None for _ in range(g_width)] for _ in range(g_height)]

        for row in range(num_rows):
            for col in range(num_cols):
                rect = pygame.Rect(
                    self.grid_area.left + round(col * c_width),
                    self.grid_area.top + round((row + 1) * c_height),
                    round(c_width),
                    round(c_height)
                )
                value = (row + 1) * 200
                q_data = board_data[row][col]
                q = Question(
                    problem=q_data["clue"],
                    options=q_data["options"],
                    answer_ind=q_data["options"].index(q_data["correct_answer"]),
                    value=value
                )
                self.grid[row + 1][col] = [rect, q, False, None]
    
    def advance_turn(self):
        if any(isinstance(s, Transition_Surface) for s in manager.layers):
            return

        self.turn_index = (self.turn_index + 1) % len(self.players)

        if self.players[self.turn_index].bot:
            delay_ms = int(random.uniform(750, 1750))
            self.bot_wait_until = pygame.time.get_ticks() + delay_ms

    def call_lowest_player(self):
        # Find player with least money
        lowest = min(self.players, key=lambda p: p.score)
        self.turn_index = self.players.index(lowest)

        # If it's a bot, schedule delay
        if lowest.bot:
            delay_ms = int(random.uniform(750, 1750))
            self.bot_wait_until = pygame.time.get_ticks() + delay_ms

        print(f"Double Jeopardy → {lowest.name} starts with ${lowest.score}")

    
    def time_update(self):
        # --- Round reset check ---
        def board_all_used() -> bool:
            g_width, g_height = intxy(self.grid_dimension)
            all_used = all(self.grid[r][c][2] for r in range(1, g_height) for c in range(g_width))
            
        if board_all_used():
            if self.multiplier == 1:
                manager.add_surface(Transition_Surface(mode="double"))
                self.multiplier = 2
                for row in range(1, g_height):
                    for col in range(g_width):
                        rect, q, used, flash = self.grid[row][col]
                        self.grid[row][col][2] = False
                        q.value = row * 200 * self.multiplier
            elif self.multiplier == 2:
                manager.add_surface(Transition_Surface(mode="final"))
                manager.add_surface(FinalJeopardy(Vec2(self.screen_w, self.screen_h), Vec2(0,0), self.players))
                manager.remove_surface(self)

        # --- Bot delayed selection ---
        elif self.bot_wait_until and pygame.time.get_ticks() >= self.bot_wait_until:
            current_player = self.players[self.turn_index]
            if current_player.bot:
                g_width, g_height = intxy(self.grid_dimension)
                available = [
                    (r, c)
                    for r in range(1, g_height)
                    for c in range(g_width)
                    if not self.grid[r][c][2]
                ]
                if available:
                    row, col = random.choice(available)
                    rect, question, used, flash = self.grid[row][col]
                    self.grid[row][col][3] = {
                        "color": current_player.color,
                        "start": pygame.time.get_ticks(),
                        "count": 0,
                        "player": current_player
                    }
                    self.grid[row][col][2] = True
            self.bot_wait_until = None
        
        if self.current_cell:
            row, col = self.current_cell
            current_cell = self.grid[row][col] # Mutable reference
            
            # When the flashing end, question surface appears
            if not current_cell[3]:
                self.current_popup.alpha = 255
                
            # When the popup screen is removed
            if self.current_popup not in manager.layers:
                
                # Mark cell as used
                current_cell[2] = True
                
                self.current_cell, self.current_popup = None, None
            
    def is_flashing(self) -> bool:
        g_width, g_height = intxy(self.grid_dimension)
        return any(self.grid[r][c][3] for r in range(1, g_height) for c in range(g_width))
    
    def on_click(self, pos: Vec2, player: Player):
        # Block if it's not this player's turn
        if self.players[self.turn_index] != player:
            print("Not your turn!")
            return
        
        row, col = self._get_rowcol(pos)
        
        if row == 0:
            print("Category row – not clickable.")
            return
        
        rect, question, used, flash = self.grid[row][col]

        if used:
            print("This question has already been answered.")
            return

        # Start flash animation (store player color and start time)
        flash = {
            "color": player.color, 
            "start": pygame.time.get_ticks(),
            "count": 0,
            "player": player
        }
        self.grid[row][col][3] = flash
        
        popup = Question_Surface(
            question=question,
            player=flash["player"],
            bots=self.players[1:],
            grid_surface=self
        )
        popup.alpha = 0
        
        self.current_popup = popup
        self.current_cell = (row, col)
        
        manager.add_surface(popup)

    def _get_rowcol(self, rpos: Vec2):
        x, y = intxy(rpos)
        c_width, c_height = intxy(self.cell_dimension)

        # Adjust for grid_area offset
        rel_x = x - self.grid_area.left
        rel_y = y - self.grid_area.top

        # Category row was shifted upward, so compensate
        category_offset = -20   # same value you used in draw
        rel_y -= category_offset

        # If click is outside the grid area, return invalid
        if rel_x < 0 or rel_y < 0:
            return -1, -1

        col = rel_x // c_width
        row = rel_y // c_height # Just use the grid indexes

        return row, col
    
    def draw(self, screen: Surface):
        # Draw full background first
        self.surface.blit(self.background, (2, 0))

        def draw_categories():
            c_width, c_height = intxy(self.cell_dimension)

            # Category row
            for col, category in enumerate(self.categories):
                rect = pygame.Rect(
                    self.grid_area.left + round(col * c_width),
                    self.grid_area.top - 5,
                    round(c_width),
                    round(c_height)
                )
                pygame.draw.rect(self.surface, Color.background, rect)
                pygame.draw.rect(self.surface, Color.border, rect, 2)
                text = Font.category_medium.render(category, True, Color.white)
                text_rect = text.get_rect(center=rect.center)
                self.surface.blit(text, text_rect)

        draw_categories()
        
        def draw_cell(row, col):
            rect, question, used, flash = self.grid[row][col]

            if flash:
                elapsed = (pygame.time.get_ticks() - flash["start"]) // 200

                if elapsed < 4:
                    fill_color = flash["color"] if elapsed % 2 == 0 else Color.background
                
                if elapsed >= 4:
                    self.grid[row][col][3] = None
                    fill_color = Color.greyed if used else Color.background
            else:
                fill_color = Color.greyed if used else Color.background

            pygame.draw.rect(self.surface, fill_color, rect)
            
            if not used or flash:
                question.value = row * 200 * self.multiplier
                
                blit_text(str(question.value), Font.category_large, Color.text, self.surface, rect.center)

            pygame.draw.rect(self.surface, Color.border, rect, 2)
        
        for row in range(1, int(self.grid_dimension.x)):
            for col in range(int(self.grid_dimension.y)):
                draw_cell(row, col)

        screen.blit(self.surface, self.pos)