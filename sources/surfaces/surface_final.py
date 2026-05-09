import pygame, random
from sources.manager import manager, Base_Surface
from sources.datatype.player import Player
from sources.util import Font, Color

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

class FinalJeopardy(Base_Surface):
    def __init__(self, dimension: Vec2, pos: Vec2, players: list[Player]):
        # Scale to 70% of window size
        screen_w, screen_h = config.screen_dimension
        dimension = Vec2(screen_w * 0.7, screen_h * 0.7)

        # Center popup
        rect = Surface(dimension).get_rect(center=(screen_w // 2, screen_h // 2))
        pos = Vec2(rect.topleft)

        super().__init__(dimension, pos)

        self.players = players
        self.category = "PlaceHolder"
        self.clue = "Type answer"
        self.confirmed = False
        self.input_text = ""
        self.active_box = False
        self.phase = "wager"
        self.option = ["answer", "Answer", "anwer"]
        self.answer = "What is answer?"

        # Precompute bot wagers (unchanged)
        sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
        leader = sorted_players[0]
        second = sorted_players[1] if len(sorted_players) > 1 else None
        for p in players:
            if p.bot:
                if p == leader and second:
                    p.wager = min(p.score, second.score * 2 + 1)
                elif p == second and leader:
                    p.wager = min(p.score, leader.score - p.score + 1)
                else:
                    p.wager = p.score
            else:
                p.wager = 0

        # Input boxes relative to popup size
        self.box_rect = Rect(40, 220, 200, 40)
        self.confirm_button = Rect(260, 220, 120, 40)
        self.answer_box = Rect(40, 320, 400, 40)

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

    def click_at(self, pos, player):
        if self.phase == "wager":
            if self.box_rect.collidepoint(pos):
                self.active_box = True
            else:
                self.active_box = False
            
            if self.confirm_button.collidepoint(pos):
                self._confirm_wager()
            
        elif self.phase == "answer":
            if self.answer_box.collidepoint(pos):
                self.active_box = True
            else:
                self.active_box = False
            
            if self.confirm_button.collidepoint(pos):
                self._lock_answer()
        
                
    def _confirm_wager(self):
        try:
            human = next(p for p in self.players if not p.bot)
            human.wager = max(0, min(int(self.input_text), human.score))
            print(f"{human.name} wagered ${human.wager}")
            self.phase = "answer"
            self.active_box = False
            self.confirmed = False
            self.input_text = ""
        except (ValueError, StopIteration):
            print(f"Confirm failed {self.input_text}")
            self.input_text = ""


    def _lock_answer(self):
        human = next(p for p in self.players if not p.bot)
        human.final_answer = self.input_text.strip()
        self.confirmed = True
        print(f"{human.name} answered: {human.final_answer}")

        for p in self.players:
            if p.bot:
                # Assign weights: 0.5 for correct, 0.25 for each wrong
                weights = []
                for opt in self.option:
                    if opt == self.correct_option:
                        weights.append(0.5)
                    else:
                        weights.append(0.25)

                p.final_answer = random.choices(self.option, weights, k=1)[0]
                print(f"{p.name} answered: {p.final_answer}")

        # --- Scoring ---
        for p in self.players:
            if p.bot:
                if p.final_answer == self.correct_option:
                    p.score += p.wager
                    print(f"{p.name} correct! +${p.wager}")
                else:
                    p.score -= p.wager
                    print(f"{p.name} wrong! -${p.wager}")
            else:
                if human.final_answer.lower() == self.correct_option.lower():
                    human.score += human.wager
                    print(f"{human.name} correct! +${human.wager}")
                else:
                    human.score -= human.wager
                    print(f"{human.name} wrong! -${human.wager}")

    
    def draw(self, screen: Surface):
        self.surface.fill(Color.background)

        # Title
        title = Font.logo_large.render("Final Jeopardy", True, Color.text)
        self.surface.blit(title, (self.surface.get_width()//2 - title.get_width()//2, 20))

        # Category
        cat_text = Font.category_medium.render(f"Category: {self.category}", True, Color.white)
        self.surface.blit(cat_text, (40, 80))

        # Clue
        clue_text = Font.clue_medium.render(self.clue, True, Color.text)
        clue_rect = clue_text.get_rect(topleft=(40, 120))
        self.surface.blit(clue_text, clue_rect)

        human = self.players[0]
        if self.phase == "wager":
            prompt = Font.clue_medium.render(f"{human.name}, enter your wager (0–{human.score}):", True, Color.text)
            self.surface.blit(prompt, (40, 180))

            color = Color.white if not self.active_box else Color.greyed
            pygame.draw.rect(self.surface, color, self.box_rect, 0)
            pygame.draw.rect(self.surface, Color.border, self.box_rect, 2)

            text_surface = Font.clue_medium.render(self.input_text, True, Color.text)
            self.surface.blit(text_surface, (self.box_rect.x+5, self.box_rect.y+5))

            if self.active_box and not self.confirmed:
                # Blink every ~500ms
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    caret_x = self.box_rect.x + 5 + text_surface.get_width() + 2
                    caret_y = self.box_rect.y + 5
                    caret_height = text_surface.get_height()
                    pygame.draw.line(self.surface, Color.text,
                                    (caret_x, caret_y),
                                    (caret_x, caret_y + caret_height), 2)
            
            # Confirm button
            self.confirm_button = Rect(260, 220, 120, 40)
            pygame.draw.rect(self.surface, Color.greyed if self.confirmed else Color.white, self.confirm_button)
            pygame.draw.rect(self.surface, Color.border, self.confirm_button, 2)
            btn_text = Font.clue_medium.render("Confirm", True, Color.text)
            btn_rect = btn_text.get_rect(center=self.confirm_button.center)
            self.surface.blit(btn_text, btn_rect)
            
        elif self.phase == "answer":
            prompt = Font.clue_medium.render(f"{human.name}, enter your answer:", True, Color.text)
            self.surface.blit(prompt, (40, 180))
            
            # draw answer input box
            color = Color.white if not self.active_box else Color.greyed
            pygame.draw.rect(self.surface, color, self.answer_box, 0)
            pygame.draw.rect(self.surface, Color.border, self.answer_box, 2)
            
            answer_display = f"What is {self.input_text}?"
            text_surface = Font.clue_medium.render(answer_display, True, Color.text)
            self.surface.blit(text_surface, (self.answer_box.x+5, self.answer_box.y+5))
            
            # Caret blinking (answer phase)
            if self.active_box and not self.confirmed:
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    caret_x = self.answer_box.x + 5 + Font.clue_medium.size(answer_display)[0] + 2
                    caret_y = self.answer_box.y + 5
                    caret_height = text_surface.get_height()
                    pygame.draw.line(self.surface, Color.text,
                                    (caret_x, caret_y),
                                    (caret_x, caret_y + caret_height), 2)
            
            # Confirm button
            self.confirm_button = Rect(520, 320, 120, 40)
            pygame.draw.rect(self.surface, Color.greyed if self.confirmed else Color.white, self.confirm_button)
            pygame.draw.rect(self.surface, Color.border, self.confirm_button, 2)
            btn_text = Font.clue_medium.render("Confirm", True, Color.text)
            btn_rect = btn_text.get_rect(center=self.confirm_button.center)
            self.surface.blit(btn_text, btn_rect)

        screen.blit(self.surface, self.pos)
        
    def resize(self, new_dimension: Vec2):
        # Resize Final Jeopardy popup proportionally to new window size.
        screen_w, screen_h = intxy(new_dimension)

        # Scale to 70% of window
        self.dimension = Vec2(screen_w * 0.7, screen_h * 0.7)

        # Recreate surface buffer
        self.surface = Surface(self.dimension, pygame.SRCALPHA)

        # Center popup
        rect = self.surface.get_rect(center=(screen_w // 2, screen_h // 2))
        self.pos = Vec2(rect.topleft)
        self.rect = rect

        # Recompute input boxes relative to new popup size
        self.box_rect = Rect(40, 220, 200, 40)
        self.confirm_button = Rect(260, 220, 120, 40)
        self.answer_box = Rect(40, 320, 400, 40)

