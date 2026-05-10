import json
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
assert AZURE_API_KEY, "Missing AZURE_API_KEY in .env"

EUS2_BASE_URL = "https://cuhk-apip.azure-api.net/openai-eus2/openai/v1"

client = OpenAI(
    base_url=EUS2_BASE_URL,
    api_key=AZURE_API_KEY,
    default_headers={"api-key": AZURE_API_KEY},
)

class LLMQuestionGenerator:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def generate_board(self, categories: List[str], rows: int = 5, difficulty: str = "normal") -> List[List[Dict]]:
        """
        Returns a 2D list: shape (rows, len(categories))
        Each element is a dict with keys: clue, correct_answer, options
        difficulty: "easy" or "hard" – used for cache file name and prompt
        """
        # cache file name based on categories and difficulty
        cache_file = self.cache_dir / f"board_{'_'.join(categories)}_{difficulty}.json"
        if cache_file.exists():
            print(f"Loading {difficulty} board from cache.")
            with open(cache_file) as f:
                return json.load(f)

        # change the prompt based on difficulty
        difficulty_instruction = ""
        if difficulty == "easy":
            difficulty_instruction = "Use common, well‑known facts. Make the questions easy to answer."
        else:
            difficulty_instruction = "Use more obscure, challenging facts. Make the questions harder."

        prompt = f"""
    You are generating a Jeopardy! game board with {len(categories)} categories:
    {', '.join(categories)}.

    For each category, generate {rows} questions of increasing difficulty.
    {difficulty_instruction}

    Each question must include:
    - clue: a statement (e.g., "This planet is known as the Red Planet.")
    - correct_answer: the complete question phrase (e.g., "What is Mars?")
    - options: three complete question phrases (e.g., "What is Mars?", "What is Venus?", "What is Jupiter?")
    IMPORTANT: The correct_answer string must exactly match one of the options.

    Return ONLY valid JSON in the following exact structure:
    {{
    "board": [
        {{
        "category": "Category name",
        "questions": [
            {{
            "clue": "...",
            "correct_answer": "...",
            "options": ["...", "...", "..."]
            }}
        ]
        }}
    ]
    }}
    """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            content = response.choices[0].message.content
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            data = json.loads(json_str)
            # 2dlist [row][col]
            board_2d = []
            for row_idx in range(rows):
                row_questions = []
                for cat_idx, cat_data in enumerate(data["board"]):
                    q_data = cat_data["questions"][row_idx]
                    row_questions.append({
                        "clue": q_data["clue"],
                        "correct_answer": q_data["correct_answer"],
                        "options": q_data["options"],
                    })
                board_2d.append(row_questions)
            # safe cache
            with open(cache_file, "w") as f:
                json.dump(board_2d, f, indent=2)
            return board_2d
        except Exception as e:
            print(f"LLM generation failed for {difficulty}: {e}. Using fallback questions.")
            return self._fallback_board(categories, rows)
    def _fallback_board(self, categories: List[str], rows: int) -> List[List[Dict]]:
        """Fallback hardcoded questions when API fails."""
        board = []
        for row in range(rows):
            row_q = []
            for cat in categories:
                row_q.append({
                    "clue": f"Sample clue for {cat}, row {row+1}",
                    "correct_answer": "Option A",
                    "options": ["Option A", "Option B", "Option C"],
                })
            board.append(row_q)
        return board