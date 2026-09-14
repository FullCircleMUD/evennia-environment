# SPDX-License-Identifier: BSD-3-Clause
"""The shape a consumer declares one weather in.

A weather is one entry in a game's spectrum — sunny with some clouds, heavy
rain, blizzard — declared once and referenced from any terrain that can have
it. It carries the effects it contributes while it is active, and two optional
strings the consumer may render.

The library never renders either string, never decides when they are shown and
never compares them. What a weather's values mean, and when its text appears,
are the consumer's.

``WeatherType`` validates itself on construction and raises there rather than
collecting, as ``EnvironmentEffectType`` does: the declaration is a line in the
consumer's own module, and the traceback should point at it.

**It does not check its effect keys against the master list.** A weather may be
declared before the effects it names are registered — both happen in the
consumer's module, in whatever order they wrote them — so refusing here would
reject a declaration that is correct by the time the game boots. That check
belongs with boot validation.

See docs/test-plan.md § WT.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class WeatherType:
    """One weather a consumer's game can have. See docs/test-plan.md § WT."""

    key: str
    effects: Mapping[str, Any]
    description: Optional[str] = None
    transition_in: Optional[str] = None

    def __post_init__(self):
        """Refuse a declaration that cannot be used, naming the key.

        Every refusal is a ``ValueError``, as ``EnvironmentEffectType``'s are: each
        one means the same thing to a consumer — you declared this wrong — and
        one class is easier to catch than a type per mistake.
        """
        if not isinstance(self.key, str):
            raise ValueError(
                f"WeatherType key {self.key!r} is a {type(self.key).__name__}, "
                f"not a string. A weather is looked up by name, so its key has "
                f"to be one."
            )

        # Nothing constrains the key past this. A space is legal, as it is for
        # an effect key: the key is a mapping handle, and a player sees
        # description and transition_in rather than this.
        if not self.key:
            raise ValueError(
                "WeatherType key is empty. Without a key the weather names "
                "nothing and no terrain slot can hold it."
            )

        # A Mapping rather than a dict, so anything that reads like one will
        # do. A list of pairs will not: it can carry the same effect key twice,
        # and one of the two would be silently ignored.
        if not isinstance(self.effects, Mapping):
            raise ValueError(
                f"Weather {self.key!r} declares effects as a "
                f"{type(self.effects).__name__}, which is not a mapping. Pass "
                f"effect key to value — an empty mapping if the weather "
                f"contributes nothing, which is an ordinary weather rather "
                f"than a mistake."
            )

        # The strings are opaque and optional: all that is checked is that
        # there is text to render, or None saying there is not.
        for name, value in (
            ("description", self.description),
            ("transition_in", self.transition_in),
        ):
            if value is None:
                continue

            if not isinstance(value, str):
                raise ValueError(
                    f"Weather {self.key!r} declares {name} as a "
                    f"{type(value).__name__}. It is text the consumer renders, "
                    f"so it has to be a string, or None for none at all."
                )
