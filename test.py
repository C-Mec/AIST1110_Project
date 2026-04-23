class question:
    def __init__(self, question, answer, answerIndex):
        self.question = question
        self.answer = answer  # list of answer (4 options)
        self.answerIndex = answerIndex

    def listAnswer(self):
        for i in range(len(self.answer)):
            print(f"{i+1}. {self.answer[i]}")



