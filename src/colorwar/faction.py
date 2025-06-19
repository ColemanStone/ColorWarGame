from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Faction:
    """Represents a single faction in the color war.

    Parameters
    ----------
    color:
        Hex string used when rendering the faction on the grid.
    name:
        Human readable faction name.
    expansion_chance:
        Probability that the faction will claim a neighboring cell each tick.
    """

    color: str
    name: str
    behavior: str = "random"
    personality: Dict[str, float] = field(
        default_factory=lambda: {
            "aggression": 1.0,
            "defense": 1.0,
            "expansionism": 1.0,
            "risk": 1.0,
        }
    )
    expansion_chance: float = 0.25
