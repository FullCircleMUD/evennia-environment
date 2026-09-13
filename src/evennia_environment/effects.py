# SPDX-License-Identifier: BSD-3-Clause
"""The shape a consumer declares one effect in, and the list they declare it to.

An effect is a named thing a terrain can change about a room — what it is
called, what type its values are in, and what a terrain that says nothing about
it gives. The library never invents one: a consumer declares every effect their
game reads, and terrains are validated against that list.

``Effect`` validates itself on construction and raises there rather than
collecting. A malformed declaration is the consumer's own code failing at their
own line, and a traceback pointing at that line is worth more than a tidy list
pointing at us. ``EffectRegistry`` holds the declarations and applies the same
rule to registering them.

**The registry holds no values.** A key's datatype and its default are all it
carries — the value for a room comes from its terrain, and the registry supplies
the fallback when the terrain declares nothing for that key.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Effect:
    """One effect a consumer's game reads. See docs/test-plan.md § EF."""

    key: str
    datatype: type
    default: Any

    def __post_init__(self):
        """Refuse a declaration that cannot be used, naming the key.

        Every refusal is a ``ValueError``: each one means the same thing to a
        consumer — you declared this wrong — and one class is easier to catch
        than a type per mistake.
        """
        if not isinstance(self.key, str):
            raise ValueError(
                f"Effect key {self.key!r} is a {type(self.key).__name__}, not a string. "
                f"An effect is looked up by name, so its key has to be one."
            )

        if not self.key:
            raise ValueError(
                "Effect key is empty. Without a key the effect names nothing and "
                "no terrain can declare a value for it."
            )

        # ``isinstance`` below would raise ``TypeError`` rather than answering if
        # datatype is not a type, so this check has to come first.
        if not isinstance(self.datatype, type):
            raise ValueError(
                f"Effect {self.key!r} declares datatype {self.datatype!r}, which is a "
                f"{type(self.datatype).__name__} rather than a type. Pass the type "
                f"itself — float, not \"float\"."
            )

        # ``None`` is the one exemption: a consumer may want a key whose default
        # means "unset", and what that means is decided in the code that reads
        # the value rather than here.
        if self.default is None:
            return

        if not isinstance(self.default, self.datatype):
            raise ValueError(
                f"Effect {self.key!r} declares datatype {self.datatype.__name__} and a "
                f"default of {self.default!r}, which is a "
                f"{type(self.default).__name__}. The default is taken as declared and "
                f"never converted, so write it in the type you asked for."
            )


class EffectRegistry:
    """The master list of effects a consumer has declared.

    Two jobs, and no more: say whether a key is registered, so a terrain's
    declarations can be validated against the list, and hand back the ``Effect``
    so a caller can read its default. See docs/test-plan.md § ER.
    """

    def __init__(self):
        self._effects = {}

    def register(self, effect: Effect) -> None:
        """Add an effect to the list, refusing a key already spoken for.

        Raises immediately rather than collecting, for the same reason
        ``Effect`` does: the call is in the consumer's own module, at a line
        they wrote, and the traceback should point there.
        """
        if not isinstance(effect, Effect):
            raise ValueError(
                f"Cannot register {effect!r}: register() takes an Effect, not a "
                f"{type(effect).__name__}."
            )

        # Registering the same declaration twice is harmless — a module imported
        # again, a consumer re-running their declarations — so it passes and
        # changes nothing. Two *different* effects under one key means one of
        # them is being silently ignored, which is worth refusing.
        existing = self._effects.get(effect.key)
        if existing is not None:
            if existing == effect:
                return
            raise ValueError(
                f"Effect {effect.key!r} is already registered as {existing!r} and "
                f"cannot be redeclared as {effect!r}. One of the two declarations "
                f"would be ignored; remove whichever is wrong."
            )

        self._effects[effect.key] = effect

    def get(self, key: str) -> Optional[Effect]:
        """Return the effect registered under ``key``, or ``None``.

        ``None`` is an ordinary answer rather than a failure: validating a
        terrain means asking about keys that may not be registered, and that is
        the question being asked.
        """
        return self._effects.get(key)


# The list a consumer registers against, from the module they declare their game
# in. One instance, because one game has one master list.
EFFECTS = EffectRegistry()
