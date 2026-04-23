#!/usr/bin/env python3
"""Shadowcrypt ASCII Dungeon Renderer — reads game_state.json and prints the board."""

import json
import sys
import os

# ANSI color codes
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    # Bright
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_BLUE = "\033[44m"

# Tile color mapping
TILE_COLORS = {
    "@": f"{C.BOLD}{C.BRIGHT_GREEN}",
    "#": f"{C.DIM}{C.WHITE}",
    ".": f"{C.DIM}{C.WHITE}",
    "M": f"{C.BOLD}{C.BRIGHT_RED}",
    "T": f"{C.BOLD}{C.YELLOW}",
    "$": f"{C.BOLD}{C.BRIGHT_YELLOW}",
    "P": f"{C.BOLD}{C.BRIGHT_MAGENTA}",
    ">": f"{C.BOLD}{C.BRIGHT_CYAN}",
    "?": f"{C.BOLD}{C.BRIGHT_BLUE}",
    "~": f"{C.BLUE}",
    "+": f"{C.YELLOW}",
    " ": "",
}

FOG_RADIUS = 5


def load_state(path):
    with open(path, "r") as f:
        return json.load(f)


def distance(x1, y1, x2, y2):
    return max(abs(x1 - x2), abs(y1 - y2))  # Chebyshev distance


def render_tile(char, visible):
    if not visible:
        return f"{C.DIM}{C.BLACK}·{C.RESET}"
    color = TILE_COLORS.get(char, C.WHITE)
    return f"{color}{char}{C.RESET}"


def hp_bar(current, maximum, width=20):
    filled = int((current / maximum) * width) if maximum > 0 else 0
    filled = max(0, min(filled, width))
    empty = width - filled
    ratio = current / maximum if maximum > 0 else 0
    if ratio > 0.6:
        color = C.BRIGHT_GREEN
    elif ratio > 0.3:
        color = C.BRIGHT_YELLOW
    else:
        color = C.BRIGHT_RED
    return f"{color}{'█' * filled}{C.DIM}{'░' * empty}{C.RESET}"


def render(state):
    game_map = state["map"]
    player = state["player"]
    entities = state.get("entities", [])
    revealed = state.get("revealed", [])
    messages = state.get("messages", [])
    floor_num = state.get("floor", 1)
    turn = state.get("turn", 0)

    rows = len(game_map)
    cols = len(game_map[0]) if rows > 0 else 0
    px, py = player["x"], player["y"]

    # Build entity overlay
    entity_map = {}
    for e in entities:
        ex, ey = e["x"], e["y"]
        t = e.get("type", "")
        if t == "monster":
            entity_map[(ex, ey)] = "M"
        elif t == "trap":
            entity_map[(ex, ey)] = "T"
        elif t == "treasure":
            entity_map[(ex, ey)] = "$"
        elif t == "potion":
            entity_map[(ex, ey)] = "P"
        elif t == "stairs":
            entity_map[(ex, ey)] = ">"
        elif t == "event":
            entity_map[(ex, ey)] = "?"

    # Header
    print()
    print(f"  {C.BOLD}{C.BRIGHT_CYAN}╔══════════════════════════════════════════════════╗{C.RESET}")
    print(f"  {C.BOLD}{C.BRIGHT_CYAN}║{C.RESET}  {C.BOLD}{C.BRIGHT_WHITE}⚔  S H A D O W C R Y P T{C.RESET}  —  {C.DIM}Floor {floor_num} · Turn {turn}{C.RESET}  {C.BOLD}{C.BRIGHT_CYAN}║{C.RESET}")
    print(f"  {C.BOLD}{C.BRIGHT_CYAN}╚══════════════════════════════════════════════════╝{C.RESET}")
    print()

    # Render map
    print(f"  {C.DIM}┌{'─' * (cols * 2)}┐{C.RESET}")
    for y in range(rows):
        row_str = f"  {C.DIM}│{C.RESET}"
        for x in range(cols):
            # Check visibility
            dist = distance(px, py, x, y)
            is_near = dist <= FOG_RADIUS
            was_revealed = revealed[y][x] if revealed and y < len(revealed) and x < len(revealed[y]) else False
            visible = is_near

            if x == px and y == py:
                row_str += f"{C.BOLD}{C.BRIGHT_GREEN}@{C.RESET} "
            elif visible:
                char = entity_map.get((x, y), game_map[y][x])
                row_str += f"{render_tile(char, True)} "
            elif was_revealed:
                char = game_map[y][x]
                row_str += f"{C.DIM}{C.BLACK}{char}{C.RESET} "
            else:
                row_str += f"{C.DIM}{C.BLACK} {C.RESET} "
        row_str += f"{C.DIM}│{C.RESET}"
        print(row_str)
    print(f"  {C.DIM}└{'─' * (cols * 2)}┘{C.RESET}")

    # Stats bar
    hp = player.get("hp", 0)
    max_hp = player.get("max_hp", 20)
    atk = player.get("atk", 3)
    defense = player.get("def", 1)
    potions = player.get("potions", 0)
    xp = player.get("xp", 0)
    level = player.get("level", 1)

    print()
    print(f"  {C.BOLD}HP{C.RESET} {hp_bar(hp, max_hp)} {C.BOLD}{hp}/{max_hp}{C.RESET}    "
          f"{C.BOLD}{C.BRIGHT_RED}ATK{C.RESET} {atk}    "
          f"{C.BOLD}{C.BRIGHT_BLUE}DEF{C.RESET} {defense}    "
          f"{C.BOLD}{C.BRIGHT_MAGENTA}Potions{C.RESET} {potions}    "
          f"{C.BOLD}{C.BRIGHT_YELLOW}LV{C.RESET} {level}    "
          f"{C.BOLD}{C.BRIGHT_CYAN}XP{C.RESET} {xp}")
    print()

    # Messages
    if messages:
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        for msg in messages[-5:]:
            print(f"  {C.DIM}{C.BRIGHT_WHITE}{msg}{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
    print()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    state_path = os.path.join(script_dir, "..", "data", "game_state.json")

    if len(sys.argv) > 1:
        state_path = sys.argv[1]

    if not os.path.exists(state_path):
        print(f"{C.BRIGHT_RED}Error: game_state.json not found at {state_path}{C.RESET}")
        sys.exit(1)

    state = load_state(state_path)
    render(state)


if __name__ == "__main__":
    main()
