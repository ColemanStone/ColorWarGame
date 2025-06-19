import random
from typing import Dict, Tuple

import pygame

from .faction import Faction


class ColorWarGame:
    """Simplified Color War simulation using pygame."""

    def __init__(self, grid_size: Tuple[int, int] = (100, 100), cell_size: int = 6):
        pygame.init()
        self.cell_size = cell_size
        self.grid_width, self.grid_height = grid_size
        self.screen = pygame.display.set_mode(
            (self.grid_width * cell_size, self.grid_height * cell_size)
        )
        pygame.display.set_caption("Color War Game")
        self.clock = pygame.time.Clock()

        self.grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.factions: Dict[str, Faction] = {}
        self.running = True

    def add_faction(self, faction: Faction, count: int = 20) -> None:
        """Place a new faction on the grid."""
        self.factions[faction.color] = faction
        placed = 0
        while placed < count:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if self.grid[y][x] is None:
                self.grid[y][x] = faction.color
                placed += 1

    def step(self) -> None:
        new_grid = [row[:] for row in self.grid]
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                color = self.grid[y][x]
                if color is None:
                    continue
                faction = self.factions.get(color)
                if faction is None:
                    continue

                directions = [(0, 1), (1, 0), (-1, 0), (0, -1)]
                random.shuffle(directions)
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        if new_grid[ny][nx] is None and random.random() < 0.25:
                            new_grid[ny][nx] = color
                            break
        self.grid = new_grid

    def draw(self) -> None:
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                color = self.grid[y][x]
                if color:
                    pygame.draw.rect(
                        self.screen,
                        pygame.Color(color),
                        pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size),
                    )
                else:
                    pygame.draw.rect(
                        self.screen,
                        pygame.Color("black"),
                        pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size),
                    )

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.step()
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()
