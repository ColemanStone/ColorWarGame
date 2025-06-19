from .game import ColorWarGame
from .faction import Faction
import random


def main() -> None:
    game = ColorWarGame()
    # Create a few random factions
    for i in range(3):
        color = "#%06x" % random.randint(0, 0xFFFFFF)
        faction = Faction(color=color, name=f"Faction {i+1}")
        game.add_faction(faction)
    game.run()


if __name__ == "__main__":
    main()
