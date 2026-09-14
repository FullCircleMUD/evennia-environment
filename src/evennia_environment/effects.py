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

import inspect
import typing
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


def _rejects_helper_arguments(helper):
    """Return why ``helper`` cannot be called as one, or ``None``.

    Every contribution is called as ``helper(value, **kwargs)`` — the running
    value positionally, and whatever the call site passed by name. Both halves
    are checkable at the declaration with ``inspect``, without calling
    anything, which turns a crash in play into a refusal at the line that wrote
    it.
    """
    if not callable(helper):
        return (
            f"{helper!r} is a {type(helper).__name__} and cannot be called. A "
            f"default is a helper, not an answer — wrap a fixed answer in one."
        )

    try:
        parameters = inspect.signature(helper).parameters.values()
    except (TypeError, ValueError):
        # A builtin or a C callable may have no introspectable signature. Take
        # it at its word rather than refusing something that would work.
        return None

    takes_value = any(
        p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)
        for p in parameters
    )
    if not takes_value:
        return (
            f"{helper!r} takes no positional argument. A helper is handed the "
            f"running value first, even when it ignores it."
        )

    takes_kwargs = any(p.kind is p.VAR_KEYWORD for p in parameters)
    if not takes_kwargs:
        return (
            f"{helper!r} has no **kwargs. Whatever a call site passes is handed "
            f"to every helper, so one has to accept them even to ignore them."
        )

    return None


