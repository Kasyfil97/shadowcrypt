#!/usr/bin/env python3
"""Shadowcrypt Curses TUI — one turn per invocation.

Renders the dungeon, waits for one keypress, processes the action,
saves state + last_action.json, and exits.
"""

import curses
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
STATE_PATH = os.path.join(DATA_DIR, "game_state.json")
LOG_PATH = os.path.join(DATA_DIR, "game_log.json")
ACTION_PATH = os.path.join(DATA_DIR, "last_action.json")

FOG_RADIUS = 5

# --- Color pair IDs ---
C_DEFAULT = 0
C_PLAYER = 1    # @ green
C_WALL = 2      # # dim white
C_FLOOR = 3     # . dim
C_MONSTER = 4   # M red
C_TRAP = 5      # T yellow
C_TREASURE = 6  # $ bright yellow
C_POTION = 7    # P magenta
C_STAIRS = 8    # > cyan
C_EVENT = 9     # ? blue
C_WATER = 10    # ~ blue
C_DOOR = 11     # + yellow
C_FOG = 12      # dim revealed tiles
C_HP_GREEN = 13
C_HP_YELLOW = 14
C_HP_RED = 15
C_HEADER = 16
C_STAT_ATK = 17
C_STAT_DEF = 18
C_STAT_POT = 19
C_STAT_LV = 20
C_STAT_XP = 21
C_MSG = 22
C_LEGEND = 23

TILE_COLOR = {
    "@": C_PLAYER,
    "#": C_WALL,
    ".": C_FLOOR,
    "M": C_MONSTER,
    "T": C_TRAP,
    "$": C_TREASURE,
    "P": C_POTION,
    ">": C_STAIRS,
    "?": C_EVENT,
    "~": C_WATER,
    "+": C_DOOR,
}


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_PLAYER, curses.COLOR_GREEN, -1)
    curses.init_pair(C_WALL, curses.COLOR_WHITE, -1)
    curses.init_pair(C_FLOOR, curses.COLOR_WHITE, -1)
    curses.init_pair(C_MONSTER, curses.COLOR_RED, -1)
    curses.init_pair(C_TRAP, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_TREASURE, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_POTION, curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_STAIRS, curses.COLOR_CYAN, -1)
    curses.init_pair(C_EVENT, curses.COLOR_BLUE, -1)
    curses.init_pair(C_WATER, curses.COLOR_BLUE, -1)
    curses.init_pair(C_DOOR, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_FOG, curses.COLOR_WHITE, -1)
    curses.init_pair(C_HP_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(C_HP_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_HP_RED, curses.COLOR_RED, -1)
    curses.init_pair(C_HEADER, curses.COLOR_CYAN, -1)
    curses.init_pair(C_STAT_ATK, curses.COLOR_RED, -1)
    curses.init_pair(C_STAT_DEF, curses.COLOR_BLUE, -1)
    curses.init_pair(C_STAT_POT, curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_STAT_LV, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_STAT_XP, curses.COLOR_CYAN, -1)
    curses.init_pair(C_MSG, curses.COLOR_WHITE, -1)
    curses.init_pair(C_LEGEND, curses.COLOR_WHITE, -1)


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def chebyshev(x1, y1, x2, y2):
    return max(abs(x1 - x2), abs(y1 - y2))


def build_entity_map(entities):
    em = {}
    for e in entities:
        ex, ey = e["x"], e["y"]
        t = e.get("type", "")
        sym = {"monster": "M", "M": "M", "trap": "T", "T": "T",
               "treasure": "$", "$": "$", "potion": "P", "P": "P",
               "stairs": ">", ">": ">", "event": "?", "?": "?"}.get(t, "?")
        em[(ex, ey)] = sym
    return em


def draw_map(win, state, entity_map, start_y, start_x):
    game_map = state["map"]
    player = state["player"]
    revealed = state.get("revealed", [])
    px, py = player["x"], player["y"]
    rows = len(game_map)
    cols = len(game_map[0]) if rows > 0 else 0

    # Top border
    try:
        win.addstr(start_y, start_x, "+" + "-" * (cols * 2) + "+",
                   curses.color_pair(C_WALL) | curses.A_DIM)
    except curses.error:
        pass

    for y in range(rows):
        try:
            win.addstr(start_y + 1 + y, start_x, "|",
                       curses.color_pair(C_WALL) | curses.A_DIM)
        except curses.error:
            pass
        for x in range(cols):
            dist = chebyshev(px, py, x, y)
            is_near = dist <= FOG_RADIUS
            was_revealed = (revealed[y][x]
                            if revealed and y < len(revealed) and x < len(revealed[y])
                            else False)
            col = start_x + 1 + x * 2
            row = start_y + 1 + y

            if x == px and y == py:
                try:
                    win.addstr(row, col, "@ ",
                               curses.color_pair(C_PLAYER) | curses.A_BOLD)
                except curses.error:
                    pass
            elif is_near:
                char = entity_map.get((x, y), game_map[y][x])
                cpair = TILE_COLOR.get(char, C_FLOOR)
                attr = curses.color_pair(cpair)
                if char in ("@", "M", "$", "P", ">", "?", "T"):
                    attr |= curses.A_BOLD
                if char in (".", "#"):
                    attr |= curses.A_DIM
                try:
                    win.addstr(row, col, char + " ", attr)
                except curses.error:
                    pass
            elif was_revealed:
                char = game_map[y][x]
                try:
                    win.addstr(row, col, char + " ",
                               curses.color_pair(C_FOG) | curses.A_DIM)
                except curses.error:
                    pass
            else:
                try:
                    win.addstr(row, col, "  ")
                except curses.error:
                    pass

        try:
            win.addstr(start_y + 1 + y, start_x + 1 + cols * 2, "|",
                       curses.color_pair(C_WALL) | curses.A_DIM)
        except curses.error:
            pass

    # Bottom border
    try:
        win.addstr(start_y + 1 + rows, start_x, "+" + "-" * (cols * 2) + "+",
                   curses.color_pair(C_WALL) | curses.A_DIM)
    except curses.error:
        pass


def draw_header(win, state, row, col):
    floor_num = state.get("floor", 1)
    turn = state.get("turn", 0)
    title = " SHADOWCRYPT "
    info = f" Floor {floor_num} | Turn {turn} "
    try:
        win.addstr(row, col, title,
                   curses.color_pair(C_HEADER) | curses.A_BOLD)
        win.addstr(row, col + len(title) + 1, info,
                   curses.color_pair(C_HEADER) | curses.A_DIM)
    except curses.error:
        pass


def draw_stats(win, state, row, col):
    p = state["player"]
    hp, max_hp = p.get("hp", 0), p.get("max_hp", 20)
    atk = p.get("atk", 3)
    defense = p.get("def", 1)
    potions = p.get("potions", 0)
    level = p.get("level", 1)
    xp = p.get("xp", 0)

    # HP bar
    bar_w = 20
    filled = int((hp / max_hp) * bar_w) if max_hp > 0 else 0
    filled = max(0, min(filled, bar_w))
    ratio = hp / max_hp if max_hp > 0 else 0
    if ratio > 0.6:
        hp_color = C_HP_GREEN
    elif ratio > 0.3:
        hp_color = C_HP_YELLOW
    else:
        hp_color = C_HP_RED

    try:
        win.addstr(row, col, "HP ", curses.color_pair(C_MSG) | curses.A_BOLD)
        win.addstr(row, col + 3, "#" * filled,
                   curses.color_pair(hp_color) | curses.A_BOLD)
        win.addstr(row, col + 3 + filled, "." * (bar_w - filled),
                   curses.color_pair(C_MSG) | curses.A_DIM)
        hp_text = f" {hp}/{max_hp}"
        win.addstr(row, col + 3 + bar_w, hp_text,
                   curses.color_pair(C_MSG) | curses.A_BOLD)

        stat_col = col + 3 + bar_w + len(hp_text) + 2
        win.addstr(row, stat_col, "ATK ",
                   curses.color_pair(C_STAT_ATK) | curses.A_BOLD)
        win.addstr(row, stat_col + 4, str(atk),
                   curses.color_pair(C_MSG))
        stat_col += 4 + len(str(atk)) + 2

        win.addstr(row, stat_col, "DEF ",
                   curses.color_pair(C_STAT_DEF) | curses.A_BOLD)
        win.addstr(row, stat_col + 4, str(defense),
                   curses.color_pair(C_MSG))
        stat_col += 4 + len(str(defense)) + 2

        win.addstr(row, stat_col, "POT ",
                   curses.color_pair(C_STAT_POT) | curses.A_BOLD)
        win.addstr(row, stat_col + 4, str(potions),
                   curses.color_pair(C_MSG))
        stat_col += 4 + len(str(potions)) + 2

        win.addstr(row, stat_col, "LV ",
                   curses.color_pair(C_STAT_LV) | curses.A_BOLD)
        win.addstr(row, stat_col + 3, str(level),
                   curses.color_pair(C_MSG))
        stat_col += 3 + len(str(level)) + 2

        win.addstr(row, stat_col, "XP ",
                   curses.color_pair(C_STAT_XP) | curses.A_BOLD)
        win.addstr(row, stat_col + 3, str(xp),
                   curses.color_pair(C_MSG))
    except curses.error:
        pass


def draw_messages(win, state, row, col, max_width):
    messages = state.get("messages", [])
    last5 = messages[-5:]
    try:
        win.addstr(row, col, "-" * min(50, max_width),
                   curses.color_pair(C_MSG) | curses.A_DIM)
        for i, msg in enumerate(last5):
            text = msg[:max_width - 2] if len(msg) > max_width - 2 else msg
            win.addstr(row + 1 + i, col, text,
                       curses.color_pair(C_MSG) | curses.A_DIM)
        win.addstr(row + 1 + len(last5), col, "-" * min(50, max_width),
                   curses.color_pair(C_MSG) | curses.A_DIM)
    except curses.error:
        pass


def draw_legend(win, row, col):
    legend = [
        ("Controls", None),
        ("Arrow/WASD", "Move"),
        ("p", "Use Potion"),
        ("w", "Wait"),
        ("q", "Quit"),
        ("", ""),
        ("Legend", None),
        ("@", "Player", C_PLAYER),
        ("#", "Wall", C_WALL),
        (".", "Floor", C_FLOOR),
        ("M", "Monster", C_MONSTER),
        ("T", "Trap", C_TRAP),
        ("$", "Treasure", C_TREASURE),
        ("P", "Potion", C_POTION),
        (">", "Stairs", C_STAIRS),
        ("?", "Event", C_EVENT),
        ("~", "Water", C_WATER),
        ("+", "Door", C_DOOR),
    ]
    for i, entry in enumerate(legend):
        try:
            if len(entry) == 2:
                key, desc = entry
                if desc is None:
                    # Section header
                    win.addstr(row + i, col, f"[ {key} ]",
                               curses.color_pair(C_HEADER) | curses.A_BOLD)
                elif key == "":
                    pass  # blank line
                else:
                    win.addstr(row + i, col, f" {key:>11s}",
                               curses.color_pair(C_MSG) | curses.A_BOLD)
                    win.addstr(row + i, col + 12, f" {desc}",
                               curses.color_pair(C_MSG) | curses.A_DIM)
            else:
                sym, desc, cpair = entry
                win.addstr(row + i, col, f"  {sym}",
                           curses.color_pair(cpair) | curses.A_BOLD)
                win.addstr(row + i, col + 4, f" {desc}",
                           curses.color_pair(C_MSG) | curses.A_DIM)
        except curses.error:
            pass


# --- Action processing ---

def resolve_combat(player, monster):
    """Auto-resolve combat. Returns (won: bool, messages: list, player_hp_after)."""
    msgs = []
    p_hp = player["hp"]
    m_hp = monster["hp"]
    p_atk = player.get("atk", 3)
    p_def = player.get("def", 1)
    m_atk = monster.get("atk", 1)
    m_def = monster.get("def", 0)
    m_name = monster.get("name", "Monster")

    while p_hp > 0 and m_hp > 0:
        # Player hits
        dmg = max(1, p_atk - m_def)
        m_hp -= dmg
        if m_hp <= 0:
            msgs.append(f"You strike the {m_name} for {dmg} damage — it falls!")
            break
        # Monster hits
        dmg_m = max(1, m_atk - p_def)
        p_hp -= dmg_m
        msgs.append(f"The {m_name} hits you for {dmg_m} damage!")
        if p_hp <= 0:
            msgs.append("You collapse to the ground...")
            break

    won = p_hp > 0
    return won, msgs, max(0, p_hp)


def process_action(state, action):
    """Process one player action. Returns (result_info: dict, updated_state)."""
    player = state["player"]
    game_map = state["map"]
    entities = state.get("entities", [])
    revealed = state.get("revealed", [])
    messages = state.get("messages", [])
    turn = state.get("turn", 0)
    floor_num = state.get("floor", 1)

    px, py = player["x"], player["y"]
    result = {
        "action": action,
        "result": "nothing",
        "combat": None,
        "player_hp": player["hp"],
        "player_pos": [px, py],
        "quit": False,
        "died": False,
        "won": False,
        "stairs": False,
    }

    if action == "quit":
        result["quit"] = True
        result["result"] = "quit"
        return result, state

    if action == "wait":
        result["result"] = "waited"
        messages.append("You wait and listen...")
        turn += 1
        state["turn"] = turn
        state["messages"] = messages[-5:]
        return result, state

    if action == "potion":
        if player.get("potions", 0) > 0 and player["hp"] < player["max_hp"]:
            heal = min(8, player["max_hp"] - player["hp"])
            player["hp"] += heal
            player["potions"] -= 1
            messages.append(f"You drink a potion and heal {heal} HP.")
            result["result"] = "used_potion"
            result["player_hp"] = player["hp"]
        else:
            messages.append("No potions to use or already at full HP.")
            result["result"] = "potion_failed"
        turn += 1
        state["turn"] = turn
        state["player"] = player
        state["messages"] = messages[-5:]
        return result, state

    # Movement
    dx, dy = 0, 0
    if action == "move_up":
        dy = -1
    elif action == "move_down":
        dy = 1
    elif action == "move_left":
        dx = -1
    elif action == "move_right":
        dx = 1
    else:
        result["result"] = "unknown"
        return result, state

    nx, ny = px + dx, py + dy
    rows = len(game_map)
    cols = len(game_map[0]) if rows > 0 else 0

    # Bounds check
    if nx < 0 or nx >= cols or ny < 0 or ny >= rows:
        messages.append("You bump into the edge of the world.")
        result["result"] = "blocked"
        state["messages"] = messages[-5:]
        return result, state

    tile = game_map[ny][nx]

    # Wall check
    if tile == "#":
        messages.append("You walk into a wall. It doesn't budge.")
        result["result"] = "blocked"
        state["messages"] = messages[-5:]
        return result, state

    # Move the player
    player["x"] = nx
    player["y"] = ny
    result["player_pos"] = [nx, ny]
    result["result"] = "moved"
    extra_turn = 0

    # Water slows
    if tile == "~":
        extra_turn = 1
        messages.append("You wade through the water... it slows you down.")

    # Update revealed
    for ry in range(rows):
        for rx in range(cols):
            if chebyshev(nx, ny, rx, ry) <= FOG_RADIUS:
                if ry < len(revealed) and rx < len(revealed[ry]):
                    revealed[ry][rx] = True

    # Check entity interactions at new position
    to_remove = []
    for i, e in enumerate(entities):
        if e["x"] != nx or e["y"] != ny:
            continue
        etype = e.get("type", "")

        if etype in ("monster", "M"):
            won, combat_msgs, new_hp = resolve_combat(player, e)
            messages.extend(combat_msgs)
            player["hp"] = new_hp
            result["player_hp"] = new_hp
            if won:
                xp_gain = e.get("max_hp", e.get("hp", 3))
                player["xp"] = player.get("xp", 0) + xp_gain
                result["combat"] = {
                    "monster": e.get("name", "Monster"),
                    "won": True,
                    "xp_gained": xp_gain
                }
                to_remove.append(i)
                # Level up check
                needed = player.get("level", 1) * 10
                if player["xp"] >= needed:
                    player["level"] = player.get("level", 1) + 1
                    messages.append(f"LEVEL UP! You are now level {player['level']}!")
                    # Auto-choose +3 HP for TUI (DM can override)
                    player["max_hp"] += 3
                    player["hp"] = min(player["hp"] + 3, player["max_hp"])
                    messages.append("You gain +3 Max HP.")
            else:
                result["combat"] = {
                    "monster": e.get("name", "Monster"),
                    "won": False
                }
                result["died"] = True
            break

        elif etype in ("trap", "T"):
            dmg = e.get("damage", 3)
            player["hp"] -= dmg
            messages.append(f"You triggered a trap! Take {dmg} damage!")
            result["player_hp"] = player["hp"]
            to_remove.append(i)
            if player["hp"] <= 0:
                result["died"] = True
                messages.append("The trap was fatal...")

        elif etype in ("treasure", "$"):
            # Random-ish reward based on turn parity
            reward_type = turn % 4
            if reward_type == 0:
                player["atk"] += 1
                messages.append("Treasure! You find a sharp blade. ATK +1!")
            elif reward_type == 1:
                player["def"] += 1
                messages.append("Treasure! You find a sturdy shield. DEF +1!")
            elif reward_type == 2:
                player["potions"] = player.get("potions", 0) + 1
                messages.append("Treasure! You find a potion!")
            else:
                heal = min(5, player["max_hp"] - player["hp"])
                player["hp"] += heal
                messages.append(f"Treasure! A healing gem restores {heal} HP!")
            to_remove.append(i)

        elif etype in ("potion", "P"):
            player["potions"] = player.get("potions", 0) + 1
            messages.append("You pick up a potion!")
            to_remove.append(i)

        elif etype in ("stairs", ">"):
            if floor_num >= 3:
                result["won"] = True
                messages.append("You ascend from the crypt! VICTORY!")
            else:
                result["stairs"] = True
                messages.append(f"You descend to floor {floor_num + 1}...")
                state["floor"] = floor_num + 1
            to_remove.append(i)

        elif etype in ("event", "?"):
            messages.append("You discover a mysterious event!")
            to_remove.append(i)

    # Remove consumed entities (reverse order to preserve indices)
    for i in sorted(to_remove, reverse=True):
        entities.pop(i)

    turn += 1 + extra_turn
    result["player_hp"] = player["hp"]

    state["turn"] = turn
    state["player"] = player
    state["entities"] = entities
    state["revealed"] = revealed
    state["messages"] = messages[-5:]

    return result, state


def get_action(key):
    """Map keypress to action string."""
    if key == curses.KEY_UP or key == ord('w') or key == ord('W'):
        # Distinguish 'w' for WASD up vs 'w' for wait:
        # Use 'w' as wait, WASD uses capital or we use different mapping
        # Actually plan says WASD for move, 'w' for wait - conflict.
        # Resolve: arrow keys + WASD for movement. Lowercase 'w' = up (WASD).
        # Separate wait key could be space or period. But plan says 'w' for wait.
        # Let's use: WASD = move, '.' or space = wait, to avoid conflict.
        # BUT plan explicitly says w=wait. So WASD minus W: use ASD + arrow keys.
        # Simplest: arrows for move, wasd for move, '.' for wait if conflict.
        # Let me re-read plan: "arrow keys/WASD (move), p (potion), w (wait), q (quit)"
        # This is contradictory (w is both WASD-up and wait). I'll make W (capital) = up,
        # w (lowercase) = wait. But curses doesn't distinguish well.
        # Resolution: Use only arrow keys for movement, w=wait as plan says.
        pass
    return None


def main(stdscr):
    curses.curs_set(0)
    stdscr.timeout(-1)  # blocking
    stdscr.keypad(True)
    init_colors()

    if not os.path.exists(STATE_PATH):
        stdscr.addstr(0, 0, f"Error: {STATE_PATH} not found. Run /shadowcrypt first.")
        stdscr.getch()
        return

    state = load_json(STATE_PATH)
    entity_map = build_entity_map(state.get("entities", []))

    # --- Draw everything ---
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    # Header row 0
    draw_header(stdscr, state, 0, 2)

    # Map starting at row 2
    map_start_y = 2
    map_start_x = 2
    draw_map(stdscr, state, entity_map, map_start_y, map_start_x)

    # Legend on the right side
    game_map = state["map"]
    rows = len(game_map)
    cols = len(game_map[0]) if rows > 0 else 0
    legend_x = map_start_x + 1 + cols * 2 + 3
    if legend_x + 20 < max_x:
        draw_legend(stdscr, map_start_y, legend_x)

    # Stats bar below map
    stats_y = map_start_y + rows + 3
    draw_stats(stdscr, state, stats_y, 2)

    # Messages below stats
    msg_y = stats_y + 2
    draw_messages(stdscr, state, msg_y, 2, min(60, max_x - 4))

    # Prompt at bottom
    prompt_y = msg_y + 8
    if prompt_y < max_y - 1:
        try:
            stdscr.addstr(prompt_y, 2, "Your move: ",
                          curses.color_pair(C_HEADER) | curses.A_BOLD)
            stdscr.addstr(prompt_y, 13,
                          "Arrows=Move  p=Potion  w=Wait  q=Quit",
                          curses.color_pair(C_MSG) | curses.A_DIM)
        except curses.error:
            pass

    stdscr.refresh()

    # --- Wait for one keypress ---
    action = None
    while action is None:
        key = stdscr.getch()
        if key == curses.KEY_UP:
            action = "move_up"
        elif key == curses.KEY_DOWN:
            action = "move_down"
        elif key == curses.KEY_LEFT:
            action = "move_left"
        elif key == curses.KEY_RIGHT:
            action = "move_right"
        elif key == ord('a') or key == ord('A'):
            action = "move_left"
        elif key == ord('d') or key == ord('D'):
            action = "move_right"
        elif key == ord('s') or key == ord('S'):
            action = "move_down"
        elif key == ord('p') or key == ord('P'):
            action = "potion"
        elif key == ord('w') or key == ord('W'):
            action = "wait"
        elif key == ord('q') or key == ord('Q'):
            action = "quit"
        # Ignore unrecognized keys

    # --- Process action ---
    result, state = process_action(state, action)

    # --- Save state ---
    save_json(STATE_PATH, state)
    save_json(ACTION_PATH, result)

    # --- Append to game log ---
    if os.path.exists(LOG_PATH):
        log = load_json(LOG_PATH)
    else:
        log = {"session_id": "tui", "turns": []}

    log_entry = {
        "turn": state.get("turn", 0),
        "player_action": action,
        "player_pos": result["player_pos"],
        "player_hp": result["player_hp"],
        "result": result["result"],
        "dm_action": "",
        "dm_narration": ""
    }
    log["turns"].append(log_entry)
    save_json(LOG_PATH, log)

    # --- Brief flash of result before exit ---
    if result.get("died"):
        try:
            stdscr.addstr(prompt_y, 2, "YOU DIED! ",
                          curses.color_pair(C_HP_RED) | curses.A_BOLD)
            stdscr.addstr(prompt_y, 12, "Press any key to exit...",
                          curses.color_pair(C_MSG))
            stdscr.refresh()
            stdscr.getch()
        except curses.error:
            pass
    elif result.get("won"):
        try:
            stdscr.addstr(prompt_y, 2, "VICTORY! ",
                          curses.color_pair(C_HP_GREEN) | curses.A_BOLD)
            stdscr.addstr(prompt_y, 11, "You escaped the Shadowcrypt! Press any key...",
                          curses.color_pair(C_MSG))
            stdscr.refresh()
            stdscr.getch()
        except curses.error:
            pass


if __name__ == "__main__":
    curses.wrapper(main)
