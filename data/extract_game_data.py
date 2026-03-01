"""Game data extraction script.

Extracts unit, civilization, technology, and counter data from AoE2DE .dat files using genieutils-py.
"""

import json
import pathlib
import datetime
from genieutils import datfile

# Path to the AoE2DE .dat file (adjust if your Steam library is elsewhere)
DAT_PATH = pathlib.Path('/mnt/d/Program Files/Steam/steamapps/common/AoE2DE/resources/_common/dat/empires2_x2_p1.dat')

# Mapping of Genie unit class IDs to schema enum values
CLASS_MAPPING = {
    1: "infantry",   # Infantry
    6: "infantry",   # Infantry
    27: "infantry",  # Spearman
    11: "archer",    # Foot Archer
    30: "archer",    # Hand Cannoneer
    36: "archer",    # Cavalry Archer
    12: "cavalry",   # Cavalry
    13: "siege",     # Siege Weapon
    54: "siege",     # Trebuchet
    5: "naval",      # Ocean Fish
    20: "naval",     # Transport Boat
    21: "naval",     # Fishing Boat
    22: "naval",     # Whale
    18: "monk",      # Monk
    3: "building",   # Building
}

# Mapping of Armor Class IDs to names for counter info
ARMOR_CLASS_NAMES = {
    1: "infantry",
    8: "cavalry",
    11: "building",
    13: "building",
    15: "archer",
    16: "naval",
    19: "unique",
    20: "siege",
    21: "building",
    27: "infantry",
    28: "archer",
    29: "infantry",
    30: "cavalry",
}

def extract_units(df):
    units = {}
    # Use Britons (usually civ 1) or another playable civ to get unit stats
    civ = df.civs[1]
    for unit in civ.units:
        if unit is None or not unit.name:
            continue
            
        # Only extract units that are in our mapped classes
        unit_class_id = unit.class_
        if unit_class_id not in CLASS_MAPPING:
            continue
            
        unit_class = CLASS_MAPPING[unit_class_id]
        
        # Use the unit's internal name as key (lowercased)
        key = unit.name.lower()
        
        # Extract cost
        cost = {"food": 0, "wood": 0, "gold": 0, "stone": 0}
        if unit.creatable:
            for rc in unit.creatable.resource_costs:
                if rc.type == 0: cost["food"] = int(rc.amount or 0)
                elif rc.type == 1: cost["wood"] = int(rc.amount or 0)
                elif rc.type == 2: cost["stone"] = int(rc.amount or 0)
                elif rc.type == 3: cost["gold"] = int(rc.amount or 0)

        # Extract attack, armor, and counters
        attack = 0
        armor = {"melee": 0, "pierce": 0}
        strong_vs = set()
        
        if unit.type_50:
            # First attack entry is usually the base attack
            if unit.type_50.attacks:
                attack = int(unit.type_50.attacks[0].amount or 0)
                
            # Collect attack bonuses (counters)
            for att in unit.type_50.attacks:
                if att.amount > 0 and att.class_ in ARMOR_CLASS_NAMES:
                    strong_vs.add(ARMOR_CLASS_NAMES[att.class_])
            
            # Find melee (class 4) and pierce (class 3) armor
            for arm in unit.type_50.armours:
                if arm.class_ == 4: armor["melee"] = int(arm.amount or 0)
                elif arm.class_ == 3: armor["pierce"] = int(arm.amount or 0)

        units[key] = {
            "name": unit.name,
            "class": unit_class,
            "age": "unknown",
            "cost": cost,
            "hp": int(unit.hit_points or 0),
            "attack": attack,
            "armor": armor,
            "range": float(unit.type_50.max_range or 0.0) if unit.type_50 else 0.0,
            "speed": float(unit.speed or 0.0),
            "training_time": 0,
            "counters": {
                "strong_vs": sorted(list(strong_vs)),
                "weak_vs": [],
            },
        }
    return units

def extract_civilizations(df):
    civs = {}
    for civ in df.civs:
        if not civ.name:
            continue
        key = civ.name.lower()
        civs[key] = {
            "name": civ.name,
            "bonuses": [],
            "team_bonus": None,
            "unique_unit": None,
            "unique_techs": {},
        }
    return civs

def extract_technologies(df):
    techs = {}
    for tech in df.techs:
        if not tech.name:
            continue
        key = tech.name.lower()
        cost = {"food": 0, "wood": 0, "gold": 0, "stone": 0}
        if hasattr(tech, 'resource_costs'):
            for rc in tech.resource_costs:
                if rc.type == 0: cost["food"] = int(rc.amount or 0)
                elif rc.type == 1: cost["wood"] = int(rc.amount or 0)
                elif rc.type == 2: cost["stone"] = int(rc.amount or 0)
                elif rc.type == 3: cost["gold"] = int(rc.amount or 0)
            
        techs[key] = {
            "name": tech.name,
            "age": "unknown",
            "cost": cost,
            "effect": None,
        }
    return techs

def main():
    if not DAT_PATH.exists():
        raise FileNotFoundError(f"Dat file not found at {DAT_PATH}")
    df = datfile.DatFile.parse(DAT_PATH)
    data = {
        "meta": {
            "version": getattr(df, "version", "unknown"),
            "extracted_at": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
            "source": str(DAT_PATH),
        },
        "units": extract_units(df),
        "civilizations": extract_civilizations(df),
        "technologies": extract_technologies(df),
    }
    output_path = pathlib.Path(__file__).parent.parent / "data" / "game_data.json"
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Game data written to {output_path}")

if __name__ == "__main__":
    main()
