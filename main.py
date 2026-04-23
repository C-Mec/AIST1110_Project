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
import object

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

jeopardy_grid = object.Grid_Surface(1000, 600)

running = True
while running:
    # poll for events
    for event in pygame.event.get():
        
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("#121314")

    # RENDER YOUR GAME HERE
    jeopardy_grid.draw()
    screen.blit(jeopardy_grid.surface, (140, 60))

    # flip() the display to put your work on screen i.e. screen refresh
    pygame.display.flip()

    # fps
    clock.tick(60)

pygame.quit()
