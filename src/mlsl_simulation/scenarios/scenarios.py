import json
from pathlib import Path

from mlsl_simulation.game_model.road_network.road_network import Road

_DATA_DIR = Path(__file__).parent / "data"


def load_scenario(scenario_key: str) -> dict:
    filepath = _DATA_DIR / f"{scenario_key.lower()}.json"
    with open(filepath) as f:
        data = json.load(f)
    roads = [Road(r["name"], r["horizontal"], r["top"], r["right"], r["left"]) for r in data["roads"]]
    return {
        "roads": roads,
        "players": data["players"],
        "scenario_name": data["scenario_name"],
    }
