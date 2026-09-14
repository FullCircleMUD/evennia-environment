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

from enum import Enum

# Evennia, because AttributeProperty is Evennia's — a descriptor over its
# attribute handler, and the mechanism this library validates through. There is
# no engine-free equivalent to import instead.
from evennia.typeclasses.attributes import AttributeProperty


class TerrainProperty(AttributeProperty):
    """A room's terrain: an enum member in, a string stored, the member back.

    Declared with the consumer's terrain enum, which is what lets it tell
    ``Terrain.SWAMP`` from another enum's member and resolve ``"swamp"`` to the
    member it names. Write-once: a room is given its terrain when it is built
    and does not change it in play.
    """

    def __init__(self, terrain_enum, **kwargs):
        """Hold the enum every assignment is checked against.

        Raises a ``ValueError`` rather than an ``AttributeError``: this runs in
        the consumer's class body, so it is a declaration being wrong rather
        than a value arriving, and it matches every other declaration in this
        library.
        """
        if not (isinstance(terrain_enum, type) and issubclass(terrain_enum, Enum)):
            raise ValueError(
                f"TerrainProperty was declared with {terrain_enum!r}, which is "
                f"a {type(terrain_enum).__name__} rather than an Enum class. "
                f"Pass the enum naming your game's terrains."
            )

        self._terrain_enum = terrain_enum

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

        return self._terrain_enum(value)

    def _to_stored(self, value):
        """Return what ``value`` should be stored as, or refuse it.

        A member gives its value; the value itself is taken as naming that
        member. Both forms exist because YAML world content can only supply the
        string, and library code will naturally hand over the member.
        """
        if value is None:
            return None

        if isinstance(value, self._terrain_enum):
            return value.value

        if isinstance(value, str):
            try:
                return self._terrain_enum(value).value
            except ValueError:
                raise AttributeError(
                    f"{self._key} cannot be {value!r}: no terrain has that "
                    f"name. Declared are "
                    f"{', '.join(repr(m.value) for m in self._terrain_enum)}."
                ) from None

        raise AttributeError(
            f"{self._key} cannot be {value!r}. It must be a member of "
            f"{self._terrain_enum.__name__}, or the name of one as a string."
        )