@dataclass(frozen=True)
class EnvironmentEffectType:
    """One kind of effect a consumer's game reads. See docs/test-plan.md § EF.

    ``return_type`` describes what a helper hands back, so it is checked
    against an answer at the call rather than against anything declared here.
    ``default`` answers when neither terrain nor weather declares this key.
    ``requires`` names the kwargs a call site has to supply for it.
    """

    key: str
    return_type: type
    default: Callable
    requires: tuple = ()

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

        # ``Any`` is refused by name because it would otherwise pass the check
        # below — isinstance(Any, type) is True — and then raise TypeError the
        # first time an answer was checked against it. A clean boot and a crash
        # in play is the outcome these checks exist to prevent.
        if self.return_type is typing.Any:
            raise ValueError(
                f"EnvironmentEffectType {self.key!r} declares a return type of "
                f"typing.Any, which cannot be used with isinstance. Declare "
                f"object instead — every answer satisfies it."
            )

        # ``isinstance`` would raise ``TypeError`` rather than answering if
        # return_type is not a type, so this check has to come first.
        if not isinstance(self.return_type, type):
            raise ValueError(
                f"EnvironmentEffectType {self.key!r} declares a return type of "
                f"{self.return_type!r}, which is a "
                f"{type(self.return_type).__name__} rather than a type. Pass "
                f"the type itself — float, not \"float\"."
            )

        refusal = _rejects_helper_arguments(self.default)
        if refusal:
            raise ValueError(
                f"EnvironmentEffectType {self.key!r} declares a default that "
                f"{refusal}"
            )

        # A bare string is iterable, so ``requires="actor"`` would pass a naive
        # check and then quietly require five kwargs named a, c, t, o and r.
        if isinstance(self.requires, str) or not isinstance(
            self.requires, (tuple, list)
        ):
            raise ValueError(
                f"EnvironmentEffectType {self.key!r} declares requires as "
                f"{self.requires!r}. It names the kwargs a call site must pass, "
                f"so it is a tuple of names — ('actor',), not 'actor'."
            )

        not_names = [name for name in self.requires if not isinstance(name, str)]
        if not_names:
            raise ValueError(
                f"EnvironmentEffectType {self.key!r} declares requires "
                f"containing {not_names!r}. Every entry is a kwarg name, so "
                f"every entry is a string."
            )

        # Normalised so the stored value is always a tuple, whatever was
        # passed. object.__setattr__ because the dataclass is frozen.
        object.__setattr__(self, "requires", tuple(self.requires))


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

        # The key is the identity. A default is a helper, and two
        # separately-written declarations hold different function objects even
        # when they read identically — so "is this the same declaration" has no
        # answer worth trusting, and a second one under a taken key means one of
        # them is being ignored either way.
        existing = self._effect_types.get(effect_type.key)
        if existing is not None:
            raise ValueError(
                f"EnvironmentEffectType {effect_type.key!r} is already "
                f"registered as {existing!r}. One key is one effect type; "
                f"remove whichever declaration is wrong."
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
    """A declared effect type, and the helper that answers for it.

    The type says ``move_cost`` is a float defaulting to ``Constant(1.0)``;
    this says what one swamp, or one blizzard, does about it. Terrain and
    weather both hold these, so neither invents a payload format.

    **Declared means changed.** A terrain or weather only declares the keys it
    wants different from the default; silence leaves the default's answer
    standing.

    See docs/test-plan.md § EE.
    """

    effect_type: EnvironmentEffectType
    helper: Callable

    def __post_init__(self):
        """Refuse a declaration that cannot be used, naming the key.

        Every refusal is a ``ValueError``, as the type's are: one class for
        "you declared this wrong" is easier to catch than a type per mistake.
        """
        # First, so the refusal below has a key to name.
        if not isinstance(self.effect_type, EnvironmentEffectType):
            raise ValueError(
                f"EnvironmentEffect was given {self.effect_type!r} as its "
                f"effect type, which is a {type(self.effect_type).__name__} "
                f"rather than an EnvironmentEffectType. Pass the declared type "
                f"itself, not its key."
            )

        # The same check the type applies to its own default, so a helper that
        # would crash at the first call is refused at the line declaring it.
        # Nothing here looks at what it returns: return_type is checked against
        # an answer on the call path, where it covers every contribution.
        refusal = _rejects_helper_arguments(self.helper)
        if refusal:
            raise ValueError(
                f"EnvironmentEffect for {self.effect_type.key!r} declares a "
                f"helper that {refusal}"
            )


def one_effect_per_type(effects, declared_by):
    """Return ``effects`` as a tuple, refusing anything that is not usable.

    Shared by whatever holds a collection of them — a weather and a terrain
    both declare one, and the rule written twice is the rule that drifts.

    Args:
        effects: what the consumer declared.
        declared_by (str): names the declaration in a refusal, e.g.
            ``"Weather 'blizzard'"``.

    Returns:
        tuple: the effects, in the order declared.

    Raises:
        ValueError: if it cannot be iterated, holds something that is not an
            ``EnvironmentEffect``, or declares two for one effect type.
    """
    # A bare EnvironmentEffect is iterable of nothing useful and a string is
    # iterable of characters, so both are refused by name rather than being
    # walked into something confusing.
    if isinstance(effects, (str, EnvironmentEffect)) or not isinstance(
        effects, (tuple, list)
    ):
        raise ValueError(
            f"{declared_by} declares effects as {effects!r}. It is a tuple of "
            f"EnvironmentEffect — an empty one if nothing is declared."
        )

    seen = {}
    for effect in effects:
        if not isinstance(effect, EnvironmentEffect):
            raise ValueError(
                f"{declared_by} declares {effect!r} among its effects, which "
                f"is a {type(effect).__name__} rather than an "
                f"EnvironmentEffect."
            )

        # One per type is what keeps the resolution chain to two links, so
        # there is no ordering to configure and no merge rule to write.
        key = effect.effect_type.key
        if key in seen:
            raise ValueError(
                f"{declared_by} declares two effects for {key!r}. One "
                f"declaration per effect type: the second would be ignored, "
                f"whether or not it says the same thing."
            )
        seen[key] = effect

    return tuple(effects)


# The list a consumer registers against, from the module they declare their game
# in. One instance, because one game has one master list.
ENVIRONMENT_EFFECT_TYPES = EnvironmentEffectTypeRegistry()
