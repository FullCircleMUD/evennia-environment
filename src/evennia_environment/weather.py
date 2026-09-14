# SPDX-License-Identifier: BSD-3-Clause
"""The shape a consumer declares one weather in.

A weather is one entry in a game's spectrum — sunny with some clouds, heavy
rain, blizzard — declared once and referenced from any terrain that can have
it. It carries the effects it declares, and two optional strings the consumer
may render.

**Declaring nothing is normal.** A weather only declares the keys it wants
different from the default; silence leaves the default's answer standing, so
the mild end of a spectrum is an empty declaration rather than a list of
no-ops.

The library never renders either string, never decides when they are shown and
never compares them. What a weather's values mean, and when its text appears,
are the consumer's.

See docs/test-plan.md § WT.
"""

from dataclasses import dataclass, field
from typing import Optional

from evennia_environment.effects import one_effect_per_type


@dataclass(frozen=True)
class WeatherType:
    """One weather a consumer's game can have. See docs/test-plan.md § WT.

    ``effects`` is a tuple of ``EnvironmentEffect`` rather than a mapping: each
    entry carries its own type, so the key lives in one place and cannot
    disagree with what is filed under it. Held as a tuple whatever was passed,
    because effects resolve at read time and a mutable collection here would
    change every room using this weather.
    """

    key: str
    effects: tuple = ()
    description: Optional[str] = None
    transition_in: Optional[str] = None

    def __post_init__(self):
        """Refuse a declaration that cannot be used, naming the key.

        Every refusal is a ``ValueError``, as the effect types' are: each one
        means the same thing to a consumer — you declared this wrong — and one
        class is easier to catch than a type per mistake.
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

        object.__setattr__(
            self,
            "effects",
            one_effect_per_type(self.effects, f"Weather {self.key!r}"),
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
