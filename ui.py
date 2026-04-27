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
   
    def remove_surface(self, base_surface: Base_Surface) -> None:
        """Remove a surface from the manager."""
        if base_surface in self.layers:
            self.layers.remove(base_surface)
    
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
    def __init__(self, dimension: Vec2, pos: Vec2, grid_dimension: Vec2, manager, player):
        super().__init__(dimension, pos)
        self.manager = manager          # Reference to surface manager
        self.player = player            # Reference to the human player
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

        self._active_popup = None       # Track currently open popup
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
                value = (row + 1) * 200
                # Create a unique question (temporary hardcoded)
                q = Question(
                    problem=f"Category {col+1} Row {row+1}: What is the capital of France?",
                    options=["Paris", "London", "Berlin"],
                    answer_ind=0,
                    value=value
                )
                self.grid[row][col] = (rect, q)
    def click_at(self, pos: Vec2):
        rect, question = self.get_cell_at_pos(pos)
        if question is None or question.used:
            print("This question has already been answered.")
            return

        # Callback when user selects an answer
        def on_answer(is_correct, points):
            if is_correct:
                self.player.add_score(points)
                print(f"Correct! {self.player.name} gains ${points}. Total: ${self.player.score}")
            else:
                self.player.add_score(-points)
                print(f"Wrong! {self.player.name} loses ${points}. Total: ${self.player.score}")
            question.used = True
            # Remove popup from manager
            if self._active_popup:
                self.manager.remove_surface(self._active_popup)
                self._active_popup = None

        # Create and add popup
        popup = QuestionPopup(question, on_answer)
        self.manager.add_surface(popup)
        self._active_popup = popup
    
    def get_cell_at_pos(self, rpos: Vec2): # add edge checking
        x, y = int(rpos.x), int(rpos.y)
        col = x // self.cell_width
        row = y // self.cell_height
        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            return self.grid[row][col]
        return None, None
    
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

# ----- QuestionPopup: a modal window showing question and options -----
class QuestionPopup(Base_Surface):
    def __init__(self, question: Question, on_answer_callback):
        # Popup size and position (centered)
        popup_dim = Vec2(600, 400)
        screen = pygame.display.get_surface()
        screen_width, screen_height = screen.get_size()
        popup_pos = Vec2((screen_width - popup_dim.x) // 2, (screen_height - popup_dim.y) // 2)
        super().__init__(popup_dim, popup_pos)
        
        self.question = question
        self.on_answer_callback = on_answer_callback
        self.font_title = pygame.font.Font(None, 32)
        self.font_option = pygame.font.Font(None, 28)
        
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
            if self.font_title.size(test_line)[0] < 540:
                line = test_line
            else:
                lines.append(line)
                line = w + " "
        lines.append(line)
        
        y_offset = 50
        for line in lines:
            text = self.font_title.render(line, True, Color.white)
            self.surface.blit(text, (30, y_offset))
            y_offset += 30
        
        # Draw option buttons
        for i, rect in enumerate(self.option_rects):
            color = (80, 80, 200) if self.selected != i else (200, 200, 80)
            pygame.draw.rect(self.surface, color, rect)
            pygame.draw.rect(self.surface, Color.white, rect, 2)
            option_text = f"{chr(65+i)}. {self.question.answer[i]}"
            text_surf = self.font_option.render(option_text, True, Color.white)
            text_rect = text_surf.get_rect(center=rect.center)
            self.surface.blit(text_surf, text_rect)
        
        screen.blit(self.surface, self.pos)

    def click_at(self, pos: Vec2):
        for i, rect in enumerate(self.option_rects):
            if rect.collidepoint(pos.x, pos.y):
                self.selected = i
                is_correct = (i == self.question.answer_index)
                self.on_answer_callback(is_correct, self.question.value)
                return True  # close popup after answer
        return False
'''
class question_screen(Grid_Surface):
    def __init__(self, width, height, question):
        super().__init__(width, height)
        self.question = question
    
    def draw(self):
        print(self.question.question)
        self.question.listAnswer()
'''