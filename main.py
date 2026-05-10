import warnings
import os

# Ignore Loading Warning in Console
warnings.filterwarnings( 
    "ignore",
    message = "Your system is avx2.*",
    category = RuntimeWarning,
)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
pygame.init()

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

from dotenv import load_dotenv
load_dotenv()

import config
from sources.manager import Surface_Manager, Game_Manager
from sources.surfaces.surface_start import StartScreen
from sources.surfaces.overlay import ScoreOverlay
from sources.surfaces.surface_question import Question_Surface
from sources.surfaces.surface_final import FinalJeopardy
from sources.surfaces.visual import Cutscene_Surface, Transition_Surface

Game_Manager.init()
Surface_Manager.init()
Surface_Manager.add_surface(StartScreen())

running = True
while running:
    for event in pygame.event.get():
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False
        
        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            config.screen_dimension = (event.w, event.h)

            # Let the manager handle resizing
            Surface_Manager.resize(config.screen_dimension)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left Click
            pos = Vec2(event.pos)
            
            human = Game_Manager.players[0]
            Surface_Manager.click_at(pos, human)
        
        if event.type == pygame.KEYDOWN:
            print(f"Keydown  {event.unicode}")
            for surface in Surface_Manager.layers:
                if isinstance(surface, FinalJeopardy):
                    surface.handle_event(event)

    # Render all surfaces in manager by their z-axis order
    Surface_Manager.render()
    
    # Update all the surfaces for realtime changes
    Surface_Manager.update()
    
    # fps
    Game_Manager.clock.tick(60)

pygame.quit()