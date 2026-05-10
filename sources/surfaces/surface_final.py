import pygame, random, config, json
from sources.manager import manager, Base_Surface, Game_Manager
from sources.surfaces.surface_end import End_Surface
from sources.datatype.player import Player
from sources.util import Font, Color, intxy
from pathlib import Path

Surface = pygame.Surface
Rect = pygame.Rect
Vec2 = pygame.Vector2

class FinalJeopardy(Base_Surface):
    def __init__(self, dimension: Vec2, pos: Vec2, players: list[Player], used_index: int):
        screen_w, screen_h = config.screen_dimension
        margin_x = int(screen_w * 0.18)
        margin_y = int(screen_h * 0.195)

        grid_w = screen_w - 2 * margin_x
        grid_h = screen_h - 1.8 * margin_y

        dimension = Vec2(grid_w, grid_h)
        pos = Vec2(margin_x, margin_y)

        super().__init__(dimension, pos)

        categories = ["History", "Science", "Literature", "Sports", "Music", "Miscellaneous"]
        cache_file = Path("cache") / f"board_{'_'.join(categories)}_hard_{used_index}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                board_data = json.load(f)
            # bottom row is the last index
            final_row = board_data[-1]
            # pick a random column
            col_idx = random.randrange(len(final_row))
            q_data = final_row[col_idx]

            self.category = categories[col_idx]
            self.clue = q_data["clue"]
            self.option = q_data["options"]
            self.correct_option = q_data["correct_answer"]
        else:
            # fallback if file missing
            self.category = "Final Jeopardy"
            self.clue = "Sample final clue"
            self.option = ["Option A", "Option B", "Option C"]
            self.correct_option = "Option A"
        
        self.confirmed = False
        self.input_text = ""
        self.active_box = False
        self.phase = "wager"
        
        # Countdowns
        self.no_wager_start = None
        self.end_countdown = None
        
        self.screen_w, self.screen_h = intxy(config.screen_dimension)
        self.background = pygame.image.load("assets/Jeopardy-BoardAlt.webp").convert()
        self.background = pygame.transform.smoothscale(self.background, (self.screen_w, self.screen_h))

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

    def on_click(self, pos, player):
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
            human = next(p for p in Game_Manager.players if not p.bot)
            if human.score < 1:
                # Start timer for "Cannot wager" message
                self.no_wager_start = pygame.time.get_ticks()
                return
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
        human = next(p for p in Game_Manager.players if not p.bot)
        human.final_answer = f"What is {self.input_text.strip()}?"
        self.confirmed = True
        print(f"{human.name} answered: {human.final_answer}")

        self.end_countdown = pygame.time.get_ticks()

        for p in Game_Manager.players:
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
        for p in Game_Manager.players:
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
        if self.end_countdown and pygame.time.get_ticks() - 6000 > self.end_countdown:
            # Call end surface
            end_surface = End_Surface(Vec2(self.screen_w, self.screen_h), Vec2(0,0))
            manager.add_surface(end_surface)
            manager.remove_surface(self)
        
        screen.blit(self.background, (2, 0))
        self.surface.fill(Color.background)

        # Title
        shadow = Font.logo_large.render("Final Jeopardy!", True, Color.shadow)
        title = Font.logo_large.render("Final Jeopardy!", True, Color.text)
        self.surface.blit(shadow, (self.surface.get_width()//2 - title.get_width()//2 + 2, 20 + 2))
        self.surface.blit(title, (self.surface.get_width()//2 - title.get_width()//2, 20))

        human = Game_Manager.players[0]

        # --- Always show wagers at bottom ---
        y = self.surface.get_height() - 100
        x_positions = [self.surface.get_width()//5,
                    self.surface.get_width()//2,
                    4*self.surface.get_width()//5]

        for i, p in enumerate(Game_Manager.players):
            if self.phase == "wager":
                if p.score < 1:
                    # Cannot wager
                    line1 = Font.clue_medium.render(f"{p.name}", True, Color.text)
                    line2 = Font.clue_medium.render("Cannot wager", True, Color.text)
                    rect1 = line1.get_rect(center=(x_positions[i], y))
                    rect2 = line2.get_rect(center=(x_positions[i], y+25))
                    self.surface.blit(line1, rect1)
                    self.surface.blit(line2, rect2)
                else:
                    line1 = Font.clue_medium.render(f"{p.name}", True, Color.text)
                    line2 = Font.clue_medium.render(f"wagering...", True, Color.text)
                    rect1 = line1.get_rect(center=(x_positions[i], y))
                    rect2 = line2.get_rect(center=(x_positions[i], y+25))
                    self.surface.blit(line1, rect1)
                    self.surface.blit(line2, rect2)
            elif self.phase == "answer":
                if p.wager == 0:
                    line1 = Font.clue_medium.render(f"{p.name}", True, Color.text)
                    line2 = Font.clue_medium.render(f"Did not wager", True, Color.text)
                    rect1 = line1.get_rect(center=(x_positions[i], y))
                    rect2 = line2.get_rect(center=(x_positions[i], y+25))
                    self.surface.blit(line1, rect1)
                    self.surface.blit(line2, rect2)
                else:
                    line1 = Font.clue_medium.render(f"{p.name}", True, Color.text)
                    line2 = Font.clue_medium.render(f"Wager: ${p.wager}", True, Color.text)
                    rect1 = line1.get_rect(center=(x_positions[i], y))
                    rect2 = line2.get_rect(center=(x_positions[i], y+25))
                    self.surface.blit(line1, rect1)
                    self.surface.blit(line2, rect2)

            # Show answer under wager if exists
            if hasattr(p, "final_answer"):
                ans_text = p.final_answer
                # Wrap answer text to fit within ~200px width
                max_width = 200
                lines = self.wrap_text(ans_text, Font.clue_small, max_width)

                y_offset = y + 55
                for line in lines:
                    ans_rendered = Font.clue_small.render(line, True, Color.text)
                    ans_rect = ans_rendered.get_rect(center=(x_positions[i], y_offset))
                    self.surface.blit(ans_rendered, ans_rect)
                    y_offset += ans_rendered.get_height() + 2

        # --- PHASE 1: WAGER ---
        if self.phase == "wager":
            # Draw the category title centered near the top
            category_text = Font.category_large.render(self.category, True, Color.text)

            # Shadow effect for readability
            shadow = Font.category_large.render(self.category, True, Color.shadow)
            shadow_rect = shadow.get_rect(center=(self.surface.get_width()//2,
                                                120 + 2))  # slight offset down
            self.surface.blit(shadow, shadow_rect)

            rect = category_text.get_rect(center=(self.surface.get_width()//2, 120))
            self.surface.blit(category_text, rect)

            # Optional underline below category
            underline_y = rect.bottom + 5
            pygame.draw.line(self.surface, Color.border,
                            (rect.left, underline_y),
                            (rect.right, underline_y), 2)
            
            if human.score < 1:
                # Centered two-line message
                msg1 = Font.clue_medium.render("Cannot wager", True, Color.text)
                msg2 = Font.clue_medium.render(f"Your ${human.score} < Min Wager $1", True, Color.text)

                rect1 = msg1.get_rect(center=(self.surface.get_width()//2,
                                            self.surface.get_height()//2 - 20))
                rect2 = msg2.get_rect(center=(self.surface.get_width()//2,
                                            self.surface.get_height()//2 + 20))

                self.surface.blit(msg1, rect1)
                self.surface.blit(msg2, rect2)

                # After 2 seconds, move to answer phase
                if self.no_wager_start:
                    elapsed = pygame.time.get_ticks() - self.no_wager_start
                    if elapsed >= 3000:
                        self.no_wager_start = pygame.time.get_ticks()
                        self.phase = "answer"
                else:
                    self.no_wager_start = pygame.time.get_ticks()
            else:
                # Normal wager input centered
                prompt = Font.clue_medium.render(f"{human.name}, enter your wager (0–{human.score}):", True, Color.text)
                rect = prompt.get_rect(center=(self.surface.get_width()//2,
                                            self.surface.get_height()//2 - 45))
                self.surface.blit(prompt, rect)

                box_w, box_h = 200, 40
                self.box_rect = Rect(self.surface.get_width()//2 - box_w//2,
                                    self.surface.get_height()//2 - box_h//2,
                                    box_w, box_h)
                color = Color.white if not self.active_box else Color.greyed
                pygame.draw.rect(self.surface, color, self.box_rect, 0)
                pygame.draw.rect(self.surface, Color.border, self.box_rect, 2)

                # Render wager text centered inside the box
                text_surface = Font.clue_medium.render(self.input_text, True, Color.text)
                text_rect = text_surface.get_rect(center=self.box_rect.center)
                self.surface.blit(text_surface, text_rect)

                # Caret blinking (center aligned after text)
                if self.active_box and not self.confirmed:
                    if (pygame.time.get_ticks() // 500) % 2 == 0:
                        caret_x = text_rect.right + 2
                        caret_y = text_rect.top
                        caret_height = text_surface.get_height()
                        pygame.draw.line(self.surface, Color.text,
                                        (caret_x, caret_y),
                                        (caret_x, caret_y + caret_height), 2)

                # Confirm button centered
                self.confirm_button = Rect(self.surface.get_width()//2 - 60,
                                        self.surface.get_height()//2 + 30,
                                        120, 40)
                pygame.draw.rect(self.surface, Color.greyed if self.confirmed else Color.white, self.confirm_button)
                pygame.draw.rect(self.surface, Color.border, self.confirm_button, 2)
                btn_text = Font.clue_medium.render("Confirm", True, Color.text)
                btn_rect = btn_text.get_rect(center=self.confirm_button.center)
                self.surface.blit(btn_text, btn_rect)

        # --- PHASE 2: ANSWER ---
        elif self.phase == "answer":
            # Show clue where wager input was
            max_width = self.surface.get_width() - 80
            lines = self.wrap_text(self.clue, Font.clue_medium, max_width)
            y = self.surface.get_height()//2 - 120
            for line in lines:
                rendered = Font.clue_medium.render(line, True, Color.text)
                rect = rendered.get_rect(center=(self.surface.get_width()//2, y))
                self.surface.blit(rendered, rect)
                y += rendered.get_height() - 5

            if self.end_countdown and pygame.time.get_ticks() - 2000 > self.end_countdown:
                correct_text = Font.clue_medium.render(f"Correct Answer: {self.correct_option}", True, Color.text)
                shadow_text = Font.clue_medium.render(f"Correct Answer: {self.correct_option}", True, Color.shadow)

                rect = correct_text.get_rect(center=(self.surface.get_width()//2,
                                                    self.surface.get_height()//2))
                shadow_rect = rect.copy()
                shadow_rect.x += 2
                shadow_rect.y += 2

                self.surface.blit(shadow_text, shadow_rect)
                self.surface.blit(correct_text, rect)

                # After showing the answer, start the end countdown
                if not self.end_countdown:
                    self.end_countdown = pygame.time.get_ticks()
            else:
                if human.wager == 0:
                    msg1 = Font.clue_medium.render("Did not wager", True, Color.text)

                    rect1 = msg1.get_rect(center=(self.surface.get_width()//2,
                                                self.surface.get_height()//2 - 20))

                    self.surface.blit(msg1, rect1)

                    if not self.end_countdown:
                        self.end_countdown = pygame.time.get_ticks()
                else:
                    # --- Answer input centered in 3 parts ---
                    prefix = " ".join(str(self.correct_option).split()[0:2])

                    # Line 1: "What/Who is"
                    line1 = Font.clue_medium.render(prefix, True, Color.text)
                    rect1 = line1.get_rect(center=(self.surface.get_width()//2,
                                                self.surface.get_height()//2 - 40))
                    self.surface.blit(line1, rect1)

                    # Line 2: input box
                    box_w, box_h = 400, 40
                    self.answer_box = Rect(self.surface.get_width()//2 - box_w//2,
                                        self.surface.get_height()//2 - 25,
                                        box_w, box_h)
                    color = Color.white if not self.active_box else Color.greyed
                    pygame.draw.rect(self.surface, color, self.answer_box, 0)
                    pygame.draw.rect(self.surface, Color.border, self.answer_box, 2)

                    text_surface = Font.clue_medium.render(self.input_text, True, Color.text)
                    text_rect = text_surface.get_rect(center=self.answer_box.center)
                    self.surface.blit(text_surface, text_rect)

                    # Caret blinking inside input box
                    if self.active_box and not self.confirmed:
                        if (pygame.time.get_ticks() // 500) % 2 == 0:
                            caret_x = text_rect.right + 2
                            caret_y = text_rect.top
                            caret_height = text_surface.get_height()
                            pygame.draw.line(self.surface, Color.text,
                                            (caret_x, caret_y),
                                            (caret_x, caret_y + caret_height), 2)

                    # Line 3: "?"
                    line3 = Font.clue_medium.render("?", True, Color.text)
                    rect3 = line3.get_rect(center=(self.surface.get_width()//2,
                                                self.surface.get_height()//2 + 30))
                    self.surface.blit(line3, rect3)

                    # Confirm button below
                    self.confirm_button = Rect(self.surface.get_width()//2 - 60,
                                            self.surface.get_height()//2 + 50,
                                            120, 40)
                    pygame.draw.rect(self.surface, Color.greyed if self.confirmed else Color.white, self.confirm_button)
                    pygame.draw.rect(self.surface, Color.border, self.confirm_button, 2)
                    btn_text = Font.clue_medium.render("Confirm", True, Color.text)
                    btn_rect = btn_text.get_rect(center=self.confirm_button.center)
                    self.surface.blit(btn_text, btn_rect)
        
        screen.blit(self.surface, self.pos)


        
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



