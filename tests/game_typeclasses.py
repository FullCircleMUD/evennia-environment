# SPDX-License-Identifier: BSD-3-Clause
"""Real Evennia typeclasses carrying the library's properties.

``AttributeProperty`` needs an object with an attribute handler behind it, so
the TP cases create one of these rather than faking one.

This module imports Evennia, so it is imported inside a test body rather than
at module scope.
"""

from evennia import DefaultRoom

from evennia_environment.room import EnvironmentRoomMixin


class TerrainRoom(EnvironmentRoomMixin, DefaultRoom):
    """A room carrying the mixin, as a consumer's room typeclass does.

    It declares nothing: the mixin brings ``terrain``, and the property reads
    the game's enum from the setting.
    """
