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
clock = pygame.time.Clock()

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

from dotenv import load_dotenv
load_dotenv()

import config
from sources.manager import manager
from sources.datatype.player import init_players
from sources.surfaces.surface_start import StartScreen
from sources.surfaces.surface_grid import Grid_Surface
from sources.surfaces.overlay import ScoreOverlay
from sources.surfaces.surface_question import Question_Surface
from sources.surfaces.surface_final import FinalJeopardy
from sources.surfaces.visual import Cutscene_Surface, Transition_Surface

# Create a resizable window
main_screen = pygame.display.set_mode(config.screen_dimension, pygame.RESIZABLE)
manager.init(main_screen)

# Init players
players = init_players()
player = players[0]

# Add start screen before grid
start_screen = StartScreen()
manager.add_surface(start_screen)

jeopardy_grid = None
score_overlay = None
final_surface = None

# Pointer
pygame.mouse.set_visible(False)

running = True
while running:
    # poll for events
    for event in pygame.event.get():
        
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False
        
        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            config.screen_dimension = (event.w, event.h)

            # Let the manager handle resizing
            manager.resize(config.screen_dimension)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left Click
            pos = Vec2(event.pos)

            surface, rpos = manager.get_top_collision(pos)
            
            print("-------")
            print(f"Pos: {pos}, Surface: {surface}, Rpos: {rpos}")
            print(manager.layers)
            
            if surface is not None:
                surface.on_click(rpos, player)
        
        if event.type == pygame.KEYDOWN:
            print(f"Keydown  {event.unicode}")
            for surface in manager.layers:
                if isinstance(surface, FinalJeopardy):
                    surface.handle_event(event)
                
    if not any(isinstance(s, StartScreen) for s in manager.layers):
        if jeopardy_grid is None and not any(isinstance(s, Transition_Surface) for s in manager.layers):
            screen_w, screen_h = config.screen_dimension

            # Grid should cover the whole window, aligned with background
            grid_w, grid_h = screen_w, screen_h
            grid_pos = Vec2(0, 0)

            jeopardy_grid = Grid_Surface(Vec2(grid_w, grid_h), grid_pos, Vec2(6, 6), players)
            manager.add_surface(jeopardy_grid)

            score_overlay = ScoreOverlay(players, jeopardy_grid)
            manager.add_surface(score_overlay)

            manager.add_surface(Transition_Surface(mode="jeopardy"))
            
            # # testing only
            # if final_surface is None:
            #     final_surface = FinalJeopardy(Vec2(screen_w, screen_h), Vec2(0, 0), players)
            #     manager.add_surface(final_surface)
    
    if (
        jeopardy_grid
        and not any(isinstance(s, Question_Surface) for s in manager.layers)
        and not any(isinstance(s, Cutscene_Surface) for s in manager.layers)
        and not any(isinstance(s, Transition_Surface) for s in manager.layers)
        and not jeopardy_grid.is_flashing()
    ):
        if jeopardy_grid.multiplier == 2 and not jeopardy_grid.bot_wait_until:
            jeopardy_grid.call_lowest_player()
        jeopardy_grid.time_update()

    # Render all surfaces in manager by their z-axis order
    manager.render()
    
    # Update all the surfaces for realtime changes
    manager.update()

    # fps
    clock.tick(60)

pygame.quit()