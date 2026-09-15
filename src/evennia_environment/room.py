# SPDX-License-Identifier: BSD-3-Clause
"""What a room carries: its terrain, and the property holding it.

**Not re-exported from the package.** This module imports Evennia, and
``evennia_environment/__init__.py`` is imported while Django is still building
its app registry — so a consumer imports from here directly, as they do with
``evennia-equipment``'s mixins.

A room's terrain is held as the enum member's string value and read back as the
member. The string is what a YAML world file can write and what a database can
be queried on; the member is what a consumer's code wants in hand.

See docs/test-plan.md § TP.
"""

# Evennia, because AttributeProperty is Evennia's — a descriptor over its
# attribute handler, and the mechanism this library validates through. There is
# no engine-free equivalent to import instead.
from evennia.typeclasses.attributes import AttributeProperty

from evennia_environment.config import (
    RESERVED_KWARGS,
    terrain_enum,
    terrain_types,
)
from evennia_environment.refusal import refuse, refuse_attribute
# Aliased: the mixin exposes a ``current_weather`` of its own, and two of
# that name in one module reads as a mistake even where it is not.
from evennia_environment.resolve import resolve
from evennia_environment.terrain import NO_TERRAIN
from evennia_environment.weather import current_weather as _weather_in_force


def _named(obj):
    """Return how a room is identified in a refusal.

    Both the key and the dbref, because two rooms can carry the same key and
    the one that failed has to be findable from the line alone.
    """
    return f"{obj.key} ({obj.dbref})"


class TerrainProperty(AttributeProperty):
    """A room's terrain: an enum member in, a string stored, the member back.

    The enum comes from ``ENVIRONMENT_TERRAIN_ENUM`` through
    ``config.terrain_enum()``, resolved once at boot — which is what lets the
    property take no arguments and the mixin carry it. Write-once: a room is
    given its terrain when it is built and does not change it in play.
    """

    def __init__(self, **kwargs):
        """Declare the attribute. The enum is read when it is needed."""
        # strattr so the stored name lands in Evennia's string column and a
        # search for every swamp room is a query rather than a walk. It cannot
        # be turned on later: a value written without the flag is invisible to
        # a property declared with it.
        kwargs.setdefault("strattr", True)
        super().__init__(default=None, **kwargs)

    def at_set(self, value, obj):
        """Return the value to store, or refuse the assignment.

        ``autocreate`` is on by default, so the first read of an unset terrain
        arrives here carrying the default. That is why ``None`` is acceptable
        while nothing is stored — refusing it would make an unassigned room
        raise on being read.
        """
        stored = obj.attributes.get(
            self._key, category=self._category, strattr=True
        )
        incoming = self._to_stored(value, obj)

        # Write-once, and identical is not a write. A room is given its terrain
        # when it is built; re-applying the same content is harmless, and any
        # other change — including clearing it — is refused.
        if stored is not None and incoming != stored:
            refuse_attribute(
                f"{_named(obj)}: {self._key} is already {stored!r} and cannot "
                f"be changed to {value!r}. A room's terrain is set when it is "
                f"built and does not change in play."
            )

        return incoming

    def at_get(self, value, obj):
        """Return the stored value resolved back to its enum member."""
        if value is None:
            return None

        return terrain_enum()(value)

    def _to_stored(self, value, obj):
        """Return what ``value`` should be stored as, or refuse it.

        A member gives its value; the value itself is taken as naming that
        member. Both forms exist because YAML world content can only supply the
        string, and library code will naturally hand over the member.

        ``obj`` is here only to name the room in a refusal. A build applying
        content to hundreds of them needs the one that failed, and without this
        the message carries the bad value and nothing to search for.
        """
        if value is None:
            return None

        if isinstance(value, terrain_enum()):
            return value.value

        if isinstance(value, str):
            try:
                return terrain_enum()(value).value
            except ValueError:
                # The enum's own ValueError is suppressed: the consumer's
                # mistake is the name, not the lookup that went looking for it.
                refuse_attribute(
                    f"{_named(obj)}: {self._key} cannot be {value!r}: no "
                    f"terrain has that name. Declared are "
                    f"{', '.join(repr(m.value) for m in terrain_enum())}.",
                    suppress_context=True,
                )

        refuse_attribute(
            f"{_named(obj)}: {self._key} cannot be {value!r}. It must be a "
            f"member of {terrain_enum().__name__}, or the name of one as a "
            f"string."
        )


