# SPDX-License-Identifier: BSD-3-Clause
"""What a key answers, given a terrain and a weather.

Pure Python: the contributors arrive as arguments rather than being found, so
this needs no room, no database and no Evennia. The room accessor is a thin
wrapper that finds both and delegates, and a consumer with a room-like thing
that is not a room can call this directly.

See docs/test-plan.md § RS.
"""


def resolve(effect_type, terrain_type=None, weather_type=None, **kwargs):
    """Return what ``effect_type`` answers here.

    Args:
        effect_type (EnvironmentEffectType): the key being asked about.
        terrain_type (TerrainType): the room's terrain, or None.
        weather_type (WeatherType): the weather in force, or None.
        **kwargs: whatever the call site passes, handed to every helper.

    Returns:
        The value, of the effect type's declared return type.

    Raises:
        ValueError: if a required kwarg is missing, or a helper hands back
            something other than the declared return type.
    """
    missing = [name for name in effect_type.requires if name not in kwargs]
    if missing:
        raise ValueError(
            f"{effect_type.key!r} was asked for without "
            f"{', '.join(repr(name) for name in missing)}. Its effect type "
            f"declares requires={tuple(effect_type.requires)!r}, so every call "
            f"site has to pass them."
        )

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
            effect.helper(value, **kwargs),
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

    raise ValueError(
        f"{described} answered {effect_type.key!r} with {value!r}, which is a "
        f"{type(value).__name__} rather than the "
        f"{effect_type.return_type.__name__} the effect type declares."
    )
