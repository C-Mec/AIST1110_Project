# 23/9 thomas
- Built a Grid_Surface class that draws a 6×5 game board with blue cells, white
borders, and dollar values ($200 to $1000).

- Generated temporary sample questions (one per cell) for testing.

- Implemented mouse click detection: when a cell is clicked, the console prints the row, column, question text, and three answer options.

- Set up the main game loop with event handling and rendering.
# 28/9 thomas
## Bug Fixes （checked by ai）

1. **`get_cell_at_pos` boundary check**  
   - Added index validation to prevent `IndexError` when clicking outside grid.

2. **`draw` method performance / display issue**  
   - Moved `screen.blit(self.surface, self.pos)` outside the nested for-loop (was being called for every cell, causing redundant blits).

---

## New Features / Additions (新增的功能)

1. **Added `QuestionPopup` class**  
   - A modal window that shows the question text and three clickable answer buttons.

2. **Modified `Grid_Surface.__init__`**  
   - Added `manager` and `player` parameters.  
   - Stored `self.manager`, `self.player`, and `self._active_popup`.

3. **Updated `_grid_init`**  
   - Each cell now gets a unique hardcoded question (different per row/col) instead of the same `Question.sample()`.

4. **Rewrote `click_at` method** in `Grid_Surface`  
   - Prevents answering used questions.  
   - Creates a `QuestionPopup` and adds it to the manager.  
   - Implements `on_answer` callback to update player score, mark question used, and remove the popup.

5. **Added `remove_surface` method** to `Surface_Manager`  
   - Enables removal of popup from the manager after answering.

6. **Updated `main.py`**  
   - Created a `Player` instance (`current_player`).  
   - Passed `manager` and `player` to `Grid_Surface` constructor.

