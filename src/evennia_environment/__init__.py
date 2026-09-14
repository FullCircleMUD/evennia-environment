# SPDX-License-Identifier: BSD-3-Clause
"""evennia-environment: terrain and weather for Evennia.

Tagline: *What a room's surroundings do to whoever is standing in it.*

The library holds two contributors to one answer. **Terrain** is permanent and
belongs to the room. **Weather** varies with the calendar and belongs to the
region. Both speak the same vocabulary: effect keys the consumer registers, and
values a call site asks for by name.

``EnvironmentEffectType`` and ``ENVIRONMENT_EFFECT_TYPES`` are the public surface so
far — the shape a consumer declares one effect in, and the list they declare it
to. The rest of the design is being agreed in docs/test-plan.md before it is
built. See docs/INDEX.md for the design wiki.
"""

# Safe at module scope: both are pure Python and import neither Django nor
# Evennia, so nothing here runs while the app registry is still being built.
from evennia_environment.effects import (
    ENVIRONMENT_EFFECT_TYPES,
    EnvironmentEffect,
    EnvironmentEffectType,
    EnvironmentEffectTypeRegistry,
)
from evennia_environment.terrain import TerrainType
from evennia_environment.weather import WeatherSlot, WeatherType

__version__ = "0.0.1"

__all__ = [
    "ENVIRONMENT_EFFECT_TYPES",
    "EnvironmentEffect",
    "EnvironmentEffectType",
    "EnvironmentEffectTypeRegistry",
    "TerrainType",
    "WeatherSlot",
    "WeatherType",
]
