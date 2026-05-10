import pygame
import random

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

Board = list[list[dict]]

import config
from sources.util import intxy
from sources.datatype.player import generate_players, Player
from sources.util import Color
from sources.llm.llm import LLMQuestionGenerator

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
            Surface_Manager.remove_surface(self)
        
    def draw(self, screen: Surface):
        screen.blit(self.surface, self.pos)
    
    def on_close(self):
        pass
    
    def time_update(self):
        pass

    def on_click(self, pos: Vec2, player: Player):
        pass

class Surface_Manager:
    layers: list[Base_Surface] = []
    main_screen: Surface = None
    
    @classmethod
    def init(cls):
        cls.main_screen = pygame.display.set_mode(config.screen_dimension, pygame.RESIZABLE)
        
        # --- Custom pointer setup ---
        pointer_img = pygame.image.load("assets/pointer.png").convert_alpha()
        w, h = pointer_img.get_size()
        cls.pointer_img = pygame.transform.smoothscale(pointer_img, (w // 8, h // 8))

    @classmethod
    def add_surface(cls, base_surface: Base_Surface) -> None:
        cls.layers.append(base_surface)

    @classmethod
    def remove_surface(cls, base_surface: Base_Surface) -> None:
        base_surface.on_close()
        
        cls.layers.remove(base_surface)

    @classmethod
    def _get_top_collision(cls, pos: Vec2) -> tuple[Base_Surface, Vec2]:
        for base_surface in reversed(cls.layers):
            if base_surface.rect.collidepoint(pos):
                rpos = pos - base_surface.pos
                return base_surface, rpos
            
            # Overshade surface shades anything behind it
            if base_surface.overshade:
                return None, None
        
        return None, None

    @classmethod
    def click_at(cls, pos: Vec2, player: Player):
        surface, rpos = cls._get_top_collision(pos)
        
        print("-------")
        print(f"Pos: {pos}, Surface: {surface}, Rpos: {rpos}")
        print(Surface_Manager.layers)
        
        if surface:
            surface.on_click(rpos, player)

    @classmethod
    def render(cls) -> None:
        # fill the screen with a color to wipe away anything from last frame
        cls.main_screen.fill(Color.black)

        for base_surface in cls.layers:
            base_surface.draw(cls.main_screen)
        
        mx, my = pygame.mouse.get_pos()
        screen_w, screen_h = cls.main_screen.get_size()
        if 0.1 <= mx < screen_w - 0.1 and 0.1 <= my < screen_h - 0.1:
            cls.main_screen.blit(cls.pointer_img, (mx, my))
        
        pygame.display.flip()
        
    def update(self) -> None:
        for surface in self.layers:
            if hasattr(surface, "time_update"):
                surface.time_update()
            
    def resize(self, new_dimension: tuple[int, int]):
        # Update screen reference and propagate resize to all surfaces
        self.main_screen = pygame.display.set_mode(new_dimension, pygame.RESIZABLE)

    @classmethod
    def update(cls) -> None:
        for base_surface in cls.layers:
            base_surface.time_update()

    @classmethod
    def resize(cls, new_dimension: tuple[int, int]):
        # Update screen reference and propagate resize to all surfaces
        cls.main_screen = pygame.display.set_mode(new_dimension, pygame.RESIZABLE)

        for surface in cls.layers:
            if hasattr(surface, "resize"):
                surface.resize(Vec2(*new_dimension))
    
    @classmethod
    def play_sound(self, filename: str, volume: float = 0.5):
        """Play a sound effect from assets/sounds folder."""
        if filename not in self.sounds:
            try:
                sound = pygame.mixer.Sound(f"assets/SFX/{filename}")
                self.sounds[filename] = sound
            except pygame.error as e:
                print(f"Error loading sound {filename}: {e}")
                return
        sound = self.sounds[filename]
        sound.set_volume(volume)
        sound.play()
                
class Game_Manager:
    players: list[Player] = []
    boards: list[Board] = []

    # Time control
    frame_frozen: int = 0
    clock = pygame.time.Clock()
    
    @classmethod
    def init(cls):
        cls.boards.append(LLMQuestionGenerator().generate_board(
            rows=5, difficulty="easy", index=int(random.uniform(0, 5))
        ))
        cls.boards.append(LLMQuestionGenerator().generate_board(
            rows=5, difficulty="hard", index=int(random.uniform(0, 5))
        ))
        
        cls.players = generate_players()
        
        pygame.mouse.set_visible(False)