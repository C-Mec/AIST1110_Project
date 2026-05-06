import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import intxy
from sources.datatype.player import Player
from sources.util import Color

class Base_Surface:
    def __init__(self, dimension: Vec2, pos: Vec2 = Vec2(0, 0), isProportion = False):
        if isProportion:
            w_ratio, h_ratio = dimension
            screen_w, screen_h = config.screen_dimension
            dimension = Vec2(screen_w * w_ratio, screen_h * h_ratio)
        
        self.pos = pos
        # Use SRCALPHA so transparency works
        self.surface = Surface(dimension, pygame.SRCALPHA)
        
        self.overshade = False
        self.dimension = dimension
        self.rect = self.surface.get_rect(topleft=pos) # Rect on screen

        # Transparency and fade
        self.alpha = 255       # fully opaque by default
        self.fading = False    # fade disabled by default
        self.fade_speed = 10   # how fast alpha decreases per frame

    def draw(self, screen: Surface):
        # Apply alpha before blitting
        self.surface.set_alpha(self.alpha)
        screen.blit(self.surface, self.pos)

        # Handle fade progression
        if self.alpha <= 0:
            manager.remove_surface(self)
        if self.fading:
            self.alpha -= self.fade_speed

    def click_at(self, pos: Vec2, player: Player):
        pass

    def start_fade(self, speed: int = 10):
        """Begin fading out this surface."""
        self.fading = True
        self.fade_speed = speed

class Surface_Manager:
    def __init__(self):
        pass
    
    def init(self, main_screen: Surface):
        '''The runtime init.'''
        
        self.main_screen = main_screen

        # A stash in which index = z-axis
        self.layers: list[Base_Surface] = []
    
    def add_surface(self, base_surface: Base_Surface) -> None: 
        self.layers.append(base_surface)
   
    def remove_surface(self, base_surface: Base_Surface) -> None:
        self.layers.remove(base_surface)
    
    def get_top_collision(self, pos: Vec2) -> tuple[Base_Surface, Vec2]:
        for base_surface in reversed(self.layers):
            if base_surface.rect.collidepoint(pos):
                rpos = pos - base_surface.pos
                return base_surface, rpos
            
            # Overshade surface shades anything behind it
            if base_surface.overshade:
                return None, None
        
        return None, None
    
    def render(self) -> None:
        # fill the screen with a color to wipe away anything from last frame
        self.main_screen.fill(Color.black)

        for base_surface in self.layers:
            base_surface.draw(self.main_screen)
        
        pygame.display.flip()

# The project-wise global instance of surface manager
# Needs to be set in main.py
manager = Surface_Manager()