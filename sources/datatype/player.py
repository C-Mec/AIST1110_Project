from sources.util import Color

class Player:
    def __init__(self, name: str, color: tuple[int, int, int]):
        self.name = name
        self.score = 0
        self.color = color  # RGB tuple

    def add_score(self, amount: int):
        self.score += amount
        
def init_players():
    # Create a human player
    player = Player("Human", None)

    # Create 2 AI players
    bot1 = Player("TEMP1", None)
    bot2 = Player("TEMP2", None)

    # Collect them
    players = [player, bot1, bot2]

    # Assign colors
    Color.assign_colors(players)

    return players