# SPDX-License-Identifier: BSD-3-Clause
"""What a key answers in a place, given the room's terrain.

Given an effect key and a terrain, this works out which contributions apply —
the terrain's, and those of the weather in force there — and folds them in
order into one value the caller acts on.

**A terrain is always given.** A room with none of its own resolves against
``NO_TERRAIN``, which declares nothing, so absence is answered before this is
reached and nothing here asks whether a terrain is there.

**The hour is read here, once.** Two things depend on it — which of a slot's
two weathers is in force, and which half of each contribution runs — and
neither re-checks it. That is what reading the calendar costs: this is no
longer callable with nothing running. ``_fold`` underneath takes everything it
needs as arguments and stays a plain function.

See docs/test-plan.md § RS and § RL.
"""

from evennia_environment.refusal import refuse
from evennia_environment.terrain import TerrainType
from evennia_environment.weather import current_weather, is_night


def resolve(effect_type, terrain_type, **kwargs):
    """Return what ``effect_type`` answers in ``terrain_type``.

    Args:
        effect_type (EnvironmentEffectType): the key being asked about.
        terrain_type (TerrainType): the room's terrain. ``NO_TERRAIN`` for a
            room with none of its own — never ``None``.
        **kwargs: whatever the call site passes, handed to every helper.

    Returns:
        The value, of the effect type's declared return type.

    Raises:
        ValueError: if the terrain is not a ``TerrainType``, a required kwarg
            is missing, or a helper hands back something other than the
            declared return type.
    """
    # First: everything below reads the terrain, and a wrong one would
    # otherwise walk nothing, find nothing and quietly answer the default.
    if not isinstance(terrain_type, TerrainType):
        refuse(
            f"{effect_type.key!r} was asked for with {terrain_type!r} as its "
            f"terrain, which is a {type(terrain_type).__name__} rather than a "
            f"TerrainType. A room with no terrain of its own resolves against "
            f"NO_TERRAIN."
        )

    missing = [name for name in effect_type.requires if name not in kwargs]
    if missing:
        refuse(
            f"{effect_type.key!r} was asked for without "
            f"{', '.join(repr(name) for name in missing)}. Its effect type "
            f"declares requires={tuple(effect_type.requires)!r}, so every call "
            f"site has to pass them."
        )

    # Once, at the top, and this answer is what the rest of the call uses.
    night = is_night()

    return _fold(
        effect_type, terrain_type, current_weather(terrain_type, night), night, **kwargs
    )


def _fold(effect_type, terrain_type, weather_type, night, /, **kwargs):
    """Run the default and then the contributors, checking each answer.

    Split from ``resolve`` so the mechanics take everything they need as
    arguments and read no clock — which is what keeps this half callable with
    nothing running.
    """
    # The default is the starting value, not a fallback consulted at the end:
    # a contribution that modifies what came before needs something to modify,
    # and a contribution that replaces it simply ignores what it was handed.
    value = _checked(
        effect_type.default(None, **kwargs), effect_type, "its default"
    )

    # Terrain, then weather. Fixed and not configurable: terrain is the base a
    # place has, weather is what varies over it. One contribution each is what
    # keeps this to two links, so there is no ordering to resolve.
    for contributor, described in (
        (terrain_type, "terrain"),
        (weather_type, "weather"),
    ):
        effect = _declared_by(contributor, effect_type)
        if effect is None:
            continue

        value = _checked(
            effect.helper_for(night)(value, **kwargs),
            effect_type,
            f"the {described} {contributor.key!r}",
        )

    return value


def _declared_by(contributor, effect_type):
    """Return the contributor's effect for this key, or ``None``.

    A linear walk: a terrain or a weather declares only what it changes, so
    there are a handful of entries at most, and one per key is guaranteed at
    the declaration.
    """
    if contributor is None:
        return None

    for effect in contributor.effects:
        if effect.effect_type is effect_type:
            return effect

    return None


def _checked(value, effect_type, described):
    """Return ``value``, or refuse it as the wrong type for this key.

    Checked after every step rather than once at the end, which is what lets
    the refusal name which helper got it wrong instead of leaving a consumer
    three candidates.
    """
    if isinstance(value, effect_type.return_type):
        return value

    refuse(
        f"{described} answered {effect_type.key!r} with {value!r}, which is a "
        f"{type(value).__name__} rather than the "
        f"{effect_type.return_type.__name__} the effect type declares."
    )
