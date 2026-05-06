import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import Font
from sources.manager import Base_Surface
from sources.datatype.player import Player

class ScoreOverlay(Base_Surface):
    def __init__(self, players: list[Player]):
        dimension = Vec2(180, 110)  # size of the rectangle 
        pos = Vec2(config.screen_dimension[0] - dimension.x - 10, 10)

        super().__init__(dimension, pos)

        # Important: create with SRCALPHA so alpha values are respected
        self.surface = Surface(dimension, pygame.SRCALPHA)
        self.pos = pos
        self.rect = self.surface.get_rect(topleft=pos)

        self.players = players
        self.font = Font.small

    def draw(self, screen: Surface):
        # Clear surface each frame
        self.surface.fill((0, 0, 0, 0))

        # Semi-transparent background (alpha = 180)
        pygame.draw.rect(self.surface, (0, 0, 0, 180), self.surface.get_rect())
        
        # Player scores (right-aligned)
        for i, player in enumerate(self.players):
            text = f"{player.name}: ${player.score}"
            # Convert hex to RGB before rendering
            rendered = self.font.render(text, True, player.color)
            text_rect = rendered.get_rect()
            text_rect.top = 10 + i * 35
            text_rect.right = self.surface.get_rect().right - 10
            self.surface.blit(rendered, text_rect)


        # Blit overlay onto main screen
        screen.blit(self.surface, self.pos)