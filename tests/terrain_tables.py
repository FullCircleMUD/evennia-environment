# SPDX-License-Identifier: BSD-3-Clause
"""Terrain type collections for the suite, standing in for a consumer's.

Imports the library but no Evennia, so it can be resolved from a setting while
Django is still building its app registry — which is when ``ready()`` runs.
"""

from evennia_environment import TerrainType, WeatherSlot, WeatherType

_STILL = WeatherType(key="still_air")
_TEN_STILL = {n: _STILL for n in range(1, 11)}

SWAMP = TerrainType(
    key="swamp",
    description="Black water between the roots.",
    weather_slots=_TEN_STILL,
)

#: Ten distinct weathers, one per slot, so WB-11 proves the band picks the
#: slot of its own number rather than any slot.
_NUMBERED = {n: WeatherType(key=f"band_{n}") for n in range(1, 11)}

#: Slot 4 alone differs after dark, so WB-12 proves the night is read rather
#: than the day happening to match.
_DAY = WeatherType(key="scorching", description="The air shimmers.")
_NIGHT = WeatherType(key="freezing_clear", description="The cold bites.")
_NUMBERED_WITH_NIGHT = dict(_NUMBERED)
_NUMBERED_WITH_NIGHT[4] = WeatherSlot(_DAY, night=_NIGHT)

MOUNTAINS = TerrainType(key="mountains", weather_slots=_NUMBERED_WITH_NIGHT)

#: Every key names a member of tests.terrain_enums.Terrain.
TERRAINS = (SWAMP, MOUNTAINS)

#: One fewer than the enum has, which is legal — a game declares its terrains
#: as it writes them. CF-13.
PARTIAL_TERRAINS = (SWAMP,)

#: A key no enum member names, so nothing could ever reach it. CF-12.
UNREACHABLE_TERRAINS = (
    SWAMP,
    TerrainType(key="tundra", weather_slots=_TEN_STILL),
)

NOT_TERRAIN_TYPES = ("swamp", "mountains")

#: Nothing declared yet, which is a correct reading rather than a mistake and
#: pairs with an empty enum. CF-05.
NO_TERRAINS = ()
