import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import font, Color, Font
from sources.manager import manager, Base_Surface
from sources.datatype.player import Player

class BorderFlash(Base_Surface):
    def __init__(self, player: Player, duration: int = 500):
        dimension = Vec2(*config.screen_dimension)
        pos = Vec2(0, 0)
        super().__init__(dimension, pos)

        self.overshade = False
        self.player = player
        self.start_time = pygame.time.get_ticks()
        self.duration = duration  # ms
        self.alpha = 0

    def draw(self, screen: Surface):
        elapsed = pygame.time.get_ticks() - self.start_time

        # Fade in/out logic
        cutoff = self.duration // 5
        if elapsed < cutoff:
            # Fade in
            self.alpha = int(255 * (elapsed / cutoff))
        elif elapsed < self.duration:
            # Fade out
            self.alpha = int(255 * (1 - (elapsed - cutoff) / cutoff))
        else:
            # End effect
            manager.remove_surface(self)
            return

        # Draw border flash
        flash_surface = Surface(config.screen_dimension, pygame.SRCALPHA)
        flash_surface.fill(Color.transparent)

        rgb = self.player.color

        # Draw thick border rectangle
        border_rect = flash_surface.get_rect()
        pygame.draw.rect(flash_surface, rgb, border_rect, 40)

        # Apply alpha
        flash_surface.set_alpha(self.alpha)
        screen.blit(flash_surface, (0, 0))

class Cutsence_Surface(Base_Surface):
        def __init__(self, message: str):
            super().__init__(None)
            
            self.message = message
        
        def draw(self, screen: Surface):
            self.surface.fill(Color.overlay)
            
            elapsed = (pygame.time.get_ticks() - self.create_time) / 1000
            
            if elapsed > 4:
                self.fade()
            
            if elapsed > 1:
                text_s = (font(72 * min((elapsed - 1), 3) / 3)
                          .render(self.message, None, Color.text))
                
                self.surface.blit(
                    text_s,
                    text_s.get_rect(center=self.rect.center)
                )
            
            screen.blit(self.surface, Vec2(0, 0))
                
def notify(message: str) -> None:
    manager.add_surface(Cutsence_Surface(message))