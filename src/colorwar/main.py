"""Command line entry point for the simplified Color War Game."""

import argparse
import random

from .game import ColorWarGame
from .faction import Faction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play the Color War Game")
    parser.add_argument(
        "--grid-size",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        default=(100, 100),
        help="Width and height of the grid",
    )
    parser.add_argument(
        "--cell-size",
        type=int,
        default=6,
        help="Pixel size of each grid cell",
    )
    parser.add_argument(
        "--factions",
        type=int,
        default=3,
        help="Number of factions to spawn",
    )
    parser.add_argument(
        "--expansion-chance",
        type=float,
        default=0.25,
        help="Chance a faction will claim a neighbor each tick",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = ColorWarGame(grid_size=tuple(args.grid_size), cell_size=args.cell_size)
    for i in range(args.factions):
        color = "#%06x" % random.randint(0, 0xFFFFFF)
        faction = Faction(
            color=color,
            name=f"Faction {i+1}",
            expansion_chance=args.expansion_chance,
        )
        game.add_faction(faction)
    game.run()


if __name__ == "__main__":
    main()
