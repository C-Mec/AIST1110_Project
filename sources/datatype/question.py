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