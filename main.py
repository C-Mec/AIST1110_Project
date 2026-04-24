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
import ui

Vec2 = pygame.Vector2

pygame.init()
clock = pygame.time.Clock()
main_screen = pygame.display.set_mode((1280, 720))

manager = ui.Surface_Manager()

jeopardy_grid = ui.Grid_Surface(Vec2(1000, 600), Vec2(140, 60))
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
            
            ...
            
            result = jeopardy_grid.get_cell_at_pos(rpos)
            if result:
                row, col, q = result
                print(f"Clicked on row {row}, col {col}")
                print(f"Question: {q.question}")
                q.listAnswer()

    # fill the screen with a color to wipe away anything from last frame
    main_screen.fill("#121314")

    # RENDER YOUR GAME HERE
    jeopardy_grid.draw()
    main_screen.blit(jeopardy_grid.surface, jeopardy_grid.pos)

    # flip() the display to put your work on screen i.e. screen refresh
    pygame.display.flip()

    # fps
    clock.tick(60)

pygame.quit()
