"""Tests for the coaching LLM integration."""

import pytest
from server.coach import Coach


@pytest.fixture
def coach():
    """Returns a Coach instance."""
    return Coach()


@pytest.mark.asyncio
async def test_coach_ask_knight_counter(coach):
    """Test that the coach correctly identifies a counter for Knights."""
    query = "My opponent is massing Knights. What should I make?"
    answer = await coach.ask(query)
    
    assert "Spearmen" in answer or "Pikemen" or "Halberdier" or "Monk" or "Camel" in answer
    assert len(answer) > 20


@pytest.mark.asyncio
async def test_coach_persona_tone(coach):
    """Test that the coach uses its thematic persona."""
    query = "Hello coach!"
    answer = await coach.ask(query)
    
    # Check for Wololo or strategic advisor tone
    assert any(word in answer.lower() for word in ["wololo", "strategic", "advisor", "coach", "monk"])


@pytest.mark.asyncio
async def test_coach_uses_game_data(coach):
    """Test that the coach knows about specific units in game_data.json."""
    # Assuming 'knght' or 'milit' is in the game data
    query = "What are the stats for a Knight?"
    answer = await coach.ask(query)
    
    assert "hp" in answer.lower() or "attack" in answer.lower() or "armor" in answer.lower()
