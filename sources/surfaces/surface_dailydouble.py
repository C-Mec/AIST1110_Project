from __future__ import annotations

import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import random
import math
from typing import Literal, TYPE_CHECKING

import config
from sources.util import intxy, now, now_is_time, blit_text_with_center, Color, Font
from sources.manager import Surface_Manager, Base_Surface, Game_Manager
from sources.datatype.question import Question
from sources.datatype.player import Player
from sources.surfaces.visual import notify, time_froze, BorderFlash, Cutscene_Surface

if TYPE_CHECKING:
    from sources.surfaces.surface_grid import Grid_Surface


class DailyDouble_Surface(Base_Surface):
    def __init__(self, question: Question, category: str, grid_surface: Grid_Surface, player: Player):
        screen_w, screen_h = config.screen_dimension
        margin_x = int(screen_w * 0.18)
        margin_y = int(screen_h * 0.195)

        grid_w = screen_w - 2 * margin_x
        grid_h = screen_h - 1.8 * margin_y

        dimension = Vec2(grid_w, grid_h)
        pos = Vec2(margin_x, margin_y)

        super().__init__(dimension, pos)

        self.question = question
        self.category = category
        self.clue = question.problem
        self.correct_option = question.options[question.answer_index]
        
        self.confirmed = False
        self.input_text = ""
        self.active_box = False
        self.phase = "wager"
        
        # Countdowns
        self.no_wager_start = None
        self.end_countdown = None
        self.timer_time = None
        
        self.screen_w, self.screen_h = intxy(config.screen_dimension)
        self.background = pygame.image.load("assets/Jeopardy-BoardAlt.webp").convert()
        self.background = pygame.transform.smoothscale(self.background, (self.screen_w, self.screen_h))

        self.player = player
        
        if self.player.bot:
            if player.score == max(map(lambda x: x.score, Game_Manager.players)):
                self.wager = 0
            else:
                self.wager = max(player.score, 1000 * Grid_Surface.multiplier)
        else:
            self.wager = 0
        self.submitted_answers: list[tuple[Player, int]] = []
        self.answer = None
        
        self.alpha = 0
        self.interactive = False

        # Input boxes relative to popup size
        self.box_rect = Rect(40, 220, 200, 40)
        self.confirm_button = Rect(260, 220, 120, 40)
        self.answer_box = Rect(40, 320, 400, 40)
        self.close_time = None
        
        self.option_rects = []
        button_height = 50
        margin = 20
        total_height = len(self.question.options) * (button_height + margin) - margin
        start_y = dimension.y - total_height - 40  # 40px padding from bottom
        for i in range(len(self.question.options)):
            rect = pygame.Rect(50, start_y + i * (button_height + margin),
                               dimension.x - 100, button_height)
            self.option_rects.append(rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active_box and not self.confirmed:
            if event.key == pygame.K_RETURN:
                if self.phase == "wager":
                    self._confirm_wager()
                elif self.phase == "answer":
                    self._lock_answer()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode

    def on_click(self, pos, player):
        if not self.interactive:
            return

        if self.phase == "wager":
            if self.box_rect.collidepoint(pos):
                self.active_box = True
            else:
                self.active_box = False
            
            if self.confirm_button.collidepoint(pos):
                self._confirm_wager()
            
        elif self.phase == "answer":
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    # Only the current player can answer
                    if player != self.player:
                        warn("Only the active player can answer!")
                        return

                    # Prevent duplicate selections
                    selected_answers = map(lambda x: x[1], self.submitted_answers)
                    if i in selected_answers:
                        warn("This option has already been chosen!")
                        return

                    # Record the answer
                    self.submitted_answers.append((player, i))

                    # Correct answer
                    if i == self.question.answer_index:
                        player.add_score(self.wager)
                        notify(f"Correct! {player.name} gains ${self.wager}. Total: ${player.score}")
                        self.close_time = pygame.time.get_ticks() + 1000
                    else:
                        player.add_score(-self.wager)
                        notify(f"Wrong! {player.name} loses ${self.wager}. Total: ${player.score}")
                        self.close_time = pygame.time.get_ticks() + 1000

                
    
    def wrap_text(self, text: str, font, max_width: int) -> list[str]:
        words = text.split()
        lines, current = [], []

        for word in words:
            test_line = " ".join(current + [word])
            if font.size(test_line)[0] <= max_width:
                current.append(word)
            else:
                lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))

        return lines
    
    def _confirm_wager(self):
        try:
            self.player = next(p for p in Game_Manager.players if not p.bot)
            if self.player.score < 1:
                # Start timer for "Cannot wager" message
                self.no_wager_start = pygame.time.get_ticks()
                return
            self.wager = max(0, min(int(self.input_text), self.player.score))
            print(f"{self.player.name} wagered ${self.wager}")
            self.phase = "answer"
            self.active_box = False
            self.confirmed = False
            self.input_text = ""
        except (ValueError, StopIteration):
            print(f"Confirm failed {self.input_text}")
            self.input_text = ""

    def draw(self, screen: Surface):
        screen.blit(self.background, (2, 0))
        self.surface.fill(Color.background)

        self.surface.set_alpha(self.alpha)
        
        # Title
        shadow = Font.logo_large.render("Daily Double", True, Color.shadow)
        title = Font.logo_large.render("Daily Double", True, Color.text)
        self.surface.blit(shadow, (self.surface.get_width()//2 - title.get_width()//2 + 2, 20 + 2))
        self.surface.blit(title, (self.surface.get_width()//2 - title.get_width()//2, 20))

        def draw_options(self):
            for i, rect in enumerate(self.option_rects):
                pygame.draw.rect(self.surface, Color.background, rect)

                if i in map(lambda x: x[1], self.submitted_answers):
                    if i == self.question.answer_index:
                        border_color = Color.correct
                    else:
                        border_color = Color.wrong
                else:
                    border_color = Color.border

                pygame.draw.rect(self.surface, border_color, rect, 2)

                option_text = f"{chr(65+i)}. {self.question.options[i]}"
                text = Font.clue_small.render(option_text, True, Color.text)
                self.surface.blit(text, text.get_rect(center=rect.center))

        
        # --- Always show wagers at bottom ---
        y = self.surface.get_height() - 100
        x_positions = self.surface.get_width()//2

        if self.phase == "wager":
            # Category title + shadow
            category_text = Font.category_large.render(self.category, True, Color.text)
            shadow = Font.category_large.render(self.category, True, Color.shadow)
            shadow_rect = shadow.get_rect(center=(self.surface.get_width()//2, 122))
            self.surface.blit(shadow, shadow_rect)
            rect = category_text.get_rect(center=(self.surface.get_width()//2, 120))
            self.surface.blit(category_text, rect)

            if self.player.bot:
                # Bot: display their wager directly, no input box
                line1 = Font.clue_medium.render(f"{self.player.name}", True, Color.text)
                line2 = Font.clue_medium.render(f"Wagering ${self.player.wager}", True, Color.text)
                rect1 = line1.get_rect(center=(self.surface.get_width()//2, self.surface.get_height()//2 - 20))
                rect2 = line2.get_rect(center=(self.surface.get_width()//2, self.surface.get_height()//2 + 20))
                self.surface.blit(line1, rect1)
                self.surface.blit(line2, rect2)
            else:
                # Human: show input box + confirm
                prompt = Font.clue_medium.render(f"{self.player.name}, enter your wager (0–{self.player.score}):", True, Color.text)
                rect = prompt.get_rect(center=(self.surface.get_width()//2, self.surface.get_height()//2 - 45))
                self.surface.blit(prompt, rect)

                box_w, box_h = 200, 40
                self.box_rect = Rect(self.surface.get_width()//2 - box_w//2,
                                    self.surface.get_height()//2 - box_h//2,
                                    box_w, box_h)
                color = Color.white if not self.active_box else Color.greyed
                pygame.draw.rect(self.surface, color, self.box_rect, 0)
                pygame.draw.rect(self.surface, Color.border, self.box_rect, 2)

                text_surface = Font.clue_medium.render(self.input_text, True, Color.text)
                text_rect = text_surface.get_rect(center=self.box_rect.center)
                self.surface.blit(text_surface, text_rect)

                # Caret blinking
                if self.active_box and not self.confirmed:
                    if (pygame.time.get_ticks() // 500) % 2 == 0:
                        caret_x = text_rect.right + 2
                        caret_y = text_rect.top
                        caret_height = text_surface.get_height()
                        pygame.draw.line(self.surface, Color.text,
                                        (caret_x, caret_y),
                                        (caret_x, caret_y + caret_height), 2)

                # Confirm button
                self.confirm_button = Rect(self.surface.get_width()//2 - 60,
                                        self.surface.get_height()//2 + 30,
                                        120, 40)
                pygame.draw.rect(self.surface, Color.greyed if self.confirmed else Color.white, self.confirm_button)
                pygame.draw.rect(self.surface, Color.border, self.confirm_button, 2)
                btn_text = Font.clue_medium.render("Confirm", True, Color.text)
                btn_rect = btn_text.get_rect(center=self.confirm_button.center)
                self.surface.blit(btn_text, btn_rect)

        elif self.phase == "answer":
            max_width = self.surface.get_width() - 80
            lines = self.wrap_text(self.question.problem, Font.clue_medium, max_width)
            y = 120  # top margin
            for line in lines:
                rendered = Font.clue_medium.render(line, True, Color.text)
                rect = rendered.get_rect(center=(self.surface.get_width()//2, y))
                self.surface.blit(rendered, rect)
                y += rendered.get_height() - 5
            draw_options(self)
            
            if self.player.bot:
                # Bot: auto-select an option
                if not any(p == self.player for p, _ in self.submitted_answers):
                    # Decide correct/wrong based on bot skill
                    correct_index = self.question.answer_index
                    wrong_indexes = [i for i in range(len(self.question.options)) if i != correct_index]

                    if random.random() < config.bot_skill:
                        choice = correct_index
                    else:
                        choice = random.choice(wrong_indexes)

                    # Simulate bot "click"
                    self.submitted_answers.append((self.player, choice))

                    if choice == correct_index:
                        self.player.add_score(self.wager)
                        notify(f"Correct! {self.player.name} gains ${self.wager}. Total: ${self.player.score}")
                        self.close_time = pygame.time.get_ticks() + 1000
                    else:
                        self.player.add_score(-self.question.value)
                        notify(f"Wrong! {self.player.name} loses ${self.wager}. Total: ${self.player.score}")
                        self.close_time = pygame.time.get_ticks() + 1000
        
        screen.blit(self.surface, self.pos)

    def time_update(self):
        if self.close_time and now_is_time(self.close_time):
            Surface_Manager.remove_surface(self)
        
    def resize(self, new_dimension: Vec2):
        screen_w, screen_h = intxy(new_dimension)

        # Match grid: recompute margins and grid area
        margin_x = int(screen_w * 0.18)
        margin_y = int(screen_h * 0.195)
        grid_w = screen_w - 2 * margin_x
        grid_h = screen_h - 1.8 * margin_y
        self.grid_area = pygame.Rect(margin_x, margin_y, grid_w, grid_h)

        # Update dimension and position to match grid_area
        self.dimension = Vec2(grid_w, grid_h)
        self.surface = Surface(self.dimension, pygame.SRCALPHA)
        self.pos = Vec2(self.grid_area.topleft)
        self.rect = self.surface.get_rect(topleft=self.pos)

        # --- Rescale background to full window ---
        self.background = pygame.image.load("assets/Jeopardy-BoardAlt.webp").convert()
        self.background = pygame.transform.smoothscale(self.background, (screen_w, screen_h))



