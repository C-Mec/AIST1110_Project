import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import config
from sources.util import intxy
from sources.datatype.player import generate_players, Player
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
    
    def on_close(self):
        pass
    
    def time_update(self):
        pass

    def on_click(self, pos: Vec2, player: Player):
        pass

class Surface_Manager:
    def __init__(self):
        pass
    
    def init(self, main_screen: Surface):
        '''The runtime init.'''
        
        self.main_screen = main_screen

        # A stash in which index = z-axis
        self.layers: list[Base_Surface] = []
        
        # --- Custom pointer setup ---
        pointer_img = pygame.image.load("assets/pointer.png").convert_alpha()
        w, h = pointer_img.get_size()
        self.pointer_img = pygame.transform.smoothscale(pointer_img, (w // 8, h // 8))
    
    def add_surface(self, base_surface: Base_Surface) -> None: 
        self.layers.append(base_surface)
   
    def remove_surface(self, base_surface: Base_Surface) -> None:
        base_surface.on_close()
        
        self.layers.remove(base_surface)
    
    def _get_top_collision(self, pos: Vec2) -> tuple[Base_Surface, Vec2]:
        for base_surface in reversed(self.layers):
            if base_surface.rect.collidepoint(pos):
                rpos = pos - base_surface.pos
                return base_surface, rpos
            
            # Overshade surface shades anything behind it
            if base_surface.overshade:
                return None, None
        
        return None, None

    def click_at(self, pos: Vec2, player: Player):
        surface, rpos = self._get_top_collision(pos)
        
        print("-------")
        print(f"Pos: {pos}, Surface: {surface}, Rpos: {rpos}")
        print(manager.layers)
        
        if surface:
            surface.on_click(rpos, player)
    
    def render(self) -> None:
        # fill the screen with a color to wipe away anything from last frame
        self.main_screen.fill(Color.black)

        for base_surface in self.layers:
            base_surface.draw(self.main_screen)
        
        mx, my = pygame.mouse.get_pos()
        screen_w, screen_h = self.main_screen.get_size()
        if 0.1 <= mx < screen_w - 0.1 and 0.1 <= my < screen_h - 0.1:
            self.main_screen.blit(self.pointer_img, (mx, my))
        
        pygame.display.flip()
        
    def update(self) -> None:
        for surface in self.layers:
            if hasattr(surface, "time_update"):
                surface.time_update()
            
    def resize(self, new_dimension: tuple[int, int]):
        # Update screen reference and propagate resize to all surfaces
        self.main_screen = pygame.display.set_mode(new_dimension, pygame.RESIZABLE)

        for surface in self.layers:
            if hasattr(surface, "resize"):
                surface.resize(Vec2(*new_dimension))
                
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
    frame_frozen: int = 0
    
    @classmethod
    def init(cls) -> list[Player]:
        cls.players = generate_players()
        return cls.players
                
# The project-wise global instance of surface manager
# Needs to be set in main.py
manager = Surface_Manager()