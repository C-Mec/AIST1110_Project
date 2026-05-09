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
        self.info_font = Font.logo_large

        # Load the Jeopardy title image
        self.background = pygame.image.load("assets/Jeopardy-TitleScreen.webp").convert()
        # Scale to fit screen
        self.background = pygame.transform.scale(self.background, config.screen_dimension)

    def draw(self, screen: Surface):
        # Draw background image
        self.surface.blit(self.background, (0, 0))

        # Overlay info text
        info_text = self.info_font.render("Press any key or click to start", True, Color.text)
        info_rect = info_text.get_rect(center=(self.dimension.x // 2, self.dimension.y * 3 // 4))
        self.surface.blit(info_text, info_rect)

        screen.blit(self.surface, Vec2(0, 0))

    def on_click(self, pos: Vec2, player: Player):
        # Remove start screen when clicked
        manager.remove_surface(self)

    def handle_key(self, event):
        # Remove start screen when any key pressed
        manager.remove_surface(self)
