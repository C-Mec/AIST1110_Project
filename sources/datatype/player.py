from sources.util import Color

class Player:
    def __init__(self, name: str, color: tuple[int, int, int], bot: bool):
        self.name = name
        self.score = 0
        self.color = color  # RGB tuple
        self.bot = bot
        self.overlay = None
        self.wager = 0

    def add_score(self, amount: int):
        self.score += amount
        if self.overlay:
            self.overlay.spawn_floating_text(self, amount)
        
        
def generate_players():
    # Create a human player
    player = Player("Human", None, False)

    # Create 2 AI players
    bot1 = Player("TEMP1", None, True)
    bot2 = Player("TEMP2", None, True)

    # Collect them
    players = [player, bot1, bot2]

    # Assign colors
    Color.assign_colors(players)

    return players