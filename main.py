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

import config
import ui
from ui import manager

Vec2 = pygame.Vector2

clock = pygame.time.Clock()

main_screen = pygame.display.set_mode(config.screen_dimension)
manager.init(main_screen)

# Create a human player
current_player = ui.Player("Human")
# Pass manager and player to Grid_Surface
jeopardy_grid = ui.Grid_Surface(Vec2(1000, 600), Vec2(140, 60), Vec2(6, 5))
manager.add_surface(jeopardy_grid)

running = True
while running:
    # poll for events
    for event in pygame.event.get():
        
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = Vec2(event.pos)

            surface, rpos = manager.get_top_collision(pos)
            
            if surface is not None:
                surface.click_at(rpos)

    # Render all surfaces in manager by their z-axis order
    manager.render()

    # fps
    clock.tick(60)

pygame.quit()
