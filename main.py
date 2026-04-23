import warnings
import os

# Ignore Loading Warning in Console
warnings.filterwarnings( 
    "ignore",
    message = "Your system is avx2.*",
    category = RuntimeWarning,
)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import object
import pygame

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("#00008B")

    # RENDER YOUR GAME HERE
    game_screen = object.game_screen(1280, 720)
    game_screen.display()

    # flip() the display to put your work on screen i.e. screen refresh
    pygame.display.flip()

    # fps
    clock.tick(60)

pygame.quit()
