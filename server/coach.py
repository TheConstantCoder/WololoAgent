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
        # Build unit summary grouped by class
        units_by_class: dict[str, list[str]] = {}
        for u in self.game_data.get("units", {}).values():
            cls = u.get("class", "other")
            if cls == "building":
                continue  # skip buildings for brevity
            units_by_class.setdefault(cls, []).append(u["name"])

        units_block = ""
        for cls, names in sorted(units_by_class.items()):
            units_block += f"  {cls.title()}: {', '.join(sorted(set(names)))}\n"

        # Build civilization summary
        civs = self.game_data.get("civilizations", {})
        civ_lines = []
        for civ in sorted(civs.values(), key=lambda c: c.get("name", "")):
            name = civ.get("name", "")
            desc = civ.get("description", "")
            uu = civ.get("unique_unit", "")
            bonuses = civ.get("bonuses", [])
            tb = civ.get("team_bonus", "")
            bonus_str = "; ".join(bonuses[:3])  # top 3 to stay concise
            civ_lines.append(f"  {name} ({desc}): UU={uu}. {bonus_str}. TB: {tb}")

        civs_block = "\n".join(civ_lines[:45])  # cap at 45 civs for token budget

        instruction = f"""CRITICAL DIRECTIVE:
1. YOU ARE the 'Wololo Coach'. 
2. ACT as a real-time battle advisor. 
3. NEVER EXPLAIN your reasoning or show your thought process.
4. NEVER use asterisks, bold text, or markdown headers.
5. NEVER start with conversational filler (e.g., "I see you are...", "Analyzing...").
6. ONLY SPEAK the advice.
7. DO NOT use words like "Observing", "Analyzing", "Confirming", or "Evaluating".
8. BE EXTREMELY CONCISE. 1-2 sharp sentences only.

KNOWLEDGE BASE — Age of Empires II: Definitive Edition

UNITS:
{units_block}
CIVS:
{civs_block}

CORE COUNTERS:
  Spears/Halbs → Cavalry
  Skirms → Archers
  Knights → Archers/Siege
  Mangonels → Massed Archers/Infantry
  Monks → Knights/Elephants
  Camels → Cavalry
  Rams → Buildings/Arrows
  BBC → Castles/Siege

ADVICE STYLE:
Provide tactical advice based on counters and civ bonuses.
Example: " Franks are strong. Go Knights and use your extra HP. Watch out for enemy Pikemen."
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
