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
from pygame_gui.core import ObjectID
import gc
import json

theme_path = "fallback_theme.json"

class AISim:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.load_complete = False  # Used to gate simulation start until load finishes

        # Fullscreen mode — gets monitor's actual resolution
        self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
        pygame.display.set_caption("AI Faction Simulator")

        # Get real resolution
        display_info = pygame.display.Info()
        screen_width, screen_height = display_info.current_w, display_info.current_h

        # Reserve space for UI
        self.progress_height = 50

        # Set target number of vertical grid cells
        target_cells_y = 500
        self.cell_size = max(2, (screen_height - self.progress_height) // target_cells_y)

        # Compute grid size to match cell size
        self.grid_height = (screen_height - self.progress_height) // self.cell_size
        self.grid_width = screen_width // self.cell_size
        self.canvas_width = self.grid_width * self.cell_size
        self.canvas_height = self.grid_height * self.cell_size

        # Resize window to match computed dimensions
        self.screen = pygame.display.set_mode(
            (self.canvas_width, self.canvas_height + self.progress_height),
            pygame.NOFRAME
        )

        self.font = pygame.font.SysFont("consolas", max(12, self.cell_size))

        # Load theme and init UI
        self.ui_manager = pygame_gui.UIManager(
            (self.canvas_width, self.canvas_height + self.progress_height),
            theme_path
        )


        self.save_button = pygame_gui.elements.UIButton(
            pygame.Rect((10, self.canvas_height + 5), (100, 30)), "Save", self.ui_manager
        )
        self.load_button = pygame_gui.elements.UIButton(
            pygame.Rect((120, self.canvas_height + 5), (100, 30)), "Load", self.ui_manager
        )
        self.new_game_button = pygame_gui.elements.UIButton(
            pygame.Rect((230, self.canvas_height + 5), (120, 30)), "New Game", self.ui_manager
        )
        self.quit_button = pygame_gui.elements.UIButton(
            pygame.Rect((360, self.canvas_height + 5), (100, 30)), "Quit", self.ui_manager
        )

        self.behaviors = [
            "aggressive", "defensive", "random", "chaotic", "teleporter", "sapper", "conqueror",
            "hoarder", "hunter", "rogue", "mirror", "corruptor", "infiltrator", "leech", "hive"
        ]

        # Placeholders until a game is started
        self.factions = {}
        self.grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.claim_age = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.last_owner = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.overwrite_cooldown = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.biomes = {"forest": set(), "lava": set(), "oasis": set()}
        self.experimental_zones = set()
        self.last_world_event = 0
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
        
        self.factions[new_color]["relations"] = {
            c: round(random.uniform(-0.3, 0.3), 2)
            for c in self.factions if c != new_color
        }
        # Also update existing factions to include the new one
        for c in self.factions:
            if c != new_color and "relations" in self.factions[c]:
                self.factions[c]["relations"][new_color] = round(random.uniform(-0.3, 0.3), 2)


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
                elif event.ui_element == self.new_game_button:
                    self.new_game()
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

    def mutate_faction(self, color):
        """Alters the behavior and personality of an existing faction without changing its color."""
        if color not in self.factions:
            return

        mutation = random.choice(self.behaviors)
        self.factions[color]["behavior"] = mutation

        for trait in self.factions[color]["personality"]:
            self.factions[color]["personality"][trait] = round(random.uniform(0.4, 2.0), 2)

        self.factions[color]["name"] += " (Mutated)"
        print(f"🧬 {color} has mutated into a new personality: {mutation}")

    def save_simulation(self):
        Tk().withdraw()
        file_path = filedialog.asksaveasfilename(defaultextension=".cwgsave", filetypes=[("Color War Save", "*.cwgsave")])
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            # Save grid (row by row)
            f.write("[GRID]\n")
            for row in self.grid:
                f.write(",".join(cell if cell else "None" for cell in row) + "\n")

            # Save factions
            f.write("[FACTIONS]\n")
            for color, data in self.factions.items():
                f.write(f"{color}|{data.get('name','')}|{data.get('behavior','random')}|{data.get('tier',1)}|"
                        f"{data.get('symbol','?')}|{data.get('dna','')}|"
                        f"{data.get('capital', (0,0))}|{data['personality']['aggression']}|"
                        f"{data['personality']['defense']}|{data['personality']['expansionism']}|"
                        f"{data['personality']['risk']}\n")

    def load_simulation(self):
        Tk().withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("Color War Save", "*.cwgsave")])
        if not file_path or not os.path.exists(file_path):
            return

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        section = None
        grid = []
        factions = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line == "[GRID]":
                section = "grid"
                continue
            elif line == "[FACTIONS]":
                section = "factions"
                continue

            if section == "grid":
                grid.append([cell if cell != "None" else None for cell in line.split(",")])
            elif section == "factions":
                parts = line.split("|")
                if len(parts) < 11:
                    continue
                color = parts[0]
                factions[color] = {
                    "name": parts[1],
                    "behavior": parts[2],
                    "tier": int(parts[3]),
                    "symbol": parts[4],
                    "dna": parts[5],
                    "capital": eval(parts[6]),
                    "personality": {
                        "aggression": float(parts[7]),
                        "defense": float(parts[8]),
                        "expansionism": float(parts[9]),
                        "risk": float(parts[10])
                    },
                    "age": 0,
                    "merges": 0,
                    "offspring": 0,
                    "memory": [],
                    "lore": {
                        "motto": "Unknown",
                        "origin": "Unknown",
                        "victory_quote": "Victory is ours."
                    },
                    "relations": {}
                }

        self.grid = grid
        self.factions = factions

        # Resize grid if needed
        saved_height = len(self.grid)
        saved_width = len(self.grid[0]) if saved_height > 0 else 0
        if saved_height != self.grid_height or saved_width != self.grid_width:
            print("⚠️ Save grid size doesn't match current screen — resizing...")
            new_grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
            for y in range(min(saved_height, self.grid_height)):
                for x in range(min(saved_width, self.grid_width)):
                    new_grid[y][x] = self.grid[y][x]
            self.grid = new_grid

        # Add missing factions from grid
        grid_colors = {cell for row in self.grid for cell in row if cell}
        for color in grid_colors:
            if color not in self.factions:
                print(f"⚠️ Recreating missing faction: {color}")
                self.factions[color] = {
                    "behavior": "random",
                    "age": 0,
                    "merges": 0,
                    "offspring": 0,
                    "symbol": "❓",
                    "name": f"Recovered {color}",
                    "tier": 1,
                    "personality": {
                        "aggression": 1.0,
                        "defense": 1.0,
                        "expansionism": 1.0,
                        "risk": 1.0
                    },
                    "relations": {}
                }

        # Rebuild relations
        for c1 in self.factions:
            self.factions[c1].setdefault("relations", {})
            for c2 in self.factions:
                if c1 != c2 and c2 not in self.factions[c1]["relations"]:
                    self.factions[c1]["relations"][c2] = round(random.uniform(-0.3, 0.3), 2)

        # 🟢 Confirm load completed
        print("✅ Save loaded and validated.")
        self.load_complete = True  # Flag for main loop

    def trigger_world_event(self):
        event = random.choice(["Time Warp", "Forgotten Return", "Singularity", "DNA Corruption"])
        if event == "Time Warp":
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if random.random() < 0.05:
                        self.grid[y][x] = None
        elif event == "Forgotten Return":
            if len(self.factions) > 3:
                ghost = random.choice(list(self.factions.keys()))
                for _ in range(300):
                    x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
                    if self.grid[y][x] is None:
                        self.grid[y][x] = ghost
        elif event == "Singularity":
            cx, cy = self.grid_width // 2, self.grid_height // 2
            for y in range(cy - 10, cy + 10):
                for x in range(cx - 10, cx + 10):
                    if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                        self.grid[y][x] = None
        elif event == "DNA Corruption":
            for color in self.factions:
                self.factions[color]["dna"] = f"X-{random.randint(1000,9999)}"
                self.factions[color]["behavior"] = random.choice(self.behaviors)

    def ensure_faction_schema(self, color, faction):
        """Ensure all expected keys exist in a faction dict"""
        defaults = {
            "behavior": "random",
            "age": 0,
            "merges": 0,
            "offspring": 0,
            "symbol": "?",
            "name": f"Recovered {color}",
            "tier": 1,
            "capital": (0, 0),
            "archetype": "Neutral",
            "personality": {
                "aggression": 1.0,
                "defense": 1.0,
                "expansionism": 1.0,
                "risk": 1.0
            },
            "memory": [],
            "relations": {},
            "dna": f"R-{random.randint(1000,9999)}",
            "lore": {
                "motto": "Unknown origins.",
                "origin": "unknown",
                "victory_quote": "Victory is ours."
            }
        }

        for key, value in defaults.items():
            if key not in faction:
                faction[key] = value
            elif isinstance(value, dict):
                for subkey, subval in value.items():
                    faction[key].setdefault(subkey, subval)

        return faction

    def new_game(self):
        self.num_factions = 200
        self.factions = {}

        archetypes = {
            "Swarm": {"expansionism": 2.0, "aggression": 1.0, "defense": 0.5, "risk": 1.5},
            "Empire": {"expansionism": 0.7, "aggression": 0.8, "defense": 2.0, "risk": 0.6},
            "Rogue": {"expansionism": 1.2, "aggression": 1.8, "defense": 0.5, "risk": 2.0},
            "Cult": {"expansionism": 1.0, "aggression": 0.9, "defense": 1.2, "risk": 1.5},
            "Neutral": {"expansionism": 1.0, "aggression": 1.0, "defense": 1.0, "risk": 1.0}
        }

        for i in range(self.num_factions):
            color = self.random_color()
            while color in self.factions:
                color = self.random_color()
            archetype = random.choice(list(archetypes.keys()))
            personality = archetypes[archetype]
            self.factions[color] = {
                "behavior": random.choice(self.behaviors),
                "age": 0, "merges": 0, "offspring": 0,
                "symbol": random.choice(["■", "●", "▲", "◆", "✦", "✶"]),
                "name": f"Faction {i+1}",
                "tier": 1,
                "capital": (random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)),
                "archetype": archetype,
                "personality": personality.copy(),
                "memory": [],
                "relations": {},
                "dna": f"{archetype[0]}-{random.randint(1000,9999)}",
                "lore": {
                    "motto": random.choice(["No mercy.", "Evolve or die.", "Unity is strength.", "From ash we rise."]),
                    "origin": random.choice(["volcanic ruin", "frozen tower", "desert tomb", "digital void"]),
                    "victory_quote": random.choice(["We. Are. Eternal.", "Nothing can stop us.", "The world belongs to us now."])
                }
            }

        for c1 in self.factions:
            for c2 in self.factions:
                if c1 != c2:
                    self.factions[c1]["relations"][c2] = round(random.uniform(-0.3, 0.3), 2)

        self.experimental_zones = set()
        for _ in range(3):
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            self.experimental_zones.add((x, y))

        self.grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.claim_age = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.last_owner = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.overwrite_cooldown = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.populate()
        threading.Thread(target=self.simulate, daemon=True).start()

    def simulate(self):
        total_cells = self.grid_width * self.grid_height
        cycle_count = 0

        while self.running and pygame.display.get_init():
            # Count faction power
            faction_power = {}
            for row in self.grid:
                for color in row:
                    if color in self.factions:
                        faction_power[color] = faction_power.get(color, 0) + 1

            self.step(faction_power)
            self.check_victory(faction_power)

            # Auto merge chance scales with time
            if random.random() < min(0.002 + cycle_count / 200000, 0.08) and len(self.factions) >= 2:
                self.auto_merge_random_factions()

            # Random biome disaster
            if cycle_count % 100 == 0 and random.random() < 0.8:
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

            # Enhanced progressive decay
            if cycle_count % 100 == 0 and faction_power:
                dominant_color, dominant_count = max(faction_power.items(), key=lambda item: item[1])
                dominant_ratio = dominant_count / total_cells

                if dominant_ratio >= 0.5:
                    decay_strength = int(dominant_ratio * 200)  # scales up to 140 tiles
                    removed = 0
                    for _ in range(2000):
                        x = random.randint(0, self.grid_width - 1)
                        y = random.randint(0, self.grid_height - 1)
                        if self.grid[y][x] == dominant_color:
                            self.grid[y][x] = None
                            pygame.draw.rect(self.screen, pygame.Color("black"),
                                            pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))
                            removed += 1
                            if removed >= decay_strength:
                                break

                    # Mutation or rebellion
                    if dominant_color in self.factions:
                        if random.random() < 0.2:
                            if random.random() < 0.5:
                                self.mutate_faction(dominant_color)
                            else:
                                self.spawn_rebellion(dominant_color)


            if dominant_color in self.factions and 0.35 <= dominant_ratio <= 0.65:
                if 0.35 <= dominant_ratio <= 0.65:
                    if random.random() < 0.6:
                        self.spawn_rebellion(dominant_color)
                    if random.random() < 0.4:
                        self.mutate_faction(dominant_color)
                    if random.random() < 0.3:
                        removed = 0
                        for _ in range(2000):
                            x = random.randint(0, self.grid_width - 1)
                            y = random.randint(0, self.grid_height - 1)
                            if self.grid[y][x] == dominant_color:
                                self.grid[y][x] = None
                                pygame.draw.rect(self.screen, pygame.Color("black"),
                                                pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))
                                removed += 1
                            if removed >= 150:
                                break

            # Cull weakest every 1000 cycles
            if cycle_count % 1000 == 0 and len(self.factions) > 10:
                if faction_power:
                    weakest = min(faction_power.items(), key=lambda item: item[1])[0]
                    if weakest in self.factions:
                        del self.factions[weakest]
                        for y in range(self.grid_height):
                            for x in range(self.grid_width):
                                if self.grid[y][x] == weakest:
                                    self.grid[y][x] = None

            # 💀 Respawn system: if factions fall below 5, generate more
            if len(self.factions) < 5:
                for _ in range(5 - len(self.factions)):
                    new_color = self.random_color()
                    while new_color in self.factions:
                        new_color = self.random_color()

                    self.factions[new_color] = {
                        "behavior": random.choice(self.behaviors),
                        "age": 0,
                        "merges": 0,
                        "offspring": 0,
                        "symbol": random.choice(["⬢", "⬡", "⬣", "✴"]),
                        "name": f"Regen {len(self.factions) + 1}",
                        "tier": 1,
                        "personality": {
                            "aggression": round(random.uniform(0.5, 1.5), 2),
                            "defense": round(random.uniform(0.5, 1.5), 2),
                            "expansionism": round(random.uniform(0.5, 1.5), 2),
                            "risk": round(random.uniform(0.5, 1.5), 2)
                        },
                        "relations": {}
                    }

                    # Place on the map
                    placed = 0
                    while placed < 30:
                        x = random.randint(0, self.grid_width - 1)
                        y = random.randint(0, self.grid_height - 1)
                        if self.grid[y][x] is None:
                            self.grid[y][x] = new_color
                            pygame.draw.rect(self.screen, pygame.Color(new_color),
                                            pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))
                            placed += 1

                # 💬 Log regeneration
                print(f"🧬 Factions regenerated: {len(self.factions)} alive")

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
                
            # Trigger rare world events every 500 ticks
            if cycle_count - self.last_world_event >= 500:
                self.last_world_event = cycle_count
                self.trigger_world_event()

            cycle_count += 1
            time.sleep(0.01)

    def step(self, faction_power):
        MAX_FACTIONS = 150
        total_cells = max(1, self.grid_width * self.grid_height)
        new_grid = [row[:] for row in self.grid]

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
                        if "relations" in self.factions[color] and target in self.factions[color]["relations"]:
                            relation = self.factions[color]["relations"][target]
                        else:
                            relation = 0
                        diplomatic_modifier = 1.0 - max(0, relation)  # reduces attack chance if they're friendly
                        if power > faction_power.get(target, 0) or random.random() < attack_chance * diplomatic_modifier:
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
        self.factions[new_color]["relations"] = {}
        for c in self.factions:
            if c != new_color:
                self.factions[new_color]["relations"][c] = round(random.uniform(-0.3, 0.3), 2)
                if "relations" in self.factions[c]:
                    self.factions[c]["relations"][new_color] = round(random.uniform(-0.3, 0.3), 2)


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
        event = random.choice(["plague", "quake", "flare", "volcano", "storm", "wipeout"])

        if event == "plague":
            for _ in range(200):
                x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
                if self.grid[y][x]:
                    self.grid[y][x] = None

        elif event == "quake":
            for _ in range(200):
                x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
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

        elif event == "volcano":
            # Hit large chunks from dominant faction
            power_map = {color: 0 for color in self.factions}
            for row in self.grid:
                for cell in row:
                    if cell in power_map:
                        power_map[cell] += 1
            if power_map:
                target = max(power_map.items(), key=lambda x: x[1])[0]
                for _ in range(1000):
                    x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
                    if self.grid[y][x] == target:
                        self.grid[y][x] = None
                        pygame.draw.rect(self.screen, pygame.Color("black"),
                                        pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))

        elif event == "storm":
            for color in list(self.factions):
                eroded = 0
                for _ in range(300):
                    x, y = random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1)
                    if self.grid[y][x] == color:
                        self.grid[y][x] = None
                        eroded += 1
                        if eroded >= 80:
                            break

        elif event == "wipeout" and len(self.factions) > 3:
            # Extremely rare total faction wipe
            target = random.choice(list(self.factions.keys()))
            del self.factions[target]
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if self.grid[y][x] == target:
                        self.grid[y][x] = None

        print(f"🌪 Disaster triggered: {event}")

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

        simulation_started = False

        while self.running:
            self.handle_events()
            time_delta = self.clock.tick(60) / 1000.0
            self.ui_manager.update(time_delta)
            self.ui_manager.draw_ui(self.screen)
            pygame.display.flip()

            # Only start simulation after load is complete or if it's a fresh game
            if not simulation_started and (self.load_complete or not self.grid):
                threading.Thread(target=self.simulate, daemon=True).start()
                simulation_started = True


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
