# Installing

What a game does to run `evennia-environment`, in the order it does it.

The library gives every room a terrain, derives the weather from the calendar, and answers whatever
questions a game asks about both. What those questions *are* is yours: the library holds no game
concepts and invents no effect.

## 1. Install the package

Not published, so install from a checkout alongside its dependencies:

```bash
pip install -e ../evennia-environment
pip install -e ../evennia-calendar -e ../evennia-logging-extension
```

## 2. Add the apps

```python
# settings.py
INSTALLED_APPS += [
    "evennia_calendar",
    "evennia_environment",
]
```

Both. The environment reads the day and the watch from the calendar.

## 3. Declare your environment

One module. Its four parts go in this order, because each uses the one above it: the terrains you
have, the questions your game asks, the weathers, and the terrains themselves.

See [the worked example](#a-worked-example) at the bottom for a full one.

## 4. Point the settings at it

```python
# settings.py
ENVIRONMENT_TERRAIN_ENUM  = "world.environment.Terrain"
ENVIRONMENT_TERRAIN_TYPES = "world.environment.TERRAINS"
ENVIRONMENT_DARK_WATCHES  = (6, 1)
```

## 5. Add the mixin to your rooms

```python
# typeclasses/rooms.py
from evennia import DefaultRoom
from evennia_environment.room import EnvironmentRoomMixin


class Room(EnvironmentRoomMixin, DefaultRoom):
    pass
```

Nothing to declare. `terrain` comes with the mixin.

## 6. Start the calendar clock

```python
# server/conf/at_server_startstop.py
from evennia_calendar import start_calendar_clock


def at_server_start():
    start_calendar_clock()
```

Without it the calendar never turns over, so the weather never changes. See
[evennia-calendar's installing.md](../../evennia-calendar/docs/installing.md).

## 7. Give your rooms a terrain

```python
room.terrain = Terrain.MOUNTAINS      # or "mountains"
```

Write-once: a room is given its terrain when it is built and does not change it in play. Anything
building rooms in bulk can set it as a string instead — a YAML field, say:

```yaml
attributes:
  - key: terrain
    value: mountains
```

## 8. Ask

```python
from world.environment import MOVE_COST

cost = destination.get_environment_effect(MOVE_COST, actor=character)
line = room.get_weather_description()
desc = room.get_terrain_description()
```

## Required settings

| Setting | What it does | Without it |
|---|---|---|
| `ENVIRONMENT_TERRAIN_ENUM` | Dotted path to the `Enum` naming your terrains | The instance does not start |
| `ENVIRONMENT_TERRAIN_TYPES` | Dotted path to your `TerrainType` objects | The instance does not start |
| `ENVIRONMENT_DARK_WATCHES` | Which of the calendar's six watches are dark, as numbers | The instance does not start |

None has a safe default. There is no terrain list the library could invent, and the calendar
deliberately declines to say which watches are dark.

An empty terrain enum, no terrain types, or no dark watches are each accepted — those are a game
being written, or one with no night. Not declaring the setting at all is not.

## Optional settings

| Setting | Default | Why |
|---|---|---|
| `ENVIRONMENT_WEATHER_SEED` | `""` | Mixed into the hash the weather derives from. Change it to reroll a world's entire weather history. Empty works; it just is not distinctive |

## What is not checked for you

- **`INSTALLED_APPS`.** Leave the library out and `ready()` never runs, so nothing validates anything
  and no signal is connected. The weather never changes.
- **The calendar clock.** Nothing here starts it. Without it the day and the watch never turn over,
  so the weather is whatever it was at boot.
- **What a helper returns.** Checked when it runs, not at boot — a helper is arbitrary code and
  cannot be run early to find out. A helper returning the wrong type is refused at the call, naming
  the key and which contributor answered.
- **Whether a terrain's effects make sense.** `Multiply(1.5)` against an `int` effect type produces a
  float and is refused at the call. Wrap it — `Chain(Multiply(1.5), RoundUp())`.
- **`room.db.terrain = ...`.** Assigning through `.db` writes past the property and is not validated.
  That is Evennia's behaviour and cannot be closed from here. Assign `room.terrain` instead.
- **Every enum member having a terrain type.** Accepted deliberately: a member with none is a game
  still being written. Rooms of that terrain answer with each effect type's default.

## When something is refused

Everything the library refuses is written to `environment.log` under your `LOG_DIR`, at ERROR, before
it raises. Look there first — the exception reaches whoever ran the command, and the file is what is
still there afterwards.

| What you see | What it means |
|---|---|
| `evennia-environment cannot start:` and a list | A setting is wrong. Every problem found is listed, so fix them all in one pass |
| The same, with a traceback under it | A module one of your settings names would not import. The traceback is the line that broke |
| `Mossy Hollow (#1): terrain cannot be 'swmap'` | A room was assigned a terrain no enum member names. The key and dbref are there so you can find it |
| `the terrain 'swamp' answered 'movement_cost' with …` | A helper handed back the wrong type. The contributor named is the one that got it wrong |

**The same line repeating is not a bug.** `resolve()` runs on every call that asks a room a question,
so one broken helper writes a line each time. The volume is telling you it is still broken.

## A worked example

A game with two terrains, three questions and four weathers.

```python
# world/environment.py
from enum import Enum

from evennia_environment import (
    Add,
    Chain,
    Constant,
    EnvironmentEffect,
    EnvironmentEffectType,
    Multiply,
    RoundUp,
    TerrainType,
    WeatherSlot,
    WeatherType,
)


# 1. The terrains this game has.
class Terrain(Enum):
    DESERT = "desert"
    MOUNTAINS = "mountains"


# 2. The questions the game asks: what can be asked for, what type it answers
#    in, and what it answers when nothing declares otherwise.
MOVE_COST = EnvironmentEffectType("move_cost", float, Constant(1.0))
THIRST_RATE = EnvironmentEffectType("thirst_rate", int, Constant(1))
VISIBILITY = EnvironmentEffectType("visibility", float, Constant(1.0))


# 3. The weathers, each declaring only what it changes.
CLEAR = WeatherType(key="clear", description="The sky is open and still.")

SCORCHING = WeatherType(
    key="scorching",
    description="The air shimmers above the dunes.",
    transition_in="The heat settles over you like a weight.",
    effects=(EnvironmentEffect(THIRST_RATE, Add(2)),),
)

FREEZING_CLEAR = WeatherType(
    key="freezing_clear",
    description="The cold comes down hard under a clear sky.",
    transition_in="The warmth goes out of the sand, and the cold arrives.",
    effects=(EnvironmentEffect(MOVE_COST, Multiply(1.2)),),
)

BLIZZARD = WeatherType(
    key="blizzard",
    description="Snow drives across the ridge in sheets.",
    transition_in="The wind rises, and the snow begins to drive.",
    effects=(
        EnvironmentEffect(VISIBILITY, Constant(0.2)),
        EnvironmentEffect(MOVE_COST, Chain(Multiply(1.5), RoundUp())),
    ),
)


# 4. The terrains: their own effects, always in force, and ten weather slots.
DESERT = TerrainType(
    key="desert",
    description="Dunes run to the horizon in every direction.",
    effects=(EnvironmentEffect(THIRST_RATE, Add(1)),),
    weather_slots={
        1: WeatherSlot(CLEAR),
        2: WeatherSlot(CLEAR),
        3: WeatherSlot(CLEAR),
        4: WeatherSlot(CLEAR),
        5: WeatherSlot(SCORCHING, night=FREEZING_CLEAR),
        6: WeatherSlot(SCORCHING, night=FREEZING_CLEAR),
        7: WeatherSlot(SCORCHING, night=FREEZING_CLEAR),
        8: WeatherSlot(SCORCHING, night=FREEZING_CLEAR),
        9: WeatherSlot(SCORCHING, night=FREEZING_CLEAR),
        10: WeatherSlot(SCORCHING, night=FREEZING_CLEAR),
    },
)

MOUNTAINS = TerrainType(
    key="mountains",
    description="Bare rock and scree, falling away on every side.",
    effects=(EnvironmentEffect(MOVE_COST, Constant(2.0)),),
    weather_slots={
        1: WeatherSlot(CLEAR),
        2: WeatherSlot(CLEAR),
        3: WeatherSlot(CLEAR),
        4: WeatherSlot(CLEAR),
        5: WeatherSlot(CLEAR),
        6: WeatherSlot(CLEAR),
        7: WeatherSlot(BLIZZARD),
        8: WeatherSlot(BLIZZARD),
        9: WeatherSlot(BLIZZARD),
        10: WeatherSlot(BLIZZARD),
    },
)

TERRAINS = (DESERT, MOUNTAINS)
```

Reading it back out of that:

- **Repeating a weather across slots weights it.** The mountains are clear in six slots of ten and
  blizzard in four, and the band reaches 7 and above far more often in winter.
- **The desert is hot from slot 5 up**, so it is scorching most of the year, and its nights bite only
  on the days it was hot.
- **Slots 1 and 2 are reachable only in winter, 9 and 10 only in summer.** The mountains' blizzards
  are a winter event; the desert's worst heat is a summer one.
- **`WeatherSlot` is always what a slot holds.** A weather that does not change after dark is
  `WeatherSlot(CLEAR)`, and the slot fills its night from its day.
