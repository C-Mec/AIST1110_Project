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
from sources.surfaces.visual import notify, BorderFlash

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
        
        self.overshade = True
        
        self.stage: Literal[
            "Buzz", 
            "Timed Answering", 
            "Non-timed Answering"
        ] = "Buzz"
        
        # Time for it close
        self.close_time = None

        # Buzz button in upper third
        self.buzz_rect = pygame.Rect(dimension.x//2 - 100, dimension.y//3, 200, 60)

        # Timer
        self.answer_start_time = None
        self.answer_duration = 5
        
        # Bot Answering
        self.bot_pending: tuple[Player, int] = None
        self.bot_buzz_time: int = None
        self.submitted_answers: list[tuple[Player, int]] = []

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

    def schedule_bot_buzz(self) -> None:
        bot_answered = set(map(lambda x: x[0], filter(lambda x: x[0].bot, self.submitted_answers)))
        bot_not_answered = set(self.bots) - bot_answered
        
        ### Handle Empty Robot Case
        
        bot = random.choice(bot_not_answered)
        
        correct_index = self.question.answer_index
        wrong_index = random.choice(set(i for i in range(3)) - set(map(lambda x: x[1], self.submitted_answers)))

        if random.random() < config.bot_skill:
            choice = correct_index
        else:
            choice = wrong_index

        # schedule buzz
        delay = random.uniform(750, 1500)
        self.bot_buzz_time = pygame.time.get_ticks() + int(delay)
        self.bot_pending = (bot, choice)

    def bot_try_answer(self, bot: Player, choice: int):
        # Flash immediately when buzz happens
        manager.add_surface(BorderFlash(bot))

        self.submitted_answers.append((bot, choice))
        self.timer_isActive = False

        if choice == self.question.answer_index:
            bot.add_score(self.question.value)
            
            print(f"{bot.name} answered correctly! +${self.question.value}")
            self.correct_option_index = choice
            self.close_time = pygame.time.get_ticks() + 1000
        else:
            bot.add_score(-self.question.value)
            
            self.wrong_option_indices.add(choice)
            print(f"{bot.name} answered wrong! -${self.question.value}")

            self.schedule_bot_buzz()
            if not self.bot_pending:
                self.close_time = pygame.time.get_ticks() + 1000
    
    def session_remaining_time(self) -> float:
        elapsed_time = (pygame.time.get_ticks() - self.answer_start_time) / 1000
        remaining_time = max(0, self.answer_duration - elapsed_time)
        
        return remaining_time
    
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
            buzz_text = Font.logo_large.render("BUZZ!", True, Color.black)
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
            # Draw options
            for i, rect in enumerate(self.option_rects):
                pygame.draw.rect(self.surface, Color.background, rect)

                if self.stage == "Timed Answering":
                    border_color = Color.border
                    
                elif self.stage == "Non-timed Answering":
                    if i == self.question.answer_index:
                        border_color = Color.correct
                    elif i in set(range(3)) - set([self.question.answer_index]):
                        border_color = Color.wrong

                pygame.draw.rect(self.surface, border_color, rect, 2)

                option_text = f"{chr(65+i)}. {self.question.options[i]}"
                text = Font.clue_small.render(option_text, True, Color.text)
                self.surface.blit(text, text.get_rect(center=rect.center))
            
        # Drawing Elements
        if self.stage == "Timed Answering":
            draw_timer(self.session_remaining_time())
            draw_options()
        elif self.stage == "Non-timed Answering":
            draw_options()
        elif self.stage == "Buzz":
            draw_buzz_button()

        screen.blit(self.surface, self.pos)
    
    def on_close(self):
        self.grid_surface.advance_turn()
    
    def time_update(self):
        # Resolve pending bot answer after 1s
        if self.bot_pending and self.bot_buzz_time and pygame.time.get_ticks() >= self.bot_buzz_time:
            bot, choice = self.bot_pending
            self.bot_try_answer(bot, choice)
            
            self.bot_pending = None
            self.bot_buzz_time = None
    
        # Kill surface after 1s delay
        if self.close_time and pygame.time.get_ticks() >= self.close_time:
            manager.remove_surface(self)
            
        if self.stage == "Timed Answering":
            remaining_time = self.session_remaining_time()
            
            if remaining_time <= 0:
                self.player.add_score(-self.question.value)
                
                notify(f"{self.player.name} timed out! -${self.question.value}")
                
                self.stage = "Non-timed Answering"

                # Setup the next bot and its answer
                self.schedule_bot_buzz()

    def on_click(self, pos: Vec2, player: Player):
        if self.stage == "Buzz" and self.buzz_rect.collidepoint(pos):
            self.stage = "Timed Answering"
            self.answer_start_time = pygame.time.get_ticks()
            
            # Screen flash in player color
            manager.add_surface(BorderFlash(self.player))
            
        ### Need to prevent multiple scoring
        
        elif self.stage == "Timed Answering":
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    self.stage = "Non-timed Answering"
                    
                    if self.question.answer_index == i:
                        player.add_score(self.question.value)
                        notify(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                        
                        self.close_time = pygame.time.get_ticks() + 1000
                    else:
                        player.add_score(-self.question.value)
                        notify(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")

                        self.schedule_bot_buzz()