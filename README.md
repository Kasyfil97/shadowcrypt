# Shadowcrypt

A terminal-based roguelike dungeon crawler where **Claude is your Dungeon Master** — dynamically generating rooms, spawning monsters, placing traps, and narrating your adventure. Every session is unique.

## Getting Started

```bash
cd /Users/kasyfilalbar/project/shadowcrypt
```

Then type `/shadowcrypt` in Claude Code to start a game.

Claude will generate the dungeon, render the ASCII map, and begin the game loop.

---

## How to Play

### Your Goal
Descend through **3 floors** of the crypt and reach the exit (`>`). Don't die.

### Controls
Each turn you'll be presented with options:

| Option | Action |
|--------|--------|
| ⬆️ Move Up | Move north |
| ⬇️ Move Down | Move south |
| ⬅️ Move Left | Move west |
| ➡️ Move Right | Move east |
| 🧪 Use Potion | Heal 8 HP (only shown when you have potions and aren't full HP) |
| ⏳ Wait | Skip your turn |

### The Map

```
@ = You         # = Wall        . = Floor
M = Monster     T = Trap        $ = Treasure
P = Potion      > = Stairs      ? = Mystery Event
~ = Water       + = Door
```

Fog of war hides tiles more than **5 steps away**. Previously visited tiles appear dimmed.

### Stats

| Stat | Starting Value | Description |
|------|---------------|-------------|
| HP | 20 | Hit points — reach 0 and you die |
| ATK | 3 | Attack power |
| DEF | 1 | Reduces incoming damage |
| Potions | 2 | Heals 8 HP each |
| XP | 0 | Gained by killing monsters |
| Level | 1 | Increases as you earn XP |

### Combat

Combat is **automatic** — when you step onto a monster's tile, the fight resolves instantly:

- You deal: `max(1, ATK - monster.DEF)` damage per hit
- Monster deals: `max(1, monster.ATK - DEF)` damage per hit
- Hits alternate until one side reaches 0 HP

### Leveling Up

Every **10 XP per level** triggers a level-up. You choose one upgrade:

- **+3 Max HP** (and immediately heal 3)
- **+1 ATK**
- **+1 DEF**

### Monsters by Floor

| Floor | Monsters |
|-------|----------|
| 1 | Rat (HP:3, ATK:1), Bat (HP:4, ATK:2), Slime (HP:5, ATK:1, DEF:1) |
| 2 | Skeleton (HP:6, ATK:3, DEF:1), Spider (HP:5, ATK:4), Ghost (HP:8, ATK:3) |
| 3 | Shadow (HP:10, ATK:5, DEF:1), Wraith (HP:12, ATK:4, DEF:2), Dark Knight (HP:15, ATK:6, DEF:3) |

### The Dungeon Master

Claude reads your play history each turn and **adapts**:

- Cautious player? Expect pressure tactics and monsters blocking exits.
- Low HP? Claude might drop a potion nearby... or not.
- Doing too well? Expect ambushes and traps near treasure.
- `?` tiles trigger unique random events — a ghostly merchant, a riddle, a cursed fountain.

---

## Tips

- **Explore thoroughly on Floor 1** — potions and treasure are your best friends early.
- **Doors `+` are walkable** — they connect rooms via corridors.
- **Water `~` slows you** — crossing it costs an extra turn.
- **Check your HP bar color** — green is safe, yellow is caution, red means use a potion.
- **The DM is watching** — erratic movement and wall-hugging both trigger different responses.

---

## Project Files

```
shadowcrypt/
├── scripts/render.py        # ASCII renderer (run directly to preview state)
├── data/game_state.json     # Live game state
├── data/game_log.json       # Full turn history
├── data/dm_summary.md       # Claude's DM notes (updated every 5 turns)
└── .claude/skills/
    └── shadowcrypt/SKILL.md # Skill definition and game loop
```

To preview the current board at any time:
```bash
python3 scripts/render.py
```
