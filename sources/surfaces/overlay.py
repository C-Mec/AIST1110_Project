import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import Font
from sources.manager import Base_Surface
from sources.datatype.player import Player

class ScoreOverlay(Base_Surface):
    def __init__(self, players: list[Player], grid):
        dimension = Vec2(220, 140)
        pos = Vec2(config.screen_dimension[0] - dimension.x - 10, 10)

        super().__init__(dimension, pos)

        self.surface = Surface(dimension, pygame.SRCALPHA)
        self.pos = pos
        self.rect = self.surface.get_rect(topleft=pos)

        self.players = players
        self.grid = grid
        self.font = Font.small

    def draw(self, screen: Surface):
        self.surface.fill((0, 0, 0, 0))

        for i, player in enumerate(self.players):
            # --- Render name (shifted left by 1/3 of overlay width) ---
            name_text = f"{player.name}:"
            name_render = self.font.render(name_text, True, player.color)
            name_rect = name_render.get_rect()
            name_rect.top = 10 + i * 35
            name_rect.right = self.surface.get_rect().right - self.surface.get_rect().width // 2

            # --- Render score (right aligned) ---
            score_text = f"${player.score}"
            score_render = self.font.render(score_text, True, player.color)
            score_rect = score_render.get_rect()
            score_rect.top = name_rect.top
            score_rect.right = self.surface.get_rect().right - 10

            # --- Background strip under both (draw first) ---
            bg_rect = Rect(
                name_rect.left - 5,
                name_rect.top,
                (score_rect.right - name_rect.left) + 10,
                max(name_rect.height, score_rect.height)
            )
            pygame.draw.rect(self.surface, (0, 0, 0, 128), bg_rect)

            # --- Blit text AFTER background ---
            self.surface.blit(name_render, name_rect)
            self.surface.blit(score_render, score_rect)

            # --- Arrow triangle if current turn (draw last so it's visible) ---
            if self.players[self.grid.turn_index] == player:
                arrow_tip = (bg_rect.left - 5, bg_rect.centery)
                arrow_top = (bg_rect.left - 20, bg_rect.top)
                arrow_bottom = (bg_rect.left - 20, bg_rect.bottom)
                pygame.draw.polygon(self.surface, player.color, [arrow_tip, arrow_top, arrow_bottom])

        screen.blit(self.surface, self.pos)