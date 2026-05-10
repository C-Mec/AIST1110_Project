from __future__ import annotations

import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import random
import math
from typing import Literal, TYPE_CHECKING

import config
from sources.util import intxy, Color, Font
from sources.manager import manager, Base_Surface
from sources.datatype.question import Question
from sources.datatype.player import Player
from sources.surfaces.visual import notify, BorderFlash, Cutscene_Surface

if TYPE_CHECKING:
    from sources.surfaces.surface_grid import Grid_Surface

# ----- Question_Surface: a modal window showing question and options -----
class Question_Surface(Base_Surface):
    def __init__(self, question: Question, player: Player, bots: list[Player], grid_surface: Grid_Surface):
        dimension = Vec2(config.screen_dimension[0] * 0.7,
                         config.screen_dimension[1] * 0.7)  # scale to window
        rect = Surface(dimension).get_rect(center=(config.screen_dimension[0]//2,
                                                   config.screen_dimension[1]//2))
        pos = rect.topleft
        super().__init__(dimension, pos)
        
        self.grid_surface = grid_surface
        self.question = question
        self.player = player
        self.bots = bots
        self.interactive = False
        
        self.overshade = True
        
        self.stage: Literal[
            "Buzz", 
            "Timed Answering", 
            "Non-timed Answering",
            "Re-buzz"
        ] = "Buzz"
        
        # Time for it close
        self.close_time = None

        # Buzz button in upper third
        self.buzz_rect = pygame.Rect(dimension.x//2 - 100, dimension.y//3, 200, 60)

        # Timer
        self.answer_start_time = None
        self.answer_duration = 5
        
        # Bot Answering
        self.bot_pending = None
        self.bot_buzz_time: int = None
        self.submitted_answers: list[tuple[Player, int]] = []
        self.answer_start_time = None
        
        # For the next turn
        self.correctly_answered = None

        # Options: compute dynamically
        self.option_rects = []
        button_height = 50
        margin = 20
        total_height = len(self.question.options) * (button_height + margin) - margin
        start_y = dimension.y - total_height - 40  # 40px padding from bottom
        for i in range(len(self.question.options)):
            rect = pygame.Rect(50, start_y + i * (button_height + margin),
                               dimension.x - 100, button_height)
            self.option_rects.append(rect)

    def schedule_next_bot(self):
        answered = {ans[0] for ans in self.submitted_answers}
        remaining_bots = [b for b in self.bots if b not in answered]

        if not remaining_bots:
            self.close_time = pygame.time.get_ticks() + 1000
            return

        bot = random.choice(remaining_bots)

        # Pick choice
        all_indices = set(range(len(self.question.options)))
        used_indices = {ans[1] for ans in self.submitted_answers}
        remaining_indices = list(all_indices - used_indices)

        if not remaining_indices:
            self.close_time = pygame.time.get_ticks() + 1000
            return

        correct_index = self.question.answer_index
        wrong_pool = [i for i in remaining_indices if i != correct_index]

        if len(remaining_indices) == 1:
            choice = correct_index
        elif len(remaining_indices) == 2:
            # 70% correct, 30% wrong
            if random.random() < 0.7:
                choice = correct_index
            else:
                choice = wrong_pool[0]
        elif len(remaining_indices) == 3:
            # 50% correct, 25% each wrong
            r = random.random()
            if r < 0.5:
                choice = correct_index
            elif r < 0.75:
                choice = wrong_pool[0]
            else:
                choice = wrong_pool[1]
        else:
            # Fallback: 50/50 correct vs random wrong
            if random.random() < 0.5:
                choice = correct_index
            else:
                choice = random.choice(wrong_pool)

        # Random delay 0.75–1.5s
        delay_ms = int(random.uniform(750, 1500))
        buzz_time = pygame.time.get_ticks() + delay_ms
        delay_ms = int(random.uniform(750, 1500))
        answer_time = delay_ms

        # Queue only this bot
        self.bot_pending = (buzz_time, bot, choice, answer_time)

    def bot_try_answer(self, bot: Player, choice: int):
        self.submitted_answers.append((bot, choice))

        if choice == self.question.answer_index:
            bot.add_score(self.question.value)
            notify(f"{bot.name} answered correctly! +${self.question.value}")
            self.correctly_answered = bot
            self.close_time = pygame.time.get_ticks() + 1000
        else:
            bot.add_score(-self.question.value)
            notify(f"{bot.name} answered wrong! -${self.question.value}")
            self.correctly_answered = False

        self.bot_pending = None
    
    def session_remaining_time(self) -> float:
        if not self.answer_start_time:
            return 0
        elapsed_time = (pygame.time.get_ticks() - self.answer_start_time) / 1000
        return max(0, self.answer_duration - elapsed_time)
    
    def draw(self, screen: Surface):
        # Paint background
        self.surface.fill(Color.background)
        pygame.draw.rect(self.surface, Color.border, self.surface.get_rect(), 3)

        # Set alpha
        self.surface.set_alpha(self.alpha)

        # Question text at top
        text = Font.clue_medium.render(self.question.problem, True, Color.text)
        self.surface.blit(text, (30, 30))
        
        def draw_buzz_button():
            # Buzz button in player color
            pygame.draw.rect(self.surface, self.player.color, self.buzz_rect)
            pygame.draw.rect(self.surface, Color.border, self.buzz_rect, 2)
            buzz_text = Font.logo_medium.render("BUZZ!", True, Color.black)
            self.surface.blit(buzz_text, buzz_text.get_rect(center=self.buzz_rect.center))
        
        def draw_timer(remaining_time: float):
            # Circle depletion in degrees
            center = (int(self.dimension.x//2), int(self.dimension.y//3))
            radius = 50
            pygame.draw.circle(self.surface, Color.border, center, radius, 2)

            # Filled pie slice shrinking

            fraction = remaining_time / self.answer_duration
            angle = 360.0 * fraction

            if angle > 0.1:
                start_deg = -90.0
                segments = max(2, int(angle / 6.0))  # ~1 point per 6 degrees
                points = [center]
                for i in range(segments + 1):
                    deg = start_deg - (angle * i / segments)
                    rad = math.radians(deg)
                    x = center[0] + radius * math.cos(rad)
                    y = center[1] + radius * math.sin(rad)
                    points.append((x, y))

                pygame.draw.polygon(self.surface, Color.timer, points)
            pygame.draw.circle(self.surface, Color.border, center, radius, 2)

            # Seconds remaining in middle
            sec_text = Font.clue_large.render(str(int(remaining_time)), True, Color.text)
            self.surface.blit(sec_text, sec_text.get_rect(center=center))
        
        def draw_options():
            for i, rect in enumerate(self.option_rects):
                pygame.draw.rect(self.surface, Color.background, rect)

                if i == self.question.answer_index and self.correctly_answered:
                    border_color = Color.correct
                elif any(ans[1] == i for ans in self.submitted_answers):
                    border_color = Color.wrong
                else:
                    border_color = Color.border

                pygame.draw.rect(self.surface, border_color, rect, 2)

                option_text = f"{chr(65+i)}. {self.question.options[i]}"
                text = Font.clue_small.render(option_text, True, Color.text)
                self.surface.blit(text, text.get_rect(center=rect.center))

        # Drawing Elements
        if self.stage == "Buzz":
            draw_buzz_button()
        else:
            if self.answer_start_time:
                draw_timer(self.session_remaining_time())
            # Always show options
            draw_options()

        screen.blit(self.surface, self.pos)
    
    def on_close(self):
        self.grid_surface.advance_turn(self.correctly_answered)
    
    def time_update(self):
        now = pygame.time.get_ticks()

        # --- Bot buzz resolution ---
        if self.bot_pending:
            buzz_time, bot, choice, answer_time = self.bot_pending
            if now >= buzz_time + answer_time:
                self.answer_start_time = None
                self.bot_try_answer(bot, choice)

                if self.correctly_answered:
                    self.close_time = now + 1000
            elif now >= buzz_time:
                if not self.answer_start_time:
                    manager.add_surface(BorderFlash(bot))
                    self.answer_start_time = pygame.time.get_ticks()

        # --- Close after delay ---
        if self.close_time and now >= self.close_time:
            self.grid_surface.advance_turn(correct=self.correctly_answered)
            manager.remove_surface(self)

        # --- Timeout handling ---
        if self.stage == "Timed Answering":
            remaining_time = self.session_remaining_time()
            if remaining_time < 0:
                self.player.add_score(-self.question.value)
                notify(f"{self.player.name} timed out! -${self.question.value}")
                self.correctly_answered = False

                # Stop timer
                self.answer_start_time = None
                self.interactive = False

                # Cutscene delay before bots buzz
                self.cutscene_done_time = now + 1000
                self.stage = "Bot Buzzing"

        # --- Cutscene → start bots ---
        elif self.stage == "Bot Buzzing":
            if (not self.bot_pending
                and not any(isinstance(s, Cutscene_Surface) for s in manager.layers)):
                self.schedule_next_bot()

    def on_click(self, pos: Vec2, player: Player):
        if not getattr(self, "interactive", True):
            return
        
        if self.stage == "Buzz" and self.buzz_rect.collidepoint(pos):
            self.stage = "Timed Answering"
            self.answer_start_time = pygame.time.get_ticks()
            
            # Screen flash in player color
            manager.add_surface(BorderFlash(self.player))
        
        elif self.stage == "Timed Answering":
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    if self.question.answer_index == i:
                        # Correct answer
                        self.correctly_answered = player
                        player.add_score(self.question.value)
                        notify(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                        self.close_time = pygame.time.get_ticks() + 1000
                    else:
                        # Wrong answer
                        self.correctly_answered = False
                        player.add_score(-self.question.value)
                        notify(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")

                        self.submitted_answers.append((player, i))
                        
                        # Stop timer immediately
                        self.answer_start_time = None  
                        self.interactive = False

                        # Trigger cutscene delay before bots buzz
                        self.cutscene_done_time = pygame.time.get_ticks() + 1000
                        self.stage = "Bot Buzzing"

        
    def resize(self, new_dimension: Vec2):
        # Resize popup proportionally to new window size.
        screen_w, screen_h = intxy(new_dimension)

        # Scale to 70% of window
        self.dimension = Vec2(screen_w * 0.7, screen_h * 0.7)

        # Recreate surface buffer
        self.surface = Surface(self.dimension, pygame.SRCALPHA)

        # Center popup
        rect = self.surface.get_rect(center=(screen_w // 2, screen_h // 2))
        self.pos = Vec2(rect.topleft)
        self.rect = rect

        # Recompute buzz button
        self.buzz_rect = pygame.Rect(self.dimension.x // 2 - 100,
                                    self.dimension.y // 3,
                                    200, 60)

        # Recompute option rects
        self.option_rects = []
        button_height = 50
        margin = 20
        total_height = len(self.question.options) * (button_height + margin) - margin
        start_y = self.dimension.y - total_height - 40
        for i in range(len(self.question.options)):
            rect = pygame.Rect(50,
                            start_y + i * (button_height + margin),
                            self.dimension.x - 100,
                            button_height)
            self.option_rects.append(rect)
