"""Gemini coach integration.

Handles LLM interactions: loading game context, constructing prompts,
and generating strategic coaching responses.
"""

import json
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from server.config import settings


class Coach:
    """AoE2 Battle Coach powered by Gemini."""

    def __init__(self):
        self._client = None
        self.model_id = settings.gemini_model
        self.game_data = self._load_game_data()
        self.system_instruction = self._construct_system_instruction()

    @property
    def client(self) -> Optional[genai.Client]:
        """Lazy initialization of the Gemini client."""
        if self._client is None:
            if not settings.gemini_api_key:
                return None
            try:
                # Use v1alpha for Multimodal Live API features
                self._client = genai.Client(
                    api_key=settings.gemini_api_key,
                    http_options=types.HttpOptions(api_version='v1alpha')
                )
            except Exception:
                return None
        return self._client

    def _load_game_data(self) -> dict:
        """Load extracted game data from JSON."""
        path = Path(settings.game_data_path)
        if not path.exists():
            return {"units": {}, "civilizations": {}, "technologies": {}}
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {"units": {}, "civilizations": {}, "technologies": {}}

    def _construct_system_instruction(self) -> str:
        """Construct the system instruction for the coach persona."""
        units = list(self.game_data.get("units", {}).keys())
        units_summary = ", ".join(units[:30])
        
        instruction = f"""You are the 'Wololo Coach', an expert Age of Empires II: Definitive Edition strategic advisor.
Your goal is to provide concise, actionable, and accurate mid-game advice to players.

KNOWLEDGE BASE:
You have access to canonical game data for units, civilizations, and technologies.
Units available in your data include: {units_summary}... (and many more).

GUIDELINES:
1. Be concise. Players are in the middle of a battle and need quick answers.
2. Be strategic. Don't just give stats; explain WHY a certain unit or technology is a good counter.
3. Be accurate. Use the provided game data to ground your answers.
4. Tone: Helpful, authoritative, and slightly thematic (use 'Wololo' occasionally but don't overdo it).
5. If you don't know an answer or it's not in the data, prioritize general high-level AoE2 strategy.

When asked about counters, consider armor classes:
- Spearmen (SPRMN) are strong vs Cavalry.
- Skirmishers (SKIRM) are strong vs Archers.
- Mangonels (MANGN) are strong vs grouped Archers and Buildings.
"""
        return instruction

    async def ask(self, query: str) -> str:
        """Generate a coaching response for a text query."""
        if not self.client:
            return "Coach Error: GEMINI_API_KEY not set. Please provide an API key (WOLOLO_GEMINI_API_KEY in .env) to enable coaching."

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            return f"Coach Error: Failed to generate response. {str(e)}"


# Global coach instance
coach = Coach()
