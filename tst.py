# ColorWarGame.py — Eternal AI Faction Simulator (Console-Free Enhanced)

import random
import threading
import time
import pickle
import os
import sys
import pygame
import pygame_gui
from tkinter import filedialog, Tk
import gc


class AISim:
    def __init__(self):
        # Grid and rendering setup
        self.cell_size = 4
        self.grid_width = 300
        self.grid_height = 550
        self.canvas_width = self.grid_width * self.cell_size
        self.canvas_height = self.grid_height * self.cell_size
        self.progress_height = 160

        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 16)

        self.screen = pygame.display.set_mode(
            (self.canvas_width, self.canvas_height + self.progress_height),
            pygame.NOFRAME
        )
        pygame.display.set_caption("AI Faction Simulator - Eternal Mode")

        self.ui_manager = pygame_gui.UIManager((self.canvas_width, self.canvas_height + self.progress_height))

        # Buttons
        self.save_button = pygame_gui.elements.UIButton(
            pygame.Rect((10, self.canvas_height + 5), (100, 30)), "Save", self.ui_manager
        )
        self.load_button = pygame_gui.elements.UIButton(
            pygame.Rect((120, self.canvas_height + 5), (100, 30)), "Load", self.ui_manager
        )
        self.quit_button = pygame_gui.elements.UIButton(
            pygame.Rect((230, self.canvas_height + 5), (100, 30)), "Quit", self.ui_manager
        )

        # Available AI behaviors
        self.behaviors = [
            "aggressive", "defensive", "random", "chaotic", "teleporter", "sapper", "conqueror",
            "hoarder", "hunter", "rogue", "mirror", "corruptor", "infiltrator", "leech", "hive"
        ]

        # Create starting factions
        self.num_factions = 10
        self.factions = {}
        for i in range(self.num_factions):
            color = self.random_color()
            while color in self.factions:
                color = self.random_color()
            self.factions[color] = {
                "behavior": random.choice(self.behaviors),
                "age": 0, "merges": 0, "offspring": 0,
                "symbol": random.choice(["■", "●", "▲", "◆", "✦", "✶"]),
                "name": f"Faction {i+1}",
                "tier": 1,
                "personality": {
                    "aggression": random.uniform(0.5, 1.5),
                    "defense": random.uniform(0.5, 1.5),
                    "expansionism": random.uniform(0.5, 1.5),
                    "risk": random.uniform(0.5, 1.5)
                }
            }

        # Grid setup
        self.grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.claim_age = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.last_owner = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.overwrite_cooldown = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        self.populate()

        self.biomes = {
            k: set((random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)) for _ in range(300))
            for k in ["forest", "lava", "oasis"]
        }

        self.running = True
        pygame.time.set_timer(pygame.USEREVENT + 99, 100)

    def random_color(self):
        return "#%06x" % random.randint(0, 0xFFFFFF)

    def spawn_rebellion(self, target_color):
        new_color = self.random_color()
        while new_color in self.factions:
            new_color = self.random_color()

        base = self.factions[target_color]
        rebel_name = f"Rebellion {len(self.factions) + 1}"
        self.factions[new_color] = {
            "behavior": random.choice(self.behaviors),
            "age": 0, "merges": 0, "offspring": 0,
            "symbol": random.choice(["☢", "☠", "✪", "✘"]),
            "name": rebel_name,
            "tier": base["tier"],
            "personality": {
                "aggression": min(2.0, base["personality"]["aggression"] + 0.5),
                "defense": max(0.3, base["personality"]["defense"] - 0.2),
                "expansionism": min(2.0, base["personality"]["expansionism"] + 0.3),
                "risk": 2.0
            }
        }

        placed = 0
        attempts = 0
        while placed < 300 and attempts < 5000:
            x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
            if self.grid[y][x] == target_color:
                self.grid[y][x] = new_color
                self.claim_age[y][x] = 0
                self.overwrite_cooldown[y][x] = 8  # grace period
                pygame.draw.rect(self.screen, pygame.Color(new_color),
                                 pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))
                placed += 1
            attempts += 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_q]):
                self.running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.USEREVENT and event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.save_button:
                    self.save_simulation()
                elif event.ui_element == self.load_button:
                    self.load_simulation()
                elif event.ui_element == self.quit_button:
                    self.running = False
                    pygame.time.set_timer(pygame.USEREVENT + 98, 300)
            elif event.type == pygame.USEREVENT + 98:
                self.running = False
            self.ui_manager.process_events(event)

    def populate(self):
        for color in self.factions:
            count = 0
            while count < 30:
                x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
                if self.grid[y][x] is None:
                    self.grid[y][x] = color
                    count += 1

    def save_simulation(self):
        Tk().withdraw()
        file_path = filedialog.asksaveasfilename(defaultextension=".sim", filetypes=[("Simulation Files", "*.sim")])
        if file_path:
            with open(file_path, "wb") as f:
                pickle.dump({"grid": self.grid, "factions": self.factions}, f)

    def load_simulation(self):
        Tk().withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("Simulation Files", "*.sim")])
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = pickle.load(f)
                self.grid = data["grid"]
                self.factions = data["factions"]
    def simulate(self):
        total_cells = self.grid_width * self.grid_height
        cycle_count = 0

        while self.running and pygame.display.get_init():
            # Count faction power
            faction_power = {color: 0 for color in self.factions}
            for row in self.grid:
                for cell in row:
                    if cell in faction_power:
                        faction_power[cell] += 1

            self.step(faction_power)
            self.check_victory(faction_power)

            # Auto merge chance scales with time
            if random.random() < min(0.002 + cycle_count / 200000, 0.08) and len(self.factions) >= 2:
                self.auto_merge_random_factions()

            # Random biome disaster
            if cycle_count % 100 == 0 and random.random() < 0.1:
                self.trigger_disaster()

            # GC to prevent leaks
            if cycle_count % 100 == 0:
                gc.collect()

            # Decay dominant faction if too strong
            if cycle_count % 50 == 0 and faction_power:
                dominant_color, dominant_count = max(faction_power.items(), key=lambda item: item[1])
                if dominant_count / total_cells >= 0.6:
                    removed = 0
                    for _ in range(1000):
                        x = random.randint(0, self.grid_width - 1)
                        y = random.randint(0, self.grid_height - 1)
                        if self.grid[y][x] == dominant_color:
                            self.grid[y][x] = None
                            pygame.draw.rect(self.screen, pygame.Color("black"),
                                             pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))
                            removed += 1
                        if removed >= 100:
                            break

            # Collapse dominant faction if over 70%
            if cycle_count % 200 == 0 and faction_power:
                dominant_color, dominant_count = max(faction_power.items(), key=lambda item: item[1])
                if dominant_count / total_cells >= 0.7:
                    del self.factions[dominant_color]
                    for y in range(self.grid_height):
                        for x in range(self.grid_width):
                            if self.grid[y][x] == dominant_color:
                                self.grid[y][x] = None
                                pygame.draw.rect(self.screen, pygame.Color("black"),
                                                 pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))

            # Rebellion if prolonged stalemate
            if faction_power:
                dominant_color = max(faction_power.items(), key=lambda item: item[1])[0]
                dominant_ratio = faction_power[dominant_color] / total_cells
                if 0.35 <= dominant_ratio <= 0.65 and random.random() < 0.2:
                    self.spawn_rebellion(dominant_color)

            # Cull weakest every 1000 cycles
            if cycle_count % 1000 == 0 and len(self.factions) > 10:
                weakest = min(faction_power.items(), key=lambda item: item[1])[0]
                if weakest in self.factions:
                    del self.factions[weakest]
                    for y in range(self.grid_height):
                        for x in range(self.grid_width):
                            if self.grid[y][x] == weakest:
                                self.grid[y][x] = None

            # Tie breaker — decay both if only 2 factions left
            if len(self.factions) == 2 and cycle_count % 100 == 0:
                for color in list(self.factions):
                    removed = 0
                    for _ in range(100):
                        x = random.randint(0, self.grid_width - 1)
                        y = random.randint(0, self.grid_height - 1)
                        if self.grid[y][x] == color:
                            self.grid[y][x] = None
                            removed += 1

            # Inject noise
            if random.random() < 0.0005:
                x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
                self.grid[y][x] = random.choice(list(self.factions.keys()))

            cycle_count += 1
            time.sleep(0)

    def step(self, faction_power):
        MAX_FACTIONS = 150
        total_cells = max(1, self.grid_width * self.grid_height)
        new_grid = [row[:] for row in self.grid]
        self.grid = new_grid

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.overwrite_cooldown[y][x] > 0:
                    self.overwrite_cooldown[y][x] -= 1

        coords = [(x, y) for y in range(self.grid_height) for x in range(self.grid_width)]
        random.shuffle(coords)

        for x, y in coords:
            color = self.grid[y][x]
            if not color or color not in self.factions or color not in faction_power:
                continue

            dominant_color = max(faction_power.items(), key=lambda item: item[1])[0]
            dominant_ratio = faction_power[dominant_color] / total_cells
            power = faction_power[color] / total_cells

            if color == dominant_color and dominant_ratio >= 0.65:
                power *= 0.8
            elif color != dominant_color and dominant_ratio >= 0.65:
                power *= 1.2

            behavior = self.factions[color]["behavior"]
            personality = self.factions[color]["personality"]

            spread_chance = 0.1 + random.random() * 0.1 * personality["risk"] + power * 0.3 * personality["expansionism"]
            attack_chance = 0.05 + random.random() * 0.1 * personality["risk"] + power * 0.4 * personality["aggression"]

            biome = 1.0
            if (x, y) in self.biomes["forest"]: biome = 0.5
            elif (x, y) in self.biomes["lava"]: biome = 0.1
            elif (x, y) in self.biomes["oasis"]: biome = 2.0

            spread_chance *= biome
            attack_chance *= biome

            directions = [(0, 1), (1, 0), (-1, 0), (0, -1)]
            random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                    continue

                target = self.grid[ny][nx]

                # Fusion
                if (
                    target and target != color and target in self.factions and
                    len(self.factions) < MAX_FACTIONS and random.random() < 0.01
                ):
                    new_color = self.blend_colors(color, target)
                    if new_color not in self.factions:
                        self.factions[new_color] = {
                            "behavior": random.choice([self.factions[color]["behavior"], self.factions[target]["behavior"]]),
                            "age": 0, "merges": 0, "offspring": 0,
                            "symbol": random.choice(["❖", "✶", "⬟", "★"]),
                            "name": f"Fusion of {self.factions[color]['name']} + {self.factions[target]['name']}",
                            "tier": max(self.factions[color]["tier"], self.factions[target]["tier"]) + 1,
                            "personality": {
                                k: (self.factions[color]["personality"][k] + self.factions[target]["personality"][k]) / 2
                                for k in ["aggression", "defense", "expansionism", "risk"]
                            }
                        }
                    new_grid[ny][nx] = new_color
                    if self.running and pygame.display.get_init():
                        pygame.draw.rect(self.screen, pygame.Color(new_color),
                                         pygame.Rect(nx * self.cell_size, ny * self.cell_size, self.cell_size, self.cell_size))
                    continue

                if target is None and random.random() < spread_chance:
                    new_grid[ny][nx] = color
                    if self.running and pygame.display.get_init():
                        pygame.draw.rect(self.screen, pygame.Color(color),
                                         pygame.Rect(nx * self.cell_size, ny * self.cell_size, self.cell_size, self.cell_size))
                    continue

                elif target != color and target in self.factions:
                    if self.overwrite_cooldown[ny][nx] == 0 and self.claim_age[ny][nx] >= 6:
                        if power > faction_power.get(target, 0) or random.random() < attack_chance:
                            new_grid[ny][nx] = color
                            self.overwrite_cooldown[ny][nx] = 4
                            if self.running and pygame.display.get_init():
                                pygame.draw.rect(self.screen, pygame.Color(color),
                                                 pygame.Rect(nx * self.cell_size, ny * self.cell_size, self.cell_size, self.cell_size))

        for faction in self.factions.values():
            faction["personality"]["aggression"] += random.uniform(-0.01, 0.01)
            faction["personality"]["aggression"] = min(max(faction["personality"]["aggression"], 0.3), 2.0)
            faction["personality"]["expansionism"] += random.uniform(-0.01, 0.01)
            faction["personality"]["expansionism"] = min(max(faction["personality"]["expansionism"], 0.3), 2.0)

        self.grid = new_grid
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                self.claim_age[y][x] = (
                    self.claim_age[y][x] + 1 if new_grid[y][x] == self.grid[y][x] else 0
                )
                self.last_owner[y][x] = self.grid[y][x]

    def check_victory(self, power_map=None):
        if power_map is None:
            power_map = {}
            for row in self.grid:
                for color in row:
                    if color:
                        power_map[color] = power_map.get(color, 0) + 1

        total = self.grid_width * self.grid_height
        for color, count in power_map.items():
            if count / total >= 0.95:
                print(f"{self.factions.get(color, {'name': color})['name']} controls 95% of the map!")

    def auto_merge_random_factions(self):
        color1, color2 = random.sample(list(self.factions.keys()), 2)
        new_color = self.blend_colors(color1, color2)
        if new_color in self.factions:
            return

        new_name = f"Merged {self.factions[color1]['name'].split()[1]}-{self.factions[color2]['name'].split()[1]}"
        self.factions[new_color] = {
            "behavior": random.choice([self.factions[color1]["behavior"], self.factions[color2]["behavior"]]),
            "age": 0, "merges": 0, "offspring": 0,
            "symbol": random.choice([self.factions[color1]["symbol"], self.factions[color2]["symbol"]]),
            "name": new_name,
            "tier": max(self.factions[color1]["tier"], self.factions[color2]["tier"]) + 1,
            "personality": {
                k: (self.factions[color1]["personality"][k] + self.factions[color2]["personality"][k]) / 2
                for k in ["aggression", "defense", "expansionism", "risk"]
            }
        }

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x] in (color1, color2):
                    self.grid[y][x] = new_color

        del self.factions[color1], self.factions[color2]

    def blend_colors(self, c1, c2):
        to_rgb = lambda h: tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        to_hex = lambda r, g, b: f"#{r:02x}{g:02x}{b:02x}"
        r1, g1, b1 = to_rgb(c1)
        r2, g2, b2 = to_rgb(c2)
        return to_hex((r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2)

    def trigger_disaster(self):
        event = random.choice(["plague", "quake", "flare"])
        for _ in range(200):
            x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
            if event == "plague" and self.grid[y][x]:
                self.grid[y][x] = None
            elif event == "quake":
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    self.grid[y][x], self.grid[ny][nx] = self.grid[ny][nx], self.grid[y][x]
            elif event == "flare":
                for color in list(self.factions):
                    if self.factions[color]["behavior"] == "teleporter":
                        del self.factions[color]
                        for y in range(self.grid_height):
                            for x in range(self.grid_width):
                                if self.grid[y][x] == color:
                                    self.grid[y][x] = None

    def run(self):
        self.clock = pygame.time.Clock()
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                color = self.grid[y][x]
                if color:
                    pygame.draw.rect(
                        self.screen,
                        pygame.Color(color),
                        pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                    )
        pygame.display.flip()

        threading.Thread(target=self.simulate, daemon=True).start()

        while self.running:
            self.handle_events()
            time_delta = self.clock.tick(60) / 1000.0
            self.ui_manager.update(time_delta)
            self.ui_manager.draw_ui(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


# Start the simulation
if __name__ == "__main__":
    sim = AISim()
    sim.run()
