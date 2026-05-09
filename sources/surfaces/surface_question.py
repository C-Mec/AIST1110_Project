import pygame

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

import random
import math

import config
from sources.util import intxy, Color, Font
from sources.manager import manager, Base_Surface
from sources.datatype.question import Question
from sources.datatype.player import Player
from sources.surfaces.visual import notify, BorderFlash

# ----- Question_Surface: a modal window showing question and options -----
class Question_Surface(Base_Surface):
    def __init__(self, question: Question, player: Player, bots: list[Player], grid):
        dimension = Vec2(config.screen_dimension[0] * 0.7,
                         config.screen_dimension[1] * 0.7)  # scale to window
        rect = Surface(dimension).get_rect(center=(config.screen_dimension[0]//2,
                                                   config.screen_dimension[1]//2))
        pos = rect.topleft
        super().__init__(dimension, pos)
        self.grid = grid
        
        self.option_border_color = Color.border
        self.selected_options = None
        self.correct_option_index = None
        self.wrong_option_indices = set()
        self.close_time = None

        self.overshade = True
        self.question = question
        self.player = player
        self.bots = bots

        # Buzz button in upper third
        self.buzz_rect = pygame.Rect(dimension.x//2 - 100, dimension.y//3, 200, 60)
        self.buzzed = False

        # Timer
        self.timer_isActive = False
        self.answer_start_time = None
        self.answer_duration = 5
        
        # Bot
        self.bot_pending = None
        self.bot_buzz_time = None
        self.bots_answered = set()
        
        self.submitted_answers: list[tuple[Player, int]] = None

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

    def schedule_bot_buzz(self):
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

        # mark bot as used
        self.bots_answered.add(bot)

        # apply choice
        self.selected_options = choice
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
            angle = 360 * (remaining_time / self.answer_duration)
            end_angle = -90 - angle

            points = [center]  # start at circle center
            steps = 50  # number of segments for smoothness
            for a in range(-90, int(end_angle), -max(1, int(angle/steps))):
                rad = math.radians(a)
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

                if self.correct_option_index == i:
                    border_color = Color.correct
                elif i in self.wrong_option_indices:
                    border_color = Color.wrong
                else:
                    border_color = Color.border

                pygame.draw.rect(self.surface, border_color, rect, 2)

                option_text = f"{chr(65+i)}. {self.question.options[i]}"
                text = Font.clue_small.render(option_text, True, Color.text)
                self.surface.blit(text, text.get_rect(center=rect.center))
            
        # Drawing Elements
        if self.buzzed:
            if self.timer_isActive:
                draw_timer(self.session_remaining_time())
                
            draw_options()
        else:
            draw_buzz_button()

        screen.blit(self.surface, self.pos)
    
    def update(self):
        # Resolve pending bot answer after 1s
        if self.bot_pending and self.bot_buzz_time and pygame.time.get_ticks() >= self.bot_buzz_time:
            bot, choice = self.bot_pending
            self.bot_pending = None
            self.bot_buzz_time = None
            self.bot_try_answer(bot, choice)
    
        # Kill surface after 1s delay
        if self.close_time and pygame.time.get_ticks() >= self.close_time:
            self.grid.advance_turn()
            manager.remove_surface(self)

        remaining_time = self.session_remaining_time()
        
        if remaining_time <= 0:
            self.player.add_score(-self.question.value)
            
            notify(f"{self.player.name} timed out! -${self.question.value}")
            
            self.timer_active = False

            # Let a bot try to answer
            if self.bots:
                available_bots = [b for b in self.bots if b not in self.bots_answered]
                if not available_bots:
                    return

                bot = random.choice(available_bots)

                # Decide choice now
                remaining_time = [i for i in range(len(self.question.options))
                            if i != self.selected_options]
                if not remaining_time:
                    return

                correct_index = self.question.answer_index
                if len(remaining_time) == 1:
                    choice = correct_index
                elif len(remaining_time) == 2:
                    choice = correct_index if random.random() < 0.7 else [i for i in remaining_time if i != correct_index][0]
                else:
                    choice = correct_index if random.random() < 0.5 else random.choice([i for i in remaining_time if i != correct_index])

                # Schedule buzz between 0.75–3s later
                delay = random.uniform(750, 1750)
                self.bot_buzz_time = pygame.time.get_ticks() + int(delay)

                # Store both bot and choice
                self.bot_pending = (bot, choice)

    def click_at(self, pos: Vec2, player: Player):
        if not self.buzzed and self.buzz_rect.collidepoint(pos):
            self.buzzed = True
            self.timer_isActive = True
            self.answer_start_time = pygame.time.get_ticks()
            
            # Screen flash in player color
            manager.add_surface(BorderFlash(self.player))
            
        elif self.buzzed and self.selected_options is None:  # prevent multiple scoring
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    self.selected_options = i
                    self.timer_isActive = False
                    
                    if self.question.answer_index == i:
                        player.add_score(self.question.value)
                        notify(f"Correct! {player.name} gains ${self.question.value}. Total: ${player.score}")
                        self.correct_option_index = i
                        
                        self.close_time = pygame.time.get_ticks() + 1000
                    else:
                        player.add_score(-self.question.value)
                        notify(f"Wrong! {player.name} loses ${self.question.value}. Total: ${player.score}")
                        self.wrong_option_indices.add(i)

                        self.draw(pygame.display.get_surface())
                        pygame.display.flip()
                        
                        # Let a bot try to answer
                        if self.bots:
                            # pick from bots that haven’t answered yet
                            available_bots = [b for b in self.bots if b not in self.bots_answered]
                            if not available_bots:
                                return

                            bot = random.choice(available_bots)

                            # Decide choice now
                            remaining = [i for i in range(len(self.question.options))
                                        if i != self.selected_options]
                            if not remaining:
                                return

                            correct_index = self.question.answer_index
                            if len(remaining) == 1:
                                choice = correct_index
                            elif len(remaining) == 2:
                                choice = correct_index if random.random() < 0.7 else [i for i in remaining if i != correct_index][0]
                            else:
                                choice = correct_index if random.random() < 0.5 else random.choice([i for i in remaining if i != correct_index])

                            # Schedule buzz between 0.75–3s later
                            delay = random.uniform(750, 1750)
                            self.bot_buzz_time = pygame.time.get_ticks() + int(delay)

                            # Store both bot and choice
                            self.bot_pending = (bot, choice)