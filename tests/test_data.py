"""Tests for game data validity and schema compliance."""

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "data"
GAME_DATA_PATH = DATA_DIR / "game_data.json"
SCHEMA_PATH = DATA_DIR / "schemas" / "game_data_schema.json"


@pytest.fixture
def game_data() -> dict:
    """Load game_data.json."""
    if not GAME_DATA_PATH.exists():
        pytest.skip("game_data.json not yet generated (Phase 1)")
    with open(GAME_DATA_PATH) as f:
        return json.load(f)


@pytest.fixture
def schema() -> dict:
    """Load the JSON schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def test_schema_exists():
    """Schema file should exist."""
    assert SCHEMA_PATH.exists(), "game_data_schema.json is missing"


def test_game_data_validates_against_schema(game_data, schema):
    """game_data.json should conform to the JSON schema."""
    from jsonschema import validate

    validate(instance=game_data, schema=schema)


def test_game_data_has_units(game_data):
    """Should contain units."""
    assert "units" in game_data
    assert len(game_data["units"]) > 0, "No units found in game data"


def test_game_data_has_civilizations(game_data):
    """Should contain civilizations."""
    assert "civilizations" in game_data
    assert len(game_data["civilizations"]) > 0, "No civilizations found"


def test_knight_has_counter_info(game_data):
    """Spot-check: Knight should have counter information."""
    units = game_data.get("units", {})
    # Check for both friendly and internal dat names
    knight = units.get("knight") or units.get("Knight") or units.get("knght")
    if knight is None:
        pytest.skip("Knight unit not yet in game data")
    assert "counters" in knight, "Knight missing counter information"
    assert "strong_vs" in knight["counters"], "Knight missing strong_vs counters"

