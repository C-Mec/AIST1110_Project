import pygame

class Color:
    white = (255, 255, 255)
    blue = (70, 130, 200)
    black = (0, 0, 0)

class Grid_Surface:
    def __init__(self, width, height):
        self.surface = pygame.Surface((width, height))
        self.grid = []
        self.cell_rects = []   # store (rect, row, col)
        self.font = pygame.font.Font(None, 36)
        self._create_sample_questions()
    def get_cell_at_pos(self, x, y):
        """Return (row, col, Question) if (x,y) inside a cell, else None"""
        for rect, row, col in self.cell_rects:
            if rect.collidepoint(x, y):
                return (row, col, self.questions[row][col])
        return None
    
    def draw(self):
        w, h = self.surface.get_size()
        cell_w = w / 6
        cell_h = h / 5
        self.cell_rects.clear()

        for row in range(5):
            for col in range(6):
                x = round(col * cell_w)
                y = round(row * cell_h)
                rect = pygame.Rect(x, y, round(cell_w), round(cell_h))
                self.cell_rects.append((rect, row, col))

                # Draw cell background
                pygame.draw.rect(self.surface, Color.blue, rect)
                # Draw border
                pygame.draw.rect(self.surface, Color.white, rect, 2)

                # Draw dollar value
                value = (row + 1) * 200
                text_surf = self.font.render(f"${value}", True, Color.white)
                text_rect = text_surf.get_rect(center=rect.center)
                self.surface.blit(text_surf, text_rect)
                
                pygame.draw.rect(self.surface, Color.white, rect, 1)
    def _create_sample_questions(self):
        """Create temporary 5x6 questions (later replace with ChatGPT)"""
        self.questions = []
        for row in range(5):
            row_q = []
            for col in range(6):
                value = (row + 1) * 200
                q = Question(
                    question=f"Sample Q for row {row+1}, col {col+1}?",
                    options=["Answer A", "Answer B", "Answer C"],
                    answer_ind=0,
                    value=value
                )
                row_q.append(q)
            self.questions.append(row_q)
    '''
class question_screen(Grid_Surface):
    def __init__(self, width, height, question):
        super().__init__(width, height)
        self.question = question
    
    def draw(self):
        print(self.question.question)
        self.question.listAnswer()
'''

class Question:
    def __init__(self, question: str, options: list[str], answer_ind: int, value: int):
        self.question = question
        self.answer = options
        self.answer_index = answer_ind
        self.value = value
        self.used = False

    def listAnswer(self):
        for i in range(len(self.answer)):
            print(f"{i+1}. {self.answer[i]}")

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
    
    def add_score(self, points):
        self.score += points
