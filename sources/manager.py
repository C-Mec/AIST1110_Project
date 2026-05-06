import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import intxy
from sources.datatype.player import Player
from sources.util import Color

class Base_Surface:
    def __init__(self, dimension: Vec2 = None, pos: Vec2 = Vec2(0, 0), *, isProportion = False):
        if dimension == None:
            dimension = config.screen_dimension
        
        if isProportion:
            screen_w, screen_h = config.screen_dimension
            
            dimension = Vec2(screen_w * dimension.x, screen_h * dimension.y)
            pos = Vec2(screen_w * pos.x, screen_h * pos.y)
        
        self.dimension = dimension
        self.surface = Surface(dimension, pygame.SRCALPHA) # Use SRCALPHA so transparency works
        
        self.pos = pos 
        self.rect = self.surface.get_rect(topleft=pos) # Rect on screen
        
        self.overshade = False
        
        self.create_time = pygame.time.get_ticks()

        # Transparency and fade
        self.alpha = 255       # fully opaque by default
        self._fade_lasttime = None # Not initialized by default

    def fade(self, speed: int = 64):
        """Fade this surface by the amount in speed per second."""
        
        if self._fade_lasttime is None:
            self._fade_lasttime = pygame.time.get_ticks()
        
        elapsed_sec = (pygame.time.get_ticks() - self._fade_lasttime) / 1000
        self.alpha -= speed * elapsed_sec
        
        self._fade_lasttime = pygame.time.get_ticks()
        
        self.surface.set_alpha(self.alpha)

        if self.alpha <= 0:
            manager.remove_surface(self)
        
    def draw(self, screen: Surface):
        screen.blit(self.surface, self.pos)

    def click_at(self, pos: Vec2, player: Player):
        pass

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