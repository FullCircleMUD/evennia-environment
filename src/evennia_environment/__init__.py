# SPDX-License-Identifier: BSD-3-Clause
"""evennia-environment: terrain and weather for Evennia.

Tagline: *What a room's surroundings do to whoever is standing in it.*

The library holds two contributors to one answer. **Terrain** is permanent and
belongs to the room. **Weather** comes from the terrain's ten slots, varying
with the calendar's day and season. Both speak the same vocabulary: effect keys
the consumer declares, and values a call site asks for by name. Either
contribution may differ by day and night.

What a consumer imports from here: the declarations — ``EnvironmentEffectType``,
``EnvironmentEffect``, ``WeatherType``, ``WeatherSlot``, ``TerrainType`` — the
stock helpers, ``NO_TERRAIN``, and ``resolve()``. ``__all__`` below is the
list.

``EnvironmentRoomMixin`` is **not** here. It imports Evennia, and this module is
imported while Django is still building its app registry, so a consumer takes it
from ``evennia_environment.room`` directly.

See docs/installing.md for what a consumer declares, and docs/INDEX.md for the
design wiki.
"""

# Safe at module scope: both are pure Python and import neither Django nor
# Evennia, so nothing here runs while the app registry is still being built.
from evennia_environment.effects import (
    EnvironmentEffect,
    EnvironmentEffectType,
)
from evennia_environment.helpers import (
    Add,
    Chain,
    Constant,
    Multiply,
    RoundDown,
    RoundUp,
)
from evennia_environment.resolve import resolve
from evennia_environment.terrain import NO_TERRAIN, TerrainType
from evennia_environment.weather import (
    WeatherSlot,
    WeatherType,
    current_weather,
    current_weather_band,
    is_night,
    weather_band,
)

__version__ = "0.0.1"

__all__ = [
    "Add",
    "Chain",
    "Constant",
    "EnvironmentEffect",
    "EnvironmentEffectType",
    "Multiply",
    "NO_TERRAIN",
    "RoundDown",
    "RoundUp",
    "TerrainType",
    "WeatherSlot",
    "WeatherType",
    "current_weather",
    "current_weather_band",
    "is_night",
    "resolve",
    "weather_band",
]
