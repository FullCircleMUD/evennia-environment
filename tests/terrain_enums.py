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
