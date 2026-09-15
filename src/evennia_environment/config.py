# SPDX-License-Identifier: BSD-3-Clause
"""The setting this library reads, and the boot check that refuses a bad one.

The terrains a game has reach the library as a setting naming an enum — see
``library-standards.md`` § Consumer-authored config, and the same shape as
``evennia-equipment``'s wearslots. There is no terrain list the library could
invent, so the setting has no safe default: it is validated once at boot and
the instance does not start without it::

    ENVIRONMENT_TERRAIN_ENUM = "world.environment.Terrain"

    class Terrain(Enum):
        SWAMP = "swamp"
        MOUNTAINS = "mountains"

**An enum with no members is accepted.** Booting to check an install before
writing content is a correct reading. What is refused is not declaring one.

See docs/test-plan.md § CF.
"""

from enum import Enum
from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from evennia_environment.terrain import TerrainType

SETTING_TERRAIN_ENUM = "ENVIRONMENT_TERRAIN_ENUM"
SETTING_TERRAIN_TYPES = "ENVIRONMENT_TERRAIN_TYPES"
SETTING_WEATHER_SEED = "ENVIRONMENT_WEATHER_SEED"
SETTING_DARK_WATCHES = "ENVIRONMENT_DARK_WATCHES"

#: What each collected problem is prefixed with in the refusal. One per line,
#: so a consumer with two things wrong works through a list rather than a
#: paragraph. Named so a test can count problems without pinning any wording.
PROBLEM_PREFIX = "\n  - "

_EXAMPLE = "'world.environment.Terrain'"
_TYPES_EXAMPLE = "'world.environment.TERRAINS'"
_WATCHES_EXAMPLE = "(6, 1)"

#: The calendar's day is six watches, numbered from one.
WATCHES = tuple(range(1, 7))

#: Separates problems found inside one check, so check_settings can list
#: them individually rather than as one paragraph.
_JOIN = "\x00"


def check_settings() -> None:
    """Refuse to start when the setting is missing or unusable.

    Called from ``AppConfig.ready()``.

    The checks on the setting itself are sequential — each makes the next
    meaningful, and there is nothing to import if the path is missing. The
    checks on the enum's members are collected, so a consumer with two things
    wrong in it fixes both in one pass rather than once per restart.
    """
    problems = []
    cause = None

    try:
        terrains = _checked_terrain_enum()
    except ImproperlyConfigured as exc:
        problems.extend(str(exc).split(_JOIN))
        cause = exc.__cause__
        terrains = None

    try:
        _check_terrain_types(terrains)
    except ImproperlyConfigured as exc:
        problems.extend(str(exc).split(_JOIN))

    try:
        _check_dark_watches()
    except ImproperlyConfigured as exc:
        problems.extend(str(exc).split(_JOIN))

    if problems:
        _refuse(problems, cause=cause)


def _checked_terrain_enum():
    """Return the consumer's terrain enum, or say why it cannot be used.

    Sequential rather than collected: each check makes the next meaningful, so
    only one can be wrong at a time.
    """
    from django.conf import settings

    path = getattr(settings, SETTING_TERRAIN_ENUM, None)

    # `not path` covers unset and empty together, which are the same mistake
    # from the library's side: nothing to resolve.
    if not path or not isinstance(path, str):
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_ENUM} is {path!r}. Point it at an Enum naming "
            f"every terrain your game has, e.g. {_EXAMPLE}."
        )

    try:
        # import_string rather than variable_from_module: the latter returns
        # None for a missing module, a missing name and a real None alike, so
        # a typo would arrive indistinguishable from a deliberate absence.
        terrains = import_string(path)
    except Exception as exc:
        # The module exists because this library asked for it, so its state is
        # our business to report. Chained rather than swallowed, so a consumer
        # gets both the setting that is wrong and why. Its members cannot be
        # looked at from here, and the message says so rather than implying
        # they were fine.
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_ENUM} names {path!r}, which could not be "
            f"loaded, so the terrains it declares were not examined."
        ) from exc

    if not (isinstance(terrains, type) and issubclass(terrains, Enum)):
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_ENUM} names {path!r}, which is "
            f"{type(terrains).__name__} and not an Enum. Declare your "
            f"terrains as an Enum, one member each."
        )

    member_problems = []

    # Read __members__, not the members, and read it first. Python folds a
    # repeated value into the member declared before it, so by the time the
    # members are walked the duplicate is gone and what remains looks perfectly
    # well formed.
    aliases = [
        name for name, member in terrains.__members__.items() if name != member.name
    ]
    if aliases:
        member_problems.append(
            f"{path} declares {', '.join(aliases)} with a value already in "
            f"use. Python folds each one into the member declared before it, "
            f"leaving the game short a terrain."
        )

    not_strings = sorted(
        member.name for member in terrains if not isinstance(member.value, str)
    )
    if not_strings:
        member_problems.append(
            f"{path} declares {', '.join(not_strings)} with values that are "
            f"not strings. A terrain's value is what a room stores and what "
            f"world content writes, so it has to be text."
        )

    if member_problems:
        # Collected: two things wrong inside one enum are independent, and a
        # consumer should fix both in one pass. Raised as one exception per
        # problem's worth of text, which check_settings splits back out.
        raise ImproperlyConfigured(_JOIN.join(member_problems))

    return terrains