class EnvironmentRoomMixin:
    """What a room answers about its surroundings.

    Mixed into a consumer's own room typeclass. It brings ``terrain`` with it —
    the property reads the game's enum from the setting, so there is nothing
    per-typeclass to declare.

    ::

        class Room(EnvironmentRoomMixin, DefaultRoom):
            pass

    A thin wrapper: it finds the room's terrain type and hands it to
    ``resolve()``, which finds the weather and reads the hour itself. See
    docs/test-plan.md § RM.
    """

    terrain = TerrainProperty()

    def get_environment_effect(self, effect_type, /, **kwargs):
        """Return what ``effect_type`` answers in this room.

        ``effect_type`` is positional-only so a caller's kwarg of that name
        lands in ``kwargs`` and is refused below, rather than raising Python's
        own ``TypeError`` before this runs.

        Args:
            effect_type (EnvironmentEffectType): the key being asked about.
            **kwargs: whatever this key requires, and anything else a helper
                may want. Not ``effect_type`` or ``terrain_type``.

        Returns:
            The value, of the effect type's declared return type.

        Raises:
            ValueError: if a kwarg uses a reserved name.
        """
        # Refused here because this is the only place kwargs is still separate
        # from the positional arguments. Left alone, resolve() gets the terrain
        # twice and Python raises before it runs — naming a parameter the
        # caller never passed, from a call where no terrain is visible.
        reserved = sorted(RESERVED_KWARGS & kwargs.keys())
        if reserved:
            refuse(
                f"{_named(self)}: {', '.join(repr(name) for name in reserved)} "
                f"cannot be passed to get_environment_effect. "
                f"{' and '.join(sorted(repr(n) for n in RESERVED_KWARGS))} are "
                f"the library's own — the effect type is the first argument and "
                f"the terrain comes from the room. Name your kwarg something "
                f"else."
            )

        # The terrain alone: resolve finds the weather from its slots and
        # reads the hour itself, so neither is worked out twice.
        return resolve(effect_type, self.terrain_type, **kwargs)

    def get_terrain_description(self):
        """Return this room's terrain's description, or ``None``.

        ``None`` for a terrain that declares no description, and for a room
        with no terrain of its own — the null terrain declares none either.
        Both are ordinary, so neither raises.
        """
        return self.terrain_type.description

    @property
    def terrain_type(self):
        """Return the ``TerrainType`` to resolve against here. Never ``None``.

        The room stores a member; the type carrying what that terrain does is
        the one whose key is the member's value.

        Two ways a room has no terrain of its own — none was assigned, and the
        member it carries has no type declared yet — and both answer
        ``NO_TERRAIN``. That declares nothing, so every key falls through to
        its own default, which is what an absent terrain gave. Substituting
        here rather than at each reader is what lets the accessors below, and
        ``resolve()``, drop their absence checks.

        ``self.terrain`` is untouched and still answers ``None``, so a builder
        asking which rooms still need one keeps its signal.
        """
        terrain = self.terrain
        if terrain is None:
            return NO_TERRAIN

        return terrain_types().get(terrain.value, NO_TERRAIN)

    def get_weather_description(self, day=None):
        """Return the active weather's description, or ``None``.

        ``None`` for a weather that declares no description, which includes
        the null terrain's — so a room with no terrain of its own answers the
        same as it did when there was nothing to read. Both are ordinary, so
        neither raises.

        Args:
            day (bool): forces the day weather when true and the night one
                when false. The current watch decides when it is not given.
        """
        # None leaves it to the watch; True and False override it.
        night = None if day is None else not day

        return _weather_in_force(self.terrain_type, night=night).description

    @property
    def current_weather(self):
        """Return the ``WeatherType`` in force here. Never ``None``.

        Every terrain has ten filled slots and both of a slot's weathers are
        always populated — and a room with none of its own resolves against
        the null terrain, whose slots are filled like any other's.
        """
        return _weather_in_force(self.terrain_type)
