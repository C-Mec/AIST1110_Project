import pygame
import random
import math

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

class Cutscene_Surface(Base_Surface):
    def __init__(self, message: str):
        super().__init__(None)
        
        self.message = message
        self.base_font = pygame.font.Font(None, 144)
        self.text_surface = self.base_font.render(self.message, True, Color.text)

    def draw(self, screen: Surface):
        self.surface.fill(Color.overlay)

        elapsed = (pygame.time.get_ticks() - self.create_time) / 1000

        if elapsed > 4:
            self.fade(128)

        if elapsed > 1:
            # Scale factor: grow to full size in 2s
            scale_factor = min((elapsed - 1) / 2, 1.0)

            # Target size is half of the oversampled surface (so final = crisp 72px)
            target_w = int(self.text_surface.get_width() * scale_factor * 0.5)
            target_h = int(self.text_surface.get_height() * scale_factor * 0.5)

            if target_w > 0 and target_h > 0:
                scaled = pygame.transform.smoothscale(self.text_surface, (target_w, target_h))
                rect = scaled.get_rect(center=self.rect.center)
                self.surface.blit(scaled, rect)

        screen.blit(self.surface, self.pos)

class Transition_Surface(Base_Surface):
    def __init__(self, message: str, mode: str = "jeopardy"):
        super().__init__(Vec2(*config.screen_dimension), Vec2(0, 0))
        self.message = message
        self.mode = mode.lower()
        self.create_time = pygame.time.get_ticks()

        # Pre-render text
        self.font = pygame.font.Font(None, 96)
        self.text_surface = self.font.render(self.message, True, Color.text)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def _bounce(self, t: float) -> int:
        bounce_period = 0.6
        bounce_index = int(t // bounce_period) + 1
        local_t = (t % bounce_period) / bounce_period

        # Height decays exponentially with bounce index
        amplitude = 200 * (0.5 ** bounce_index)

        # Parabolic arc: starts at baseline (0), peaks at amplitude, returns to baseline
        y = amplitude * (1 - (2 * local_t - 1) ** 2)

        return int(y)

    def draw(self, screen: Surface):
        self.surface.fill(Color.overlay)
        elapsed = (pygame.time.get_ticks() - self.create_time) / 1000.0

        y_offset = 0
        x_offset = 0

        if elapsed < 1.0:
            # Drop in
            progress = elapsed / 1.0
            y_offset = -self.rect.height * (1 - progress)
        elif self.mode in ("jeopardy", "double"):
            # Bounce above baseline
            t = elapsed - 1.0
            y_offset = -self._bounce(t)   # negative so it goes upward only
        elif self.mode == "final":
            # Drop then shake
            if elapsed < 1.6:
                y_offset = -self._bounce(elapsed - 1.0)
            else:
                t = elapsed - 1.6
                x_offset = int(20 * math.sin(25 * t))

        rect = self.text_surface.get_rect(center=(self.rect.centerx + x_offset,
                                                  self.rect.centery + y_offset))
        self.surface.blit(self.text_surface, rect)
        screen.blit(self.surface, self.pos)
        
        if elapsed > 4:
            self.fade(128)

def notify(message: str) -> None:
    manager.add_surface(Cutscene_Surface(message))