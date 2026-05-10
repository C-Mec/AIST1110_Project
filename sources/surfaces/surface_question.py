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
            "Result"
        ] = "Buzz"
        self.current_player = None
        
        # Time for it close
        self.close_time = None

        # Buzz button in upper third
        self.buzz_rect = pygame.Rect(dimension.x//2 - 100, dimension.y//3 + 40, 200, 60)

        # Timer
        self.session_time = None
        self.timer_time = None
        self.answer_duration = 5
        self.buzz_flash_start_time = None
        
        # Bot Answering
        self.bot_action: tuple[Player, Vec2, int] = None # bot, pos, time
        self.submitted_answers: list[tuple[Player, int]] = []
        self.timer_time = None
        
        self.schedule_bot_action()
        print(self.bot_action)

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

    def schedule_bot_action(self) -> None:
        def determine_bot() -> Player:
            bots = filter(lambda x: x.bot and x != self.current_player, Game_Manager.players)
            
            return random.choice(list(bots))
            
        def determine_choice() -> int:
            correct_index = self.question.answer_index
            
            # Submitted answers must be wrong
            used_indexes = map(lambda x: x[1], self.submitted_answers) 
            wrong_indexes = [i for i in range(3) if i != correct_index and i not in used_indexes]

            if random.random() < config.bot_skill:
                return random.choice(wrong_indexes)
            else:
                return correct_index
        
        buzz_point = Vec2(640, 340)
        option_points = [Vec2(640, 400), Vec2(640, 475), Vec2(640, 540)]
        
        # Schedule bot answer
        if self.stage == "Answering" and self.current_player.bot:
            choice = determine_choice()
            
            click_time = pygame.time.get_ticks() + random.uniform(3000, 7000)
            self.bot_action = (self.current_player, option_points[choice], click_time)
        
        if self.stage == "Buzz" or self.stage == "Timeout Re-buzz" or self.stage == "Wrong Re-buzz":
            bot = determine_bot()
            
            click_time = pygame.time.get_ticks() + random.uniform(3000, 7000)
            
            # If bot_rebuzz time is later than the previous bot answer time, it should not override the previous bot's answer
            if self.bot_action and click_time > self.bot_action[2]:
                return
            
            self.bot_action = (bot, buzz_point, click_time)
    
    def session_remaining_time(self) -> float:
        assert self.timer_time
        
        elapsed_time = (pygame.time.get_ticks() - self.timer_time) / 1000
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
            if self.buzz_flash_start_time and now_is_time(self.buzz_flash_start_time):
                flashing = ((now() - self.buzz_flash_start_time) // 500 ) % 2
                
                center_color = Color.buzz_light if flashing else Color.buzz_dark
                
                if (now() - self.buzz_flash_start_time) > 2000:
                    self.buzz_flash_start_time = None
            else:
                center_color = Color.buzz_dark
            
            pygame.draw.rect(self.surface, center_color, self.buzz_rect)
            pygame.draw.rect(self.surface, Color.border, self.buzz_rect, 4)
            
            blit_text_with_center("BUZZ", Font.logo_medium, Color.black, self.surface, self.buzz_rect.center)
        
        def draw_timer(remaining_time: float):
            # Circle depletion in degrees
            center = (int(self.dimension.x//2), int(self.dimension.y//3-25))
            radius = 50
            
            ring_color = Color.wrong if remaining_time == 0 else Color.border
            pygame.draw.circle(self.surface, ring_color, center, radius+4, 4)

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

                center_color = Color.timer if remaining_time > 1 else Color.wrong
                pygame.draw.polygon(self.surface, center_color, points)
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
        self.grid_surface.advance_turn(self.current_player)
        
    def time_update(self):
        # Resolve pending bot answer after 1s
        if self.bot_action and now_is_time(self.bot_action[2]):
            print("triggered")

            bot, pos, time = self.bot_action
            self.bot_action = None
            
            Surface_Manager.click_at(pos, bot)
            
        if self.session_time and now_is_time(self.session_time):
            self.session_time = None
            print(pygame.time.get_ticks())
            
            self.stage = "Answering"
            
            self.timer_time = pygame.time.get_ticks()
            
            # Screen flash in player color
            Surface_Manager.add_surface(BorderFlash(self.current_player))
            
            self.schedule_bot_action()
    
        # Kill surface after 1s delay
        if self.close_time and now_is_time(self.close_time):
            Surface_Manager.remove_surface(self)

        # --- Timeout handling ---
        if self.stage == "Answering" and self.session_remaining_time() <= 0:
            self.stage = "Timeout Re-buzz"
            self.schedule_bot_action()

    def on_click(self, pos: Vec2, player: Player):
        print(pos, player)
        
        if self.stage in ["Buzz", "Wrong Re-buzz", "Timeout Re-buzz"] and self.buzz_rect.collidepoint(pos):
            answered_players = map(lambda x: x[0], self.submitted_answers)
            
            if player == self.current_player or player in answered_players:
                warn("You are not allowed to buzz!")
                return
            
            # When someone is robbed he cannot answered again
            if self.current_player:
                self.submitted_answers.append((self.current_player, -1))
                
            self.current_player = player
            self.bot_action = None # Clear all bot actions
            
            notify(f"{player.name} buzzed!")
            
            self.session_time = now() + 100
            print("Session Time Setup", self.session_time)
        
        if self.stage == "Answering" or self.stage == "Timeout Re-buzz":
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    if player != self.current_player:
                        warn("Only the current player can answer!")
                        return

                    selected_answers = map(lambda x: x[1], self.submitted_answers)
                    if i in selected_answers:
                        warn("This answer is already selected!")
                    
                    self.submitted_answers.append((player, i))
                    
                    if self.question.answer_index == i:
                        self.stage = "Result"
                        self._frozen_timer_time = self.session_remaining_time()
                        
                        player.add_score(self.question.value)
                        
                        notify(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                        
                        self.close_time = pygame.time.get_ticks() + 1000
                    else:
                        self.stage = "Wrong Re-buzz"
                        
                        player.add_score(-self.question.value)
                        
                        notify(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")

                        self.schedule_bot_action()