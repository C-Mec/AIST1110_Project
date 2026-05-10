import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import random

import config

def intxy(vec: Vec2) -> tuple[int, int]:
    return round(vec.x), round(vec.y)

def now_is_time(time: int):
    from sources.manager import Game_Manager
    
    return pygame.time.get_ticks() - time - Game_Manager.frame_frozen > 0

def make_font(path: str, size: int) -> pygame.font.Font:
    """Load a font file and auto-scale based on screen width."""
    scaled_size = round(size * (config.screen_dimension.x / 1280))
    return pygame.font.Font(path, scaled_size)

class Font:
    # Define paths to your font files
    swiss911 = "assets/fonts/Swiss 911 Compressed Regular.otf"
    korinna  = "assets/fonts/itc-korinna-std/ITC Korinna Regular.otf"
    gyparody = "assets/fonts/gyparody.ttf"

    # Category / board values
    category_small  = make_font(swiss911, 24)
    category_medium = make_font(swiss911, 36)
    category_large  = make_font(swiss911, 48)

    # Clue text
    clue_small  = make_font(korinna, 20)
    clue_medium = make_font(korinna, 28)
    clue_large  = make_font(korinna, 36)

    # Logo / transitions
    logo_medium = make_font(gyparody, 60)
    logo_large  = make_font(gyparody, 72)
    logo_huge   = make_font(gyparody, 120)
    
class Color:
    border = "#D49E9E"   #"#FFFFFF"
    text = "#f6a53a"   #"#FFFFFF"
    shadow = "#241B0F"
    
    background = "#051c96"   #4682C8"
    black = "#000000"
    white = "#FFFFFF"
    greyed = "#808080"
    
    correct = "#3CB371"  # green
    wrong = "#DC143C"  # red
    
    buzz_light = "#557ABE"
    buzz_dark = "#2927C4"
    
    timer = "#50C8C8"
    
    overlay = "#000000B4"
    transparent = "#00000000"
    
    palette = [
        "#4287F5", "#3CB371", "#DC143C", "#FFD700", "#FF69B4",
        "#8A2BE2", "#FF8C00", "#00CED1", "#ADFF2F", "#FF4500",
        "#7FFF00", "#FF1493", "#20B2AA", "#FF6347", "#9370DB",
        "#40E0D0", "#FFB6C1", "#6A5ACD", "#00FA9A", "#FF00FF"
    ]
    
    @staticmethod
    def assign_colors(players):
        """Randomly assign distinct colors from palette to players."""
        chosen = random.sample(Color.palette, len(players))
        for player, color in zip(players, chosen):
            player.color = color

def blit_text_with_center(text: str, font: pygame.font.Font, color: Color, screen: Surface, centerPos):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=centerPos)
    screen.blit(text_surface, text_rect)