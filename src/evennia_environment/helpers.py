# SPDX-License-Identifier: BSD-3-Clause
"""Helpers a consumer would otherwise write for themselves.

Tools, not a vocabulary. A consumer uses these, ignores them, or mixes them
with their own functions, and nothing here restricts what an effect may do.

Every one satisfies the helper contract — ``f(value, **kwargs) -> value`` — so
they go anywhere a helper goes, including as an effect type's ``default``.
They are classes rather than closures so they carry a readable ``repr``,
compare equal to their like, and validate their arguments at construction.

See docs/test-plan.md § SH.
"""

import math
from dataclasses import dataclass
from typing import Any

from evennia_environment.effects import rejects_helper_arguments
from evennia_environment.refusal import refuse


@dataclass(frozen=True)
class Constant:
    """Return a fixed value, whatever came before. See § SH."""

    value: Any

    def __call__(self, value, **kwargs):
        """Return the declared value, ignoring everything handed in.

        Ignoring the running value is what makes a declaration an override
        rather than a modification.
        """
        return self.value


@dataclass(frozen=True)
class Multiply:
    """Scale what was handed in. See § SH."""

    factor: Any

    def __post_init__(self):
        _refuse_a_non_number(self.factor, "Multiply", "factor")

    def __call__(self, value, **kwargs):
        """Return what was handed in, scaled."""
        return value * self.factor


@dataclass(frozen=True)
class Add:
    """Offset what was handed in. See § SH."""

    amount: Any

    def __post_init__(self):
        _refuse_a_non_number(self.amount, "Add", "amount")

    def __call__(self, value, **kwargs):
        """Return what was handed in, offset."""
        return value + self.amount


@dataclass(frozen=True)
class RoundUp:
    """Return the whole number at or above what was handed in. See § SH."""

    def __call__(self, value, **kwargs):
        """Round up. From a negative, up means toward zero."""
        return math.ceil(value)


@dataclass(frozen=True)
class RoundDown:
    """Return the whole number at or below what was handed in. See § SH."""

    def __call__(self, value, **kwargs):
        """Round down. From a negative, down means away from zero."""
        return math.floor(value)


class Chain:
    """Run helpers in order, each handed what the one before returned.

    A helper itself, so it goes anywhere one goes. See § SH.
    """

    def __init__(self, *helpers):
        """Hold the helpers, refusing one that cannot be called as one.

        Checked here rather than when the chain runs, so a bad member is a
        refusal at the line that declared it rather than a crash part-way
        through a call.
        """
        for helper in helpers:
            refusal = rejects_helper_arguments(helper)
            if refusal:
                refuse(f"Chain was given a member that {refusal}")

        self._helpers = helpers

    def __call__(self, value, **kwargs):
        """Run each helper in turn, handing on what the last one returned.

        An empty chain returns what it was handed — the written form of
        "nothing happens here".
        """
        for helper in self._helpers:
            value = helper(value, **kwargs)

        return value

    def __repr__(self):
        return f"Chain({', '.join(repr(h) for h in self._helpers)})"


def _refuse_a_non_number(value, helper, field):
    """Raise unless ``value`` is a number worth doing arithmetic with.

    ``bool`` is refused rather than treated as a number: it subclasses ``int``,
    so ``isinstance(True, int)`` is ``True`` and a plain numeric check would
    take ``Multiply(True)`` and quietly scale by one.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        refuse(
            f"{helper} was given {value!r} as its {field}, which is a "
            f"{type(value).__name__}. It has to be a number."
        )
