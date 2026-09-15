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

import hashlib
from dataclasses import dataclass, field
from typing import Optional

from evennia_environment.config import BAND_FLOOR, BANDS, SEASON_SHIFT
from evennia_environment.effects import one_effect_per_type
from evennia_environment.refusal import refuse


@dataclass(frozen=True)
class WeatherSlot:
    """One of a terrain's ten slots: what occurs there, day and night.

    See docs/test-plan.md § WS.
    """

    day: "WeatherType"
    night: Optional["WeatherType"] = None

    def __post_init__(self):
        """Refuse a slot that cannot be used, and fill night from day.

        Filling ``night`` here rather than leaving it ``None`` is what keeps
        the rest of the library free of absence checks: whatever resolves the
        active weather asks for day or night and gets a weather type either
        way. It also makes "does this slot differ at night" answerable as
        ``slot.night is slot.day``, with no flag to carry.
        """
        if not isinstance(self.day, WeatherType):
            refuse(
                f"WeatherSlot was given {self.day!r} as its day weather, which "
                f"is a {type(self.day).__name__} rather than a WeatherType. "
                f"Pass the declared weather itself, not its key."
            )

        if self.night is None:
            object.__setattr__(self, "night", self.day)
            return

        if not isinstance(self.night, WeatherType):
            refuse(
                f"WeatherSlot for {self.day.key!r} was given {self.night!r} as "
                f"its night weather, which is a {type(self.night).__name__} "
                f"rather than a WeatherType. Leave it out for a slot that does "
                f"not change after dark."
            )


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
            refuse(
                f"WeatherType key {self.key!r} is a {type(self.key).__name__}, "
                f"not a string. A weather is looked up by name, so its key has "
                f"to be one."
            )

        # Nothing constrains the key past this. A space is legal, as it is for
        # an effect key: the key is a mapping handle, and a player sees
        # description and transition_in rather than this.
        if not self.key:
            refuse(
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
                refuse(
                    f"Weather {self.key!r} declares {name} as a "
                    f"{type(value).__name__}. It is text the consumer renders, "
                    f"so it has to be a string, or None for none at all."
                )


#: Today's band and the day it was worked out for. Module state, rebuilt on
#: the next rollover or the next read — nothing about a band depends on it
#: surviving, and a reload restarts the process anyway.
_held_band = None
_held_day = None


def weather_band(day, season, seed=""):
    """Return the band for ``day`` in ``season``, one to ten.

    Derived rather than rolled: the same day and seed always give the same
    number, so nothing is stored and no two processes have to agree on
    anything. Any day past or future can be asked for.

    Args:
        day (int): the day being asked about.
        season (Season): the season it falls in. Required rather than
            defaulted — a band without one is not meaningful, and a
            ``GameDate`` carries both, so working one out costs a single call.
        seed (str): the game's weather seed. Changing it rerolls a world's
            entire weather history.

    Returns:
        int: the band, 1 to 10.
    """
    # hashlib rather than hash(): the builtin is randomised per process for
    # strings, so two processes would disagree about the weather, and it is the
    # identity for small ints, so hash(day) % 6 is a metronome rather than
    # weather. Eight bytes is a machine word and plenty of mixing.
    digest = hashlib.sha256(f"{seed}:{day}".encode()).digest()
    return (
        int.from_bytes(digest[:8], "big") % BANDS
        + BAND_FLOOR
        + SEASON_SHIFT[season]
    )


def current_weather_band():
    """Return today's band, held between rollovers.

    Computed by ``day_changed`` when the clock is running, and on the first
    read when nothing is held — which is what answers between a restart and
    the next rollover.
    """
    if _held_band is None:
        refresh_weather_band()

    return _held_band


def game_date():
    """Return the calendar's current date.

    Wrapped rather than imported at module scope: importing it pulls Evennia
    and reads settings, and this module is re-exported from ``__init__.py``,
    which runs while Django is still building its app registry.
    """
    from evennia_calendar import game_date as _from_calendar

    return _from_calendar()


def refresh_weather_band(sender=None, **kwargs):
    """Recompute and hold today's band. Connected to ``day_changed``.

    One calculation, two triggers: the signal when the clock is running, and a
    read that finds nothing held. Asking the calendar what day it is costs
    seven times what hashing it does, so the saving is in not asking on every
    read rather than in caching the hash.
    """
    global _held_band, _held_day

    from evennia_environment.config import weather_seed

    # One call: the date carries the day and the season both.
    date = game_date()
    _held_day = date.day_of_year
    _held_band = weather_band(date.day_of_year, date.season, weather_seed())


#: Whether the current watch is dark, and the watch it was worked out for.
#: Module state, rebuilt on the next watch or the next read.
_held_dark = None
_held_phase = None


def is_dark():
    """Return whether the current watch is one the consumer declared dark.

    Held between watches: ``phase_changed`` refreshes it, and a read computes
    it when nothing is held — which is what answers between a restart and the
    next watch.
    """
    if _held_dark is None:
        refresh_is_dark()

    return _held_dark


def refresh_is_dark(sender=None, **kwargs):
    """Recompute and hold whether it is dark. Connected to ``phase_changed``.

    One calculation, two triggers, as the band has: the signal when the clock
    is running, and a read that finds nothing held.
    """
    global _held_dark, _held_phase

    from evennia_environment.config import dark_watches

    _held_phase = game_date().phase
    _held_dark = _held_phase in dark_watches()


def current_weather(terrain_type, dark=None):
    """Return the weather in force for ``terrain_type``.

    The band names the slot — both run 1 to 10 — and the slot answers with its
    day or night weather.

    Args:
        terrain_type (TerrainType): the terrain whose slots to read.
        dark (bool): forces night when true and day when false. Worked out
            from the current watch when not given.

    Returns:
        WeatherType: the weather in force.
    """
    # The band is the slot number — both run 1 to 10 — so a terrain's slots
    # are indexed by it directly and there is nothing to map.
    slot = terrain_type.weather_slots[current_weather_band() - 1]

    if dark is None:
        dark = is_dark()

    # Both are always populated: WeatherSlot fills night from day when none
    # was declared, so this never has to test for absence.
    return slot.night if dark else slot.day
