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

from evennia_environment.config import terrain_enum, terrain_types
# Aliased: the mixin exposes a ``current_weather`` of its own, and two of
# that name in one module reads as a mistake even where it is not.
from evennia_environment.resolve import resolve
from evennia_environment.weather import current_weather as _weather_in_force


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
        incoming = self._to_stored(value)

        # Write-once, and identical is not a write. A room is given its terrain
        # when it is built; re-applying the same content is harmless, and any
        # other change — including clearing it — is refused.
        if stored is not None and incoming != stored:
            raise AttributeError(
                f"{self._key} is already {stored!r} and cannot be changed to "
                f"{value!r}. A room's terrain is set when it is built and does "
                f"not change in play."
            )

        return incoming

    def at_get(self, value, obj):
        """Return the stored value resolved back to its enum member."""
        if value is None:
            return None

        return terrain_enum()(value)

    def _to_stored(self, value):
        """Return what ``value`` should be stored as, or refuse it.

        A member gives its value; the value itself is taken as naming that
        member. Both forms exist because YAML world content can only supply the
        string, and library code will naturally hand over the member.
        """
        if value is None:
            return None

        if isinstance(value, terrain_enum()):
            return value.value

        if isinstance(value, str):
            try:
                return terrain_enum()(value).value
            except ValueError:
                raise AttributeError(
                    f"{self._key} cannot be {value!r}: no terrain has that "
                    f"name. Declared are "
                    f"{', '.join(repr(m.value) for m in terrain_enum())}."
                ) from None

        raise AttributeError(
            f"{self._key} cannot be {value!r}. It must be a member of "
            f"{terrain_enum().__name__}, or the name of one as a string."
        )


class EnvironmentRoomMixin:
    """What a room answers about its surroundings. A placeholder.

    Mixed into a consumer's own room typeclass. It brings ``terrain`` with it —
    the property reads the game's enum from the setting, so there is nothing
    per-typeclass to declare.

    ::

        class Room(EnvironmentRoomMixin, DefaultRoom):
            pass

    Every method here is unimplemented. Two things are missing under them: the
    route from the stored terrain to its ``TerrainType``, and which of the
    terrain's ten weather slots is active. See docs/test-plan.md § RM.
    """

    terrain = TerrainProperty()

    def get_environment_effect(self, effect_type, **kwargs):
        """Return what ``effect_type`` answers in this room.

        Args:
            effect_type (EnvironmentEffectType): the key being asked about.
            **kwargs: whatever this key requires, and anything else a helper
                may want.

        Returns:
            The value, of the effect type's declared return type.
        """
        # Both optional: a room with no terrain has no weather either, and
        # resolve answers with the effect type's default.
        return resolve(
            effect_type,
            terrain_type=self.terrain_type,
            weather_type=self.current_weather,
            **kwargs,
        )

    def get_terrain_description(self):
        """Return this room's terrain's description, or ``None``.

        ``None`` for a room with no terrain, and for a terrain that declares
        no description — both are ordinary, so neither raises.
        """
        terrain = self.terrain_type
        return None if terrain is None else terrain.description

    @property
    def terrain_type(self):
        """Return the ``TerrainType`` this room's terrain names, or ``None``.

        The room stores a member; the type carrying what that terrain does is
        the one whose key is the member's value. Boot has already refused a
        type no member names, so a member with no type is the only miss, and
        it means a game still being written.
        """
        terrain = self.terrain
        return None if terrain is None else terrain_types().get(terrain.value)

    def get_weather_description(self, day=None):
        """Return the active weather's description, or ``None``.

        ``None`` for a room with no terrain — there is no slot table to read a
        band against — and for a weather that declares no description. Both
        are ordinary, so neither raises.

        Args:
            day (bool): forces the day weather when true and the night one
                when false. The current watch decides when it is not given.
        """
        terrain = self.terrain_type
        if terrain is None:
            return None

        # None leaves it to the watch; True and False override it.
        dark = None if day is None else not day

        return _weather_in_force(terrain, dark=dark).description

    @property
    def current_weather(self):
        """Return the ``WeatherType`` in force here, or ``None``.

        ``None`` only when the room has no terrain: the band names a slot,
        every slot is filled, and both a slot's weathers are always populated.
        """
        terrain = self.terrain_type
        return None if terrain is None else _weather_in_force(terrain)
