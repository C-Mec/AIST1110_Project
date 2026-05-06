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

import config
from sources.manager import manager
from sources.datatype.player import init_players
from sources.surfaces.surface_start import StartScreen
from sources.surfaces.surface_grid import Grid_Surface
from sources.surfaces.overlay import ScoreOverlay

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

running = True
while running:
    # poll for events
    for event in pygame.event.get():
        
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False
        
        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            # Update screen dimension
            config.screen_dimension = (event.w, event.h)
            main_screen = pygame.display.set_mode(config.screen_dimension, pygame.RESIZABLE)
            manager.init(main_screen)

            # Recompute grid with 1/12 buffer
            screen_w, screen_h = config.screen_dimension
            buffer_w = screen_w // 12
            buffer_h = screen_h // 12
            grid_w = screen_w - 2 * buffer_w
            grid_h = screen_h - 2 * buffer_h
            grid_pos = Vec2(buffer_w, buffer_h)

            # Replace old grid with new resized one
            manager.layers = [s for s in manager.layers if not isinstance(s, Grid_Surface)]
            jeopardy_grid = Grid_Surface(Vec2(grid_w, grid_h), grid_pos, Vec2(6, 6), players)
            manager.add_surface(jeopardy_grid)

            # Re-add score overlay in top-right
            manager.layers = [s for s in manager.layers if not isinstance(s, ScoreOverlay)]
            score_overlay = ScoreOverlay(players)
            manager.add_surface(score_overlay)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = Vec2(event.pos)

            surface, rpos = manager.get_top_collision(pos)
            
            click_logging = True
            if click_logging:
                print(f"Pos: {pos}, Surface: {surface}, Rpos: {rpos}")
            
            layer_logging = True
            if layer_logging:
                print(manager.layers)
            
            if surface is not None:
                surface.click_at(rpos, player)
                
    if not any(isinstance(s, StartScreen) for s in manager.layers):
        if jeopardy_grid is None:
            # Compute grid with buffer
            screen_w, screen_h = config.screen_dimension
            buffer_w, buffer_h = screen_w // 12, screen_h // 12
            grid_w, grid_h = screen_w - 2 * buffer_w, screen_h - 2 * buffer_h
            grid_pos = Vec2(buffer_w, buffer_h)

            jeopardy_grid = Grid_Surface(Vec2(grid_w, grid_h), grid_pos, Vec2(6, 6), players)
            manager.add_surface(jeopardy_grid)

            score_overlay = ScoreOverlay(players)
            manager.add_surface(score_overlay)

    # Render all surfaces in manager by their z-axis order
    manager.render()

    # fps
    clock.tick(60)

pygame.quit()