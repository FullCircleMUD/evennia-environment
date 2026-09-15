# SPDX-License-Identifier: BSD-3-Clause
"""The shape a consumer declares one terrain in.

A terrain is permanent and belongs to the room. It carries its own effects,
always in force whatever the sky is doing, and the ten weather slots that can
occur in it.

**Declaring an effect means changing it.** A terrain declares only the keys it
wants different from the default; silence leaves the default's answer standing.

See docs/test-plan.md § TT.
"""

from dataclasses import dataclass
from typing import Optional

from evennia_environment.config import SLOT_NUMBERS
from evennia_environment.effects import one_effect_per_type
from evennia_environment.refusal import refuse
from evennia_environment.weather import WeatherSlot, WeatherType


@dataclass(frozen=True)
class TerrainType:
    """One kind of terrain a consumer's game has. See docs/test-plan.md § TT.

    ``weather_slots`` is declared as a dict keyed one to ten and stored as a
    tuple in slot order — a dict in a frozen dataclass is mutable, and mutating
    it would change every room of this terrain at read time. The same weather in
    several slots is how a terrain weights it.
    """

    key: str
    effects: tuple = ()
    weather_slots: dict = None
    description: Optional[str] = None

    def __post_init__(self):
        """Refuse a declaration that cannot be used, naming the key.

        Every refusal is a ``ValueError``, as every other declaration's is.
        """
        if not isinstance(self.key, str):
            refuse(
                f"TerrainType key {self.key!r} is a {type(self.key).__name__}, "
                f"not a string. A terrain is looked up by name, so its key has "
                f"to be one."
            )

        if not self.key:
            refuse(
                "TerrainType key is empty. Without a key the terrain names "
                "nothing and no room can be assigned it."
            )

        object.__setattr__(
            self,
            "effects",
            one_effect_per_type(self.effects, f"Terrain {self.key!r}"),
        )

        object.__setattr__(self, "weather_slots", self._slots_in_order())

        if self.description is not None and not isinstance(self.description, str):
            refuse(
                f"Terrain {self.key!r} declares a description as a "
                f"{type(self.description).__name__}. It is text the consumer "
                f"renders, so it has to be a string, or None for none at all."
            )

    def _slots_in_order(self):
        """Return the ten slots as a tuple, refusing anything else.

        A terrain with no weather — a cavern, an interior — still declares ten,
        of whatever its still air is called. That keeps the rule unconditional
        and means nothing downstream asks whether a terrain has weather.
        """
        slots = self.weather_slots

        if not isinstance(slots, dict):
            refuse(
                f"Terrain {self.key!r} declares weather_slots as {slots!r}. It "
                f"is a dict keyed 1 to 10, one weather slot each."
            )

        missing = sorted(set(SLOT_NUMBERS) - set(slots))
        extra = sorted(
            repr(number) for number in slots if number not in SLOT_NUMBERS
        )
        if missing or extra:
            refuse(
                f"Terrain {self.key!r} declares weather slots "
                f"{sorted(map(repr, slots))}. Every terrain has exactly ten, "
                f"keyed 1 to 10"
                + (f"; missing {missing}" if missing else "")
                + (f"; unexpected {extra}" if extra else "")
                + ". Repeat a weather across slots to weight it."
            )

        ordered = []
        for number in SLOT_NUMBERS:
            slot = slots[number]

            # A WeatherSlot and nothing else, a WeatherType included. One
            # shape, so a consumer never chooses between two classes on a
            # condition — a slot that does not change at night is
            # WeatherSlot(BLIZZARD), and the slot fills its own night.
            if not isinstance(slot, WeatherSlot):
                refuse(
                    f"Terrain {self.key!r} declares {slot!r} in weather slot "
                    f"{number}, which is a {type(slot).__name__}. Every slot "
                    f"holds a WeatherSlot — wrap a weather that does not change "
                    f"at night, as WeatherSlot(blizzard)."
                )

            ordered.append(slot)

        return tuple(ordered)


# Declared here rather than in config.py, where library-standards.md puts
# module-level constants. An exemption for these two only — anything else new
# goes in config.py.
#
# They cannot move: both are built by *calling* TerrainType(...) and
# WeatherType(...), so config.py would need those imported at module scope, and
# this module already imports SLOT_NUMBERS from config.py — that closes a
# cycle. config.py works around the same cycle in _check_terrain_types by
# importing TerrainType inside the function, which a check can do and a
# constant cannot.
#
# The library-standards linter's `constant_outside_config` warning names these
# two and is expected. Do not "fix" it by moving them.

#: The weather a room with no terrain has: nothing, said as a weather so the
#: slot table below can be filled. It declares no effects and no text, so it
#: contributes nothing and renders as nothing.
_NO_WEATHER = WeatherType(key="no_weather")

#: What ``EnvironmentRoomMixin.terrain_type`` answers when a room has no
#: terrain of its own — because none was assigned, or because the member it
#: carries has no ``TerrainType`` declared for it yet.
#:
#: A null object, not content. It declares no effects, so every key falls
#: through to its own default — the same answer an absent terrain gave, with
#: nothing downstream having to ask whether a terrain is there. The library
#: naming a terrain would breach its own rules; naming *nothing* does not.
#:
#: Its key names what it is rather than being empty — a declaration refuses an
#: empty key, and nothing here should be built past its own validation. The key
#: collides with nothing because the null is never looked up by one: it is what
#: a lookup answers when it *misses*, so a consumer declaring the same string
#: gets their own terrain and never this.
#:
#: It never reaches the database. ``room.terrain`` still answers ``None`` for
#: an unassigned room, so a builder asking which rooms still need one keeps
#: its signal.
NO_TERRAIN = TerrainType(
    key="no_terrain",
    effects=(),
    weather_slots={number: WeatherSlot(_NO_WEATHER) for number in SLOT_NUMBERS},
)
