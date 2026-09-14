# SPDX-License-Identifier: BSD-3-Clause
"""Effect types, the list they go in, and an effect type with a magnitude.

An effect type is a named thing a room's surroundings can change — what it is
called, what type its values are in, and what something that says nothing about
it gives. The library never invents one: a consumer declares every effect type
their game reads, and terrains are validated against that list.

An ``EnvironmentEffect`` is a type paired with a magnitude. The type says
``movement_cost`` is a float defaulting to 1.0; the effect says a swamp makes
it 2.5. Terrain and weather both hold these, so neither invents a payload
format of its own.

Everything here validates itself on construction and raises there rather than
collecting. A malformed declaration is the consumer's own code failing at their
own line, and a traceback pointing at that line is worth more than a tidy list
pointing at us. ``EnvironmentEffectTypeRegistry`` applies the same rule to
registering a type.

**The registry holds no magnitudes.** A key's datatype and its default are all
it carries — the value for a room comes from its terrain, and the registry
supplies the fallback when the terrain declares nothing for that key.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class EnvironmentEffectType:
    """One kind of effect a consumer's game reads. See docs/test-plan.md § EF."""

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
                f"EnvironmentEffectType key {self.key!r} is a "
                f"{type(self.key).__name__}, not a string. An effect type is "
                f"looked up by name, so its key has to be one."
            )

        if not self.key:
            raise ValueError(
                "EnvironmentEffectType key is empty. Without a key the effect "
                "type names nothing and no terrain can declare a value for it."
            )

        # ``isinstance`` below would raise ``TypeError`` rather than answering if
        # datatype is not a type, so this check has to come first.
        if not isinstance(self.datatype, type):
            raise ValueError(
                f"EnvironmentEffectType {self.key!r} declares datatype "
                f"{self.datatype!r}, which is a {type(self.datatype).__name__} "
                f"rather than a type. Pass the type itself — float, not \"float\"."
            )

        # ``None`` is the one exemption: a consumer may want a key whose default
        # means "unset", and what that means is decided in the code that reads
        # the value rather than here.
        if self.default is None:
            return

        if not isinstance(self.default, self.datatype):
            raise ValueError(
                f"EnvironmentEffectType {self.key!r} declares datatype "
                f"{self.datatype.__name__} and a default of {self.default!r}, "
                f"which is a {type(self.default).__name__}. The default is taken "
                f"as declared and never converted, so write it in the type you "
                f"asked for."
            )


class EnvironmentEffectTypeRegistry:
    """The master list of effect types a consumer has declared.

    Two jobs, and no more: say whether a key is registered, so a terrain's
    declarations can be validated against the list, and hand back the
    ``EnvironmentEffectType`` so a caller can read its default. See
    docs/test-plan.md § ER.
    """

    def __init__(self):
        self._effect_types = {}

    def register(self, effect_type: EnvironmentEffectType) -> None:
        """Add an effect type to the list, refusing a key already spoken for.

        Raises immediately rather than collecting, for the same reason
        ``EnvironmentEffectType`` does: the call is in the consumer's own
        module, at a line they wrote, and the traceback should point there.
        """
        if not isinstance(effect_type, EnvironmentEffectType):
            raise ValueError(
                f"Cannot register {effect_type!r}: register() takes an "
                f"EnvironmentEffectType, not a {type(effect_type).__name__}."
            )

        # Registering the same declaration twice is harmless — a module imported
        # again, a consumer re-running their declarations — so it passes and
        # changes nothing. Two *different* effect types under one key means one
        # of them is being silently ignored, which is worth refusing.
        existing = self._effect_types.get(effect_type.key)
        if existing is not None:
            if existing == effect_type:
                return
            raise ValueError(
                f"EnvironmentEffectType {effect_type.key!r} is already "
                f"registered as {existing!r} and cannot be redeclared as "
                f"{effect_type!r}. One of the two declarations would be "
                f"ignored; remove whichever is wrong."
            )

        self._effect_types[effect_type.key] = effect_type

    def get(self, key: str) -> Optional[EnvironmentEffectType]:
        """Return the effect type registered under ``key``, or ``None``.

        ``None`` is an ordinary answer rather than a failure: validating a
        terrain means asking about keys that may not be registered, and that is
        the question being asked.
        """
        return self._effect_types.get(key)


@dataclass(frozen=True)
class EnvironmentEffect:
    """A declared effect type, and what something gives for it.

    The type says ``movement_cost`` is a float defaulting to 1.0; this says
    that a swamp, or a blizzard, makes it 2.5. Terrain and weather both hold
    these, so neither invents a payload format of its own.

    See docs/test-plan.md § EE.
    """

    effect_type: EnvironmentEffectType
    magnitude: Any

    def __post_init__(self):
        """Refuse a declaration that cannot be used, naming the key.

        Every refusal is a ``ValueError``, as the type's are: one class for
        "you declared this wrong" is easier to catch than a type per mistake.
        """
        # First, so the two checks below can read the datatype and the key off
        # a type that is really one.
        if not isinstance(self.effect_type, EnvironmentEffectType):
            raise ValueError(
                f"EnvironmentEffect was given {self.effect_type!r} as its "
                f"effect type, which is a {type(self.effect_type).__name__} "
                f"rather than an EnvironmentEffectType. Pass the declared type "
                f"itself, not its key."
            )

        # ``None`` is exempt for a type's default, because "no default" is a
        # real state. "No magnitude" is not one: something that does not touch
        # an effect leaves it out of its collection, so omission already says
        # so, and a second way to say nothing would have to be handled
        # everywhere a magnitude is read.
        if self.magnitude is None:
            raise ValueError(
                f"EnvironmentEffect for {self.effect_type.key!r} has a "
                f"magnitude of None. Leave the effect out altogether to say it "
                f"contributes nothing."
            )

        if not isinstance(self.magnitude, self.effect_type.datatype):
            raise ValueError(
                f"EnvironmentEffect for {self.effect_type.key!r} has a "
                f"magnitude of {self.magnitude!r}, which is a "
                f"{type(self.magnitude).__name__} rather than the "
                f"{self.effect_type.datatype.__name__} its type declares. The "
                f"magnitude is taken as written and never converted."
            )


# The list a consumer registers against, from the module they declare their game
# in. One instance, because one game has one master list.
ENVIRONMENT_EFFECT_TYPES = EnvironmentEffectTypeRegistry()
