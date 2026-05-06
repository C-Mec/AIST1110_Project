import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import Font, Color
from sources.manager import manager, Base_Surface
from sources.datatype.player import Player

class StartScreen(Base_Surface):
    def __init__(self):
        # Full screen overlay
        dimension = Vec2(*config.screen_dimension)
        super().__init__(dimension)

        self.overshade = True  # blocks interaction until dismissed
        self.title_font = Font.extralarge
        self.info_font = Font.large

    def draw(self, screen: Surface):
        # Fill background
        self.surface.fill(Color.background)

        # Title
        title_text = self.title_font.render("JEOPARDY!", True, Color.text)
        title_rect = title_text.get_rect(center=(self.dimension.x // 2, self.dimension.y // 3))
        self.surface.blit(title_text, title_rect)

        # Info
        info_text = self.info_font.render("Press any key or click to start", True, Color.text)
        info_rect = info_text.get_rect(center=(self.dimension.x // 2, self.dimension.y // 2))
        self.surface.blit(info_text, info_rect)
        
        screen.blit(self.surface, Vec2(0, 0))

    def click_at(self, pos: Vec2, player: Player):
        # Remove start screen when clicked
        manager.remove_surface(self)

    def handle_key(self, event):
        # Remove start screen when any key pressed
        manager.remove_surface(self)