# SPDX-License-Identifier: BSD-3-Clause
"""evennia-environment: terrain and weather for Evennia.

Tagline: *What a room's surroundings do to whoever is standing in it.*

The library holds two contributors to one answer. **Terrain** is permanent and
belongs to the room. **Weather** varies with the calendar and belongs to the
region. Both speak the same vocabulary: effect keys the consumer registers, and
values a call site asks for by name.

Nothing is public yet — the design is being agreed in docs/test-plan.md before
any of it is built. See docs/INDEX.md for the design wiki.
"""

__version__ = "0.0.1"

__all__ = []
