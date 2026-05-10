import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import Font, intxy
from sources.manager import Base_Surface, Game_Manager
from sources.datatype.player import Player
from sources.surfaces.visual import FloatingText

class ScoreOverlay(Base_Surface):
    def __init__(self, grid_surface):
        dimension = Vec2(220, 140)
        pos = Vec2(config.screen_dimension[0] - dimension.x - 10, 10)
        super().__init__(dimension, pos)

        self.font = Font.category_small
        self.floating_texts = []
        
        self.grid_surface = grid_surface
        self.grid_surface.overlay_surface = self # Reference

        # give each player a reference back to this overlay
        for p in Game_Manager.players:
            p.overlay = self

    def spawn_floating_text(self, player, amount):
        ft = FloatingText(player, amount)
        self.floating_texts.append(ft)
    
    def get_score_rect(self, player: Player) -> Rect:
        idx = Game_Manager.players.index(player)
        name_top = 10 + idx * 35

        score_text = f"${player.score}"
        score_render = self.font.render(score_text, True, player.color)
        score_rect = score_render.get_rect()
        score_rect.top = name_top
        score_rect.right = self.surface.get_rect().right - 10
        return score_rect
    
    def resize(self, new_dimension: Vec2):
        screen_w, screen_h = intxy(new_dimension)

        # Keep same overlay size, but move to new top-right
        self.pos = Vec2(screen_w - self.dimension.x - 10, 10)

        # Recreate surface buffer
        self.surface = Surface(self.dimension, pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=self.pos)
    
    def draw(self, screen: Surface):
        self.surface.fill((0, 0, 0, 0))

        for i, player in enumerate(Game_Manager.players):
            # render name
            name_text = f"{player.name}:"
            name_render = self.font.render(name_text, True, player.color)
            name_rect = name_render.get_rect()
            name_rect.top = 10 + i * 35
            name_rect.right = self.surface.get_rect().right - self.surface.get_rect().width // 2

            # render score
            score_text = f"${player.score}"
            score_render = self.font.render(score_text, True, player.color)
            score_rect = score_render.get_rect()
            score_rect.top = name_rect.top
            score_rect.right = self.surface.get_rect().right - 10

            # background strip
            bg_rect = Rect(
                name_rect.left - 5,
                name_rect.top - 2,
                (score_rect.right - name_rect.left) + 10,
                max(name_rect.height, score_rect.height) + 4
            )
            pygame.draw.rect(self.surface, (0, 0, 0, 200), bg_rect)

            # blit text
            self.surface.blit(name_render, name_rect)
            self.surface.blit(score_render, score_rect)

            # arrow
            if self.grid_surface.current_player == player:
                arrow_tip = (bg_rect.left - 5, bg_rect.centery)
                arrow_top = (bg_rect.left - 20, bg_rect.top)
                arrow_bottom = (bg_rect.left - 20, bg_rect.bottom)
                pygame.draw.polygon(self.surface, player.color, [arrow_tip, arrow_top, arrow_bottom])

        # draw floating texts
        for ft in self.floating_texts[:]:
            if not ft.update():
                self.floating_texts.remove(ft)
            else:
                ft.draw(self.surface)

        screen.blit(self.surface, self.pos)