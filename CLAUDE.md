# Shadowcrypt — AI Dungeon Master Game

A terminal-based roguelike dungeon crawler where Claude acts as the Dungeon Master.

## Project Structure

- `scripts/render.py` — ASCII renderer, reads `data/game_state.json` and prints the board with ANSI colors and fog of war
- `data/game_state.json` — Current game state (map, player, entities)
- `data/game_log.json` — Append-only action log for Claude to read and adapt
- `data/dm_summary.md` — Claude's running DM summary (updated every ~5 turns)
- `.claude/skills/shadowcrypt/SKILL.md` — Skill definition with game loop

## How to Play

Run `/shadowcrypt` in Claude Code to start a game session.

## Game Rules

- **Map:** 24×24 grid, fog of war (5-tile Chebyshev radius)
- **Goal:** Reach the exit on floor 3
- **Player stats:** HP (20), ATK (3), DEF (1), Potions (2)
- **Combat:** Auto-resolved. Player deals `ATK - monster.DEF`, monster deals `monster.ATK - player.DEF`. Min 1 damage per hit. Alternating hits until one dies.
- **Leveling:** Gain XP from kills (XP = monster max HP). Every 10 XP = level up, player chooses +3 HP, +1 ATK, or +1 DEF.
- **Potions:** Heal 8 HP (capped at max_hp).

## Map Symbols

```
@ = Player    # = Wall     . = Floor    M = Monster
T = Trap      $ = Treasure P = Potion   > = Stairs
? = Event     ~ = Water    + = Door
```

## Renderer

```bash
python3 scripts/render.py
# or with explicit path:
python3 scripts/render.py data/game_state.json
```
