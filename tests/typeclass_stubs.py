# SPDX-License-Identifier: BSD-3-Clause
"""Stand-in room typeclasses for the startup-validation tests.

**Nothing here imports Evennia.** `test_settings.py` points
``BASE_ROOM_TYPECLASS`` at one of these, and `check_settings` resolves that
during ``django.setup()`` — before Django has finished starting, and while
``evennia.DefaultRoom`` is still ``None``. A class inheriting from it at that
moment dies on a metaclass conflict.

They are not real typeclasses and do not need to be: startup validation only
asks what a class inherits from. A room the suite actually creates objects
from lives in `game_typeclasses.py`, which is imported lazily inside a test.

The same shape `evennia-scaling` uses for the same reason.
"""

from evennia_environment.room import EnvironmentRoomMixin


class RoomStub(EnvironmentRoomMixin):
    """Correctly configured — the mixin is there. CF-24's case."""


class PlainStub:
    """No mixin — what an unmodified Evennia room typeclass looks like.

    CF-25's case: the app installed and the mixin never mixed in.
    """