def _check_terrain_types(terrains):
    """Refuse terrain types that are missing, unusable, or unreachable.

    ``terrains`` is the enum when it resolved and None when it did not — a key
    cannot be checked against members nobody could read.
    """
    from django.conf import settings

    path = getattr(settings, SETTING_TERRAIN_TYPES, None)

    if not path or not isinstance(path, str):
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_TYPES} is {path!r}. Point it at the TerrainType "
            f"objects your game declares, e.g. {_TYPES_EXAMPLE}."
        )

    try:
        declared = import_string(path)
    except Exception as exc:
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_TYPES} names {path!r}, which could not be "
            f"loaded."
        ) from exc

    if isinstance(declared, (str, TerrainType)) or not isinstance(
        declared, (tuple, list)
    ):
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_TYPES} names {path!r}, which is "
            f"{type(declared).__name__}. It is a tuple of TerrainType."
        )

    not_terrains = [
        repr(item) for item in declared if not isinstance(item, TerrainType)
    ]
    if not_terrains:
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_TYPES} names {path!r}, which holds "
            f"{', '.join(not_terrains)}. Every entry is a TerrainType."
        )

    if terrains is None:
        return

    # A key no member names can never be reached: a room stores a member's
    # value, so nothing could arrive at it. The reverse is fine — a member with
    # no terrain type yet is a game being written.
    named = {member.value for member in terrains}
    unreachable = sorted(
        repr(terrain.key) for terrain in declared if terrain.key not in named
    )
    if unreachable:
        raise ImproperlyConfigured(
            f"{SETTING_TERRAIN_TYPES} declares {', '.join(unreachable)}, which "
            f"no member of {terrains.__name__} names. A room stores a member's "
            f"value, so nothing could ever reach them."
        )


def _check_dark_watches():
    """Refuse dark watches that are missing or not watch numbers.

    The calendar deliberately refuses to say which of its six watches are
    dark, so the library cannot invent a default either. An empty tuple is a
    game with no night, which is a correct reading; not declaring is not.
    """
    from django.conf import settings

    declared = getattr(settings, SETTING_DARK_WATCHES, None)

    # A string is iterable, so "6,1" would otherwise be walked as characters.
    if declared is None or isinstance(declared, str) or not isinstance(
        declared, (tuple, list, set, frozenset)
    ):
        raise ImproperlyConfigured(
            f"{SETTING_DARK_WATCHES} is {declared!r}. Name the watches your "
            f"game counts as dark, as numbers — the calendar has six, so "
            f"e.g. {_WATCHES_EXAMPLE}. Declare an empty tuple for a game with "
            f"no night."
        )

    out_of_range = sorted(
        repr(watch)
        for watch in declared
        if not isinstance(watch, int) or isinstance(watch, bool)
        or watch not in WATCHES
    )
    if out_of_range:
        raise ImproperlyConfigured(
            f"{SETTING_DARK_WATCHES} names {', '.join(out_of_range)}, which "
            f"are not watches. The calendar's day is six, numbered 1 to 6."
        )


def _refuse(problems, cause=None):
    """Raise one refusal carrying every problem found.

    One problem per line, so a consumer with two things wrong works through a
    list rather than a paragraph.
    """
    raise ImproperlyConfigured(
        "evennia-environment cannot start:"
        + "".join(f"{PROBLEM_PREFIX}{problem}" for problem in problems)
    ) from cause


@lru_cache(maxsize=1)
def terrain_enum():
    """Return the consumer's terrain enum. Checked at boot.

    Resolved once and held for the life of the process: the enum comes from a
    setting naming a module, and neither settings nor an imported module can
    change while the server is up.

    A test that swaps the setting does need to clear it —
    ``terrain_enum.cache_clear()``.
    """
    from django.conf import settings

    return import_string(getattr(settings, SETTING_TERRAIN_ENUM))


@lru_cache(maxsize=1)
def terrain_types():
    """Return the consumer's terrain types, keyed by their key.

    Resolved once and held for the life of the process, as ``terrain_enum``
    is. A test that swaps the setting must call
    ``terrain_types.cache_clear()``.
    """
    from django.conf import settings

    return {
        terrain.key: terrain
        for terrain in import_string(getattr(settings, SETTING_TERRAIN_TYPES))
    }


def weather_seed() -> str:
    """Return the game's weather seed.

    A setting with a safe default, so it is not a boot check — any string
    works, and an unset one simply means every game on this calendar shares a
    sky until someone sets it. Changing it rerolls a world's entire weather
    history.
    """
    from django.conf import settings

    return getattr(settings, SETTING_WEATHER_SEED, "") or ""


@lru_cache(maxsize=1)
def dark_watches() -> frozenset:
    """Return the watches the consumer declared dark. Checked at boot.

    A test that swaps the setting must call ``dark_watches.cache_clear()``.
    """
    from django.conf import settings

    return frozenset(getattr(settings, SETTING_DARK_WATCHES))
