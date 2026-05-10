from __future__ import annotations

import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import random
import math
from typing import Literal, TYPE_CHECKING

import config
from sources.util import intxy, now_is_time, Color, Font
from sources.manager import manager, Base_Surface, Game_Manager
from sources.datatype.question import Question
from sources.datatype.player import Player
from sources.surfaces.visual import notify, BorderFlash, Cutscene_Surface

if TYPE_CHECKING:
    from sources.surfaces.surface_grid import Grid_Surface

warn = print # For now

# ----- Question_Surface: a modal window showing question and options -----
class Question_Surface(Base_Surface):
    def __init__(self, question: Question, grid_surface: Grid_Surface):
        dimension = Vec2(config.screen_dimension[0] * 0.7,
                         config.screen_dimension[1] * 0.7)  # scale to window
        rect = Surface(dimension).get_rect(center=(config.screen_dimension[0]//2,
                                                   config.screen_dimension[1]//2))
        pos = rect.topleft
        super().__init__(dimension, pos)
        
        self.grid_surface = grid_surface
        self.question = question        
        
        self.overshade = True
        
        self.stage: Literal[
            "Buzz", 
            "Answering", 
            "Timeout Re-buzz",
            "Wrong Re-buzz",
            "Re-answering",
            "Result"
        ] = "Buzz"
        self.current_player = None
        
        # Time for it close
        self.close_time = None

        # Buzz button in upper third
        self.buzz_rect = pygame.Rect(dimension.x//2 - 100, dimension.y//3, 200, 60)

        # Timer
        self.answer_start_time = None
        self.answer_duration = 5
        
        # Bot Answering
        self.bot_action: tuple[Player, int, int] = None # Player, choice, time
        self.submitted_answers: list[tuple[Player, int]] = []
        self.answer_start_time = None
        
        self.schedule_bot_action()
        print(self.bot_action)
        
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

    def schedule_bot_action(self, same_player = False) -> None:
        if same_player:
            bot = self.current_player
        else:
            bots = filter(lambda x: x.bot, Game_Manager.players)
            bot_answered = set(map(lambda x: x[0], filter(lambda x: x[0].bot, self.submitted_answers)))
            bot_not_answered = set(bots) - bot_answered
            
            bot = random.choice(list(bot_not_answered))
        
        correct_index = self.question.answer_index
        wrong_index = [i for i in range(3) if i != correct_index]

        if len(wrong_index) == 1:
            # 70% correct, 30% wrong
            if random.random() < 0.7:
                choice = correct_index
            else:
                choice = wrong_index[0]
        elif len(wrong_index) == 2:
            # 50% correct, 25% each wrong
            r = random.random()
            if r < 0.5:
                choice = correct_index
            elif r < 0.75:
                choice = wrong_index[0]
            else:
                choice = wrong_index[1]

        # schedule buzz
        delay = random.uniform(2750, 3500)
        click_time = pygame.time.get_ticks() + int(delay)
        self.bot_action = (bot, choice, click_time)
        
        print(self.bot_action, "SEttttttting")
    
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
            pygame.draw.rect(self.surface, Color.timer, self.buzz_rect)
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

        # Drawing Elements
        if self.stage == "Buzz":
            draw_buzz_button()
        if self.stage in ["Answering", "Re-answering"]:
            draw_timer(self.session_remaining_time())
            draw_options()
        if self.stage == "Result":
            draw_timer(self._frozen_timer_time)
            draw_options()
        if self.stage == "Timeout Re-buzz":
            draw_timer(self.session_remaining_time())
            draw_buzz_button()
            draw_options()
        if self.stage == "Wrong Re-buzz":
            draw_buzz_button()
            draw_options()

        screen.blit(self.surface, self.pos)
    
    def on_close(self):
        self.grid_surface.advance_turn(self.correctly_answered)
        
    def time_update(self):
        
        def _bot_click():
            bot, choice, click_time = self.bot_action
            self.bot_action = None

            buzz_point = Vec2(640, 310)
            option_points = [Vec2(640, 400), Vec2(640, 475), Vec2(640, 540)]
            
            if self.stage in ["Buzz", "Timeout Re-buzz", "Wrong Re-buzz"]:
                click_point = buzz_point
            elif self.stage in ["Answering", "Re-answering"]:
                click_point = option_points[choice]
            
            print(click_point, bot)
            manager.click_at(click_point, bot)
        
        # Resolve pending bot answer after 1s
        if self.bot_action and now_is_time(self.bot_action[2]):
            print("triggered")

            _bot_click()
    
        # Kill surface after 1s delay
        if self.close_time and pygame.time.get_ticks() >= self.close_time:
            manager.remove_surface(self)

        # --- Timeout handling ---
        if self.stage == "Timed Answering":
            remaining_time = self.session_remaining_time()
            
            if remaining_time <= 0:
                self.current_player.add_score(-self.question.value)
                
                notify(f"{self.current_player.name} timed out! -${self.question.value}")
                
                self.stage = "Non-timed Answering"

                # Setup the next bot and its answer
                self.schedule_bot_action()

    def on_click(self, pos: Vec2, player: Player):
        print(pos, player)
        
        def init_answer_session(player):
            self.current_player = player
            self.answer_start_time = pygame.time.get_ticks()
            
            # Screen flash in player color
            manager.add_surface(BorderFlash(self.current_player))
            
            if player.bot:
                self.schedule_bot_action(True)
            
        
        if self.stage == "Buzz" and self.buzz_rect.collidepoint(pos):
            self.stage = "Answering"
            init_answer_session(player)
        
        
        if self.stage == "Answering":
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    if player != self.current_player:
                        warn("Only the current player can answer!")
                        return
                    
                    if self.question.answer_index == i:
                        self.stage = "Result"
                        self._frozen_timer_time = pygame.time.get_ticks()
                        
                        player.add_score(self.question.value)
                        notify(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                        self.close_time = pygame.time.get_ticks() + 1000
                    else:
                        self.stage = "Wrong Re-buzz"
                        
                        player.add_score(-self.question.value)
                        notify(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")

                        self.schedule_bot_action()
        
        if self.stage == "Timeout Re-buzz":
            if self.buzz_rect.collidepoint(pos):
                if player == self.current_player:
                    warn("You cannot buzz while answering!")
                    return

                # Now player must be other players
                self.stage = "Re-answering"
                init_answer_session(player)
                
                notify(f"{player.name} buzzes!")
        
        if self.stage == "Wrong Re-buzz" and self.buzz_rect.collidepoint(pos):
            if player == self.current_player:
                warn("You cannot buzz again!")
                return
            
            self.stage = "Re-answering"
            init_answer_session(player)
        
        if self.stage == "Re-answering":
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    if player != self.current_player:
                        warn("Only the current player can answer!")
                        return
                    
                    if self.question.answer_index == i:
                        player.add_score(self.question.value)
                        notify(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                    else:
                        notify(f"No one answers correctly!")
                    
                    self.close_time = pygame.time.get_ticks() + 1000
        
        print(self.bot_action, pygame.time.get_ticks(), "End of on click")
