import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import random

import config

def intxy(vec: Vec2) -> tuple[int, int]:
    return round(vec.x), round(vec.y)

def font(size: int) -> pygame.font.Font:
    # Use width for auto-scaling
    size = round(size * (config.screen_dimension.x / 1280))
    return pygame.font.Font(None, size)

class Font:
    small = font(24)
    large = font(36)
    extralarge = font(72)
    medium = font(28)
    
class Color:
    border = "#000000"   #"#FFFFFF"
    text = "#f6a53a"   #"#FFFFFF"
    background = "#051c96"   #4682C8"
    black = "#000000"
    white = "#FFFFFF"
    greyed = "#808080"
    
    correct = "#3CB371"  # green
    wrong = "#DC143C"  # red
    
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