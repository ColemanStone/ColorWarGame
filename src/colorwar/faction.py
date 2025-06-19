from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Faction:
    """Represents a single faction in the color war."""

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
