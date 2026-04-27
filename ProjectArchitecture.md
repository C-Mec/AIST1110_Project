## Project Architecture Summary(by ai)

### Core Pattern
**Object-oriented + Layer-based UI management** on Pygame.

### Main Modules (`ui.py`)

| Class | Responsibility |
|-------|----------------|
| `Base_Surface` | Base class for all UI components. Has its own `Surface` and position. |
| `Surface_Manager` | Manages Z-order, adds/removes surfaces, handles mouse collision, renders all layers. |
| `Grid_Surface` | The game board (6×5). Draws cells, stores `Question` objects, handles clicks → creates popup. |
| `QuestionPopup` | Modal window showing question + 3 answer buttons. Uses callback to return result. |
| `Question` | Data model: text, options, correct index, value, used flag. |
| `Player` | Name, score, add_score(). |

### Main Loop (`main.py`)
- Create Pygame window and `Surface_Manager`
- Create `Player` (human) and `Grid_Surface` (pass manager + player)
- Event loop: mouse click → manager finds top surface → calls `click_at()`
- `manager.render()` draws everything

### Data Flow
```
Click → Manager → Grid_Surface.click_at() → Create QuestionPopup (add to manager)
→ User clicks option → Popup callback → Update player.score, mark question used, remove popup
→ Render updates
```

### Completed (Milestone 1)
- Board with unique hardcoded questions
- Popup with question and options
- Score update (correct +value, wrong -value)
- Question can be answered only once

### Next (Milestone 2)
- AI players (auto-choose cells, probability answers, fake delay)
- Rounds (Jeopardy / Double / Final)
- Daily Double + wagering slider
- ChatGPT-generated questions

---
