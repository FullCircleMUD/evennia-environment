# SPDX-License-Identifier: BSD-3-Clause
"""Terrain enums for the suite, standing in for a consumer's own.

Imports nothing but ``enum`` — the same discipline as
``evennia-equipment``'s ``tests/slot_enums.py``. A consumer's declaration
module is imported early and from places that cannot afford Evennia, and a
fixture that reached for anything heavier would stop proving that.
"""

from enum import Enum


class Terrain(Enum):
    """What a consumer's terrain enum looks like."""

    SWAMP = "swamp"
    MOUNTAINS = "mountains"


class Season(Enum):
    """An unrelated enum, so TP-04 has something to be wrong against.

    A member of this is a perfectly good enum member and still not a terrain,
    which is the distinction a property holding the enum can draw and a bare
    ``isinstance(value, Enum)`` check cannot.
    """

    WINTER = "winter"


class AliasedTerrain(Enum):
    """Two members sharing a value, which Python folds into one. CF-06.

    ``JUNGLE`` becomes a second name for ``FOREST`` and the game is a terrain
    short, with nothing raised.
    """

    FOREST = "forest"
    JUNGLE = "forest"


class NumberedTerrain(Enum):
    """Values that are not strings. CF-07."""

    SWAMP = 1
    MOUNTAINS = 2


class DoublyWrongTerrain(Enum):
    """A duplicate value and a non-string value at once. CF-08."""

    FOREST = "forest"
    JUNGLE = "forest"
    SWAMP = 3


class EmptyTerrain(Enum):
    """No members, which is a correct reading rather than a mistake. CF-05."""


NOT_AN_ENUM = "this names no terrains"


#: Declared in a module that imports nothing but ``enum``, so the terrain types
#: themselves live beside the suite's other fixtures rather than here. See
#: tests/terrain_tables.py.
