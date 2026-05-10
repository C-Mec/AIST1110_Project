import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import Font, Color
from sources.manager import Surface_Manager, Base_Surface, Game_Manager
from sources.datatype.player import Player
from sources.surfaces.surface_grid import Grid_Surface
from sources.surfaces.overlay import ScoreOverlay
from sources.surfaces.visual import Transition_Surface

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

    def resize(self, new_dimension: Vec2):
        # Resize start screen to new window size.
        self.dimension = new_dimension
        self.surface = Surface(new_dimension, pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=Vec2(0, 0))

        # Rescale background to fit new screen
        self.background = pygame.image.load("assets/Jeopardy-TitleScreen.webp").convert()
        self.background = pygame.transform.scale(self.background, (int(new_dimension.x), int(new_dimension.y)))

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
        Surface_Manager.remove_surface(self)

    def on_close(self):
        screen_w, screen_h = config.screen_dimension

        # Grid should cover the whole window, aligned with background
        grid_w, grid_h = screen_w, screen_h
        grid_pos = Vec2(0, 0)

        jeopardy = Grid_Surface(Vec2(grid_w, grid_h), grid_pos, Game_Manager.players[0])
        
        Surface_Manager.add_surface(jeopardy)
        Surface_Manager.add_surface(ScoreOverlay(jeopardy))
        Surface_Manager.add_surface(Transition_Surface(mode="jeopardy"))