import pygame
import random
import math

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import Color, Font
from sources.manager import manager, Base_Surface, Game_Manager
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
    
    def resize(self, new_dimension: Vec2):
        # Resize flash surface to new window size
        self.dimension = new_dimension
        self.surface = Surface(new_dimension, pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=self.pos)

class TimeFroze(Base_Surface):
    def __init__(self, duration: int):
        super().__init__()
        
        self.overshade = True
        
        # Duration in ms
        self.duration = duration
        
    def time_update(self):
        assert not any(isinstance(s, Transition_Surface) for s in manager.layers)
        
        Game_Manager.frame_frozen = pygame.time.get_ticks() - self.create_time
        
        if pygame.time.get_ticks() - self.create_time > self.duration:
            manager.remove_surface(self)
    
    def on_close(self):
        Game_Manager.frame_frozen = 0

def time_froze(time: int):
    manager.add_surface(TimeFroze(time))

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
    
    def time_update(self):
        assert not any(isinstance(s, Transition_Surface) for s in manager.layers)
        
        Game_Manager.frame_frozen = pygame.time.get_ticks() - self.create_time
    
    def on_close(self):
        Game_Manager.frame_frozen = 0
        
    def resize(self, new_dimension: Vec2):
        # Resize cutscene overlay to new window size
        self.dimension = new_dimension
        self.surface = Surface(new_dimension, pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=self.pos)

class Transition_Surface(Base_Surface):
    def __init__(self, mode: str = "jeopardy"):
        super().__init__(Vec2(*config.screen_dimension), Vec2(0, 0))
        self.mode = mode.lower()
        self.create_time = pygame.time.get_ticks()

        # Load the correct image depending on mode
        if self.mode == "dailydouble":
            self.image = pygame.image.load("assets/Jeopardy-DailyDouble.webp").convert_alpha()
        elif self.mode == "double":
            self.image = pygame.image.load("assets/Jeopardy-DoubleJeopardy.png").convert_alpha()
        elif self.mode == "final":
            self.image = pygame.image.load("assets/Jeopardy-FinalJeopardy.webp").convert_alpha()
        else:
            self.image = pygame.image.load("assets/Jeopardy-Jeopardy.webp").convert_alpha()

        # Scale image to full screen
        self.image = pygame.transform.smoothscale(self.image, config.screen_dimension)
        self.image_rect = self.image.get_rect(center=self.rect.center)

    def _bounce(self, t: float) -> int:
        bounce_period = 0.6
        bounce_index = int(t // bounce_period) + 1
        local_t = (t % bounce_period) / bounce_period

        amplitude = 200 * (0.5 ** bounce_index)
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
        elif self.mode in ("jeopardy", "double", "dailydouble"):
            # Bounce above baseline
            t = elapsed - 1.0
            y_offset = -self._bounce(t)
        elif self.mode == "final":
            # Drop then shake
            if elapsed < 1.6:
                y_offset = -self._bounce(elapsed - 1.0)
            else:
                t = elapsed - 1.6
                x_offset = int(20 * math.sin(25 * t))

        rect = self.image.get_rect(center=(self.rect.centerx + x_offset,
                                           self.rect.centery + y_offset))
        self.surface.blit(self.image, rect)
        screen.blit(self.surface, self.pos)

        if elapsed > 3:
            self.fade(128)
    
    def time_update(self):
        assert not any(isinstance(s, Cutscene_Surface) for s in manager.layers)
        
        Game_Manager.frame_frozen = pygame.time.get_ticks() - self.create_time
    
    def on_close(self):
        Game_Manager.frame_frozen = 0
        
    def resize(self, new_dimension: Vec2):
        # Resize transition screen and rescale image
        self.dimension = new_dimension
        self.surface = Surface(new_dimension, pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=self.pos)

        # Reload and rescale image to new dimension
        if self.mode == "dailydouble":
            self.image = pygame.image.load("assets/Jeopardy-DailyDouble.webp").convert_alpha()
        elif self.mode == "double":
            self.image = pygame.image.load("assets/Jeopardy-DoubleJeopardy.png").convert_alpha()
        elif self.mode == "final":
            self.image = pygame.image.load("assets/Jeopardy-FinalJeopardy.webp").convert_alpha()
        else:
            self.image = pygame.image.load("assets/Jeopardy-Jeopardy.webp").convert_alpha()

        self.image = pygame.transform.smoothscale(self.image, (int(new_dimension.x), int(new_dimension.y)))
        self.image_rect = self.image.get_rect(center=self.rect.center)


class FloatingText:
    def __init__(self, player: Player, amount: int):
        self.player = player
        self.amount = amount
        self.color = player.color
        self.font = player.overlay.font
        self.alpha = 255
        self.start_time = pygame.time.get_ticks()
        self.duration = 1500  # ms lifetime

        # Get starting position directly from overlay
        score_rect = player.overlay.get_score_rect(player)
        self.pos = Vec2(score_rect.right, score_rect.centery)

        self.direction = "up" if amount > 0 else "down"

    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        self.pos.y += -0.3 if self.direction == "up" else 0.3
        self.alpha = max(0, 255 * (1 - progress))
        return progress < 1.0

    def draw(self, surface: Surface):
        text = f"{'+' if self.amount > 0 else ''}{self.amount}"
        render = self.font.render(text, True, self.color)
        render.set_alpha(int(self.alpha))
        rect = render.get_rect()
        rect.centery = int(self.pos.y)
        rect.right = int(self.pos.x)  # keep right aligned
        surface.blit(render, rect)

def notify(message: str) -> None:
    manager.add_surface(Cutscene_Surface(message))