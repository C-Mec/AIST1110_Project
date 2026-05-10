class Question:
    def __init__(self, problem: str, options: list[str], answer_ind: int, value: int, is_daily: bool):
        self.problem = problem
        self.options = options
        self.answer_index = answer_ind
        self.value = value
        self.used = False
        self.is_daily = is_daily

    def listAnswer(self):
        for i in range(len(self.options)):
            print(f"{i+1}. {self.options[i]}")
    
    @staticmethod
    def sample(col: int, row: int, value: int):
        return Question(
            problem=f"Category {col+1} Row {row+1}: What is the capital of France?",
            options=["Paris", "London", "Berlin"],
            answer_ind=0,
            value=value
        )