import pygame, config
from sources.util import Font, Color, intxy
from sources.manager import manager, Base_Surface, Game_Manager
from sources.datatype.player import Player

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

class End_Surface(Base_Surface):
    def __init__(self, dimension: Vec2, pos: Vec2):
        screen_w, screen_h = config.screen_dimension
        margin_x = int(screen_w * 0.18)
        margin_y = int(screen_h * 0.195)

        grid_w = screen_w - 2 * margin_x
        grid_h = screen_h - 1.8 * margin_y

        dimension = Vec2(grid_w, grid_h)
        pos = Vec2(margin_x, margin_y)
        super().__init__(dimension, pos)

        # Background
        self.background = pygame.image.load("assets/Jeopardy-BoardAlt.webp").convert()
        self.background = pygame.transform.smoothscale(self.background, (screen_w, screen_h))

        # Sort players by score
        self.players = sorted(Game_Manager.players, key=lambda p: p.score, reverse=True)
        self.winner = self.players[0] if self.players else None

        # Animation state
        self.start_time = pygame.time.get_ticks()
        self.zoom_scale = 1.0

        # Quit button rect
        self.quit_button = Rect(self.dimension.x//2 - 60,
                                self.dimension.y - 80,
                                120, 40)

    def time_update(self):
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
        self.zoom_scale = min(elapsed, 1.0)

    def draw(self, screen: Surface):
        screen.blit(self.background, (2, 0))
        self.surface.fill(Color.background)

        if self.winner:
            texts = [
                ("Congratulations!", Font.logo_large),
                (self.winner.name, Font.logo_large),
                (f"${self.winner.score}", Font.logo_large)
            ]

            center_x = self.surface.get_width() // 2
            center_y = self.surface.get_height() // 2
            y_offset = center_y - (len(texts) * 60) // 2

            for text, font in texts:
                base_surface = font.render(text, True, Color.text)
                shadow_surface = font.render(text, True, Color.shadow)

                w, h = base_surface.get_size()
                scaled_surface = pygame.transform.smoothscale(
                    base_surface, (int(w * self.zoom_scale), int(h * self.zoom_scale))
                )
                scaled_shadow = pygame.transform.smoothscale(
                    shadow_surface, (int(w * self.zoom_scale), int(h * self.zoom_scale))
                )

                rect = scaled_surface.get_rect(center=(center_x, y_offset))
                shadow_rect = rect.copy()
                shadow_rect.x += 2
                shadow_rect.y += 2

                self.surface.blit(scaled_shadow, shadow_rect)
                self.surface.blit(scaled_surface, rect)

                y_offset += rect.height + 20

        # --- Draw Quit button ---
        pygame.draw.rect(self.surface, Color.white, self.quit_button)
        pygame.draw.rect(self.surface, Color.border, self.quit_button, 2)

        # Render shadow first
        quit_shadow = Font.clue_medium.render("Quit", True, Color.shadow)
        shadow_rect = quit_shadow.get_rect(center=self.quit_button.center)
        shadow_rect.x += 2
        shadow_rect.y += 2
        self.surface.blit(quit_shadow, shadow_rect)

        # Render main text on top
        quit_text = Font.clue_medium.render("Quit", True, Color.text)
        quit_rect = quit_text.get_rect(center=self.quit_button.center)
        self.surface.blit(quit_text, quit_rect)


        screen.blit(self.surface, self.pos)

    def on_click(self, pos: Vec2, player: Player):
        # Check if quit button clicked
        if self.quit_button.collidepoint(pos):
            pygame.quit()
            exit()