import pygame


class game_screen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def display(self):
        for i in range(5):
            for j in range(6):
                pygame.draw.rect(game_screen, (255, 255, 255), (j*200, i*144, 220, 164), 1)

class question_screen(game_screen):
    def __init__(self, width, height, question):
        super().__init__(width, height)
        self.question = question
    
    def display(self):
        print(self.question.question)
        self.question.listAnswer()

class question(question_screen):
    def __init__(self, question, answer, answerIndex):
        self.question = question
        self.answer = answer  # list of answer (3 options)
        self.answerIndex = answerIndex

    def listAnswer(self):
        for i in range(len(self.answer)):
            print(f"{i+1}. {self.answer[i]}")

class player:
    def __init__(self, name):
        self.name = name
        self.score = 0
    
    def update_score(self, points):
        self.score += points

