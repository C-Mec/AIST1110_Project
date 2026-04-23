import pygame

class Color:
    white = (255, 255, 255)

class Grid_Surface:
    def __init__(self, width, height):
        self.surface = pygame.Surface((width, height))
        self.grid = []
    
    def draw(self):
        # Portion Coordinate
        w, h = self.surface.get_size()
        cell_w = w / 6
        cell_h = h / 5
        
        for row in range(5):
            for col in range(6):
                rect = pygame.Rect(
                    round(col * cell_w),
                    round(row * cell_h),
                    round(cell_w),
                    round(cell_h)
                )
                
                pygame.draw.rect(self.surface, Color.white, rect, 1)

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
    def __init__(self, question: str, options: list[str], answer_ind: int):
        self.question = question
        self.answer = options
        self.answer_index = answer_ind

    def listAnswer(self):
        for i in range(len(self.answer)):
            print(f"{i+1}. {self.answer[i]}")

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
    
    def add_score(self, points):
        self.score += points