# SPDX-License-Identifier: BSD-3-Clause
"""The shape a consumer declares one terrain in.

A placeholder. ``TerrainType`` carries no fields yet — it exists so the room
mixin can hold a real class from the start and validate against it, rather than
accepting a string now and being retrofitted once the fields are agreed.

What it will carry is in docs/test-plan.md § Current thinking: the terrain's own
environment effects, always in force, and its ten numbered weather slots. None
of that is designed, and nothing here anticipates it.

See docs/test-plan.md § TT.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TerrainType:
    """One kind of terrain a consumer's game has. See docs/test-plan.md § TT.

    Frozen from the start rather than once it has fields: adding a field to a
    frozen class is nothing, while finding a mutable one after rooms hold it is
    a change to something already in use.
    """
