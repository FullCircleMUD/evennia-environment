# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for evennia-environment, run via ``python runtests.py``.

Every case the library commits to lives in docs/test-plan.md, and every test
function here carries its case ID as its docstring so the trail reads both ways.
"""

import dataclasses
from unittest import TestCase, mock

# The TP cases create real objects, so they need a database around them. The
# rest are pure Python and stay on the lighter base.
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase as DjangoTestCase
from django.test import override_settings

from evennia_environment.config import (
    PROBLEM_PREFIX,
    SETTING_DARK_WATCHES,
    SETTING_TERRAIN_ENUM,
    SETTING_TERRAIN_TYPES,
    check_settings,
    dark_watches,
    terrain_enum,
    terrain_types,
)

import evennia_environment
from evennia_environment import (
    Add,
    Chain,
    Constant,
    EnvironmentEffect,
    EnvironmentEffectType,
    EnvironmentEffectTypeRegistry,
    Multiply,
    RoundDown,
    RoundUp,
    TerrainType,
    WeatherSlot,
    WeatherType,
    current_weather,
    current_weather_band,
    is_dark,
    resolve,
    weather_band,
)


class ScaffoldTests(TestCase):
    """The install and the test runner work end to end."""

    def test_sc_01_package_imports_and_reports_its_version(self):
        """SC-01"""
        self.assertEqual(evennia_environment.__version__, "0.0.1")


def _constant(answer):
    """A helper of the shape every contribution takes, for the cases below."""

    def _helper(value, **kwargs):
        return answer

    return _helper


class EffectTypeConstructionTests(TestCase):
    """EF-01 — EF-02. What a valid declaration gives back."""

    def test_ef_01_carries_its_key_return_type_default_and_requires(self):
        """EF-01"""
        default = _constant(1.0)
        effect_type = EnvironmentEffectType(
            key="movement_cost",
            return_type=float,
            default=default,
            requires=("actor",),
        )

        self.assertEqual(effect_type.key, "movement_cost")
        self.assertIs(effect_type.return_type, float)
        self.assertIs(effect_type.default, default)
        self.assertEqual(effect_type.requires, ("actor",))

    def test_ef_02_is_frozen(self):
        """EF-02"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", return_type=float, default=_constant(1.0)
        )

        with self.assertRaises(dataclasses.FrozenInstanceError):
            effect_type.default = _constant(2.0)


class EffectTypeKeyTests(TestCase):
    """EF-03 — EF-04. The key names the effect type, so it has to be a name."""

    def test_ef_03_refuses_a_key_that_is_not_a_string(self):
        """EF-03"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key=42, return_type=float, default=_constant(1.0))

    def test_ef_04_refuses_an_empty_key(self):
        """EF-04"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key="", return_type=float, default=_constant(1.0))


class EffectTypeReturnTypeTests(TestCase):
    """EF-05, EF-13 — EF-14. What a helper must hand back."""

    def test_ef_05_refuses_a_return_type_that_is_not_a_type(self):
        """EF-05"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(
                key="movement_cost", return_type="float", default=_constant(1.0)
            )

    def test_ef_13_refuses_typing_any(self):
        """EF-13"""
        from typing import Any

        with self.assertRaises(ValueError) as caught:
            EnvironmentEffectType(
                key="movement_cost", return_type=Any, default=_constant(1.0)
            )

        # Any passes isinstance(Any, type) and then raises TypeError at the
        # first answer, so the refusal has to name the way out.
        self.assertIn("object", str(caught.exception))

    def test_ef_14_accepts_object_as_the_anything_declaration(self):
        """EF-14"""
        effect_type = EnvironmentEffectType(
            key="mood", return_type=object, default=_constant("calm")
        )

        self.assertIs(effect_type.return_type, object)


class EffectTypeDefaultTests(TestCase):
    """EF-15 — EF-17. The default is a helper, and takes what helpers take."""

    def test_ef_15_refuses_a_default_that_is_not_callable(self):
        """EF-15"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key="movement_cost", return_type=float, default=1.0)

    def test_ef_16_refuses_a_default_that_cannot_take_the_running_value(self):
        """EF-16"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(
                key="movement_cost", return_type=float, default=lambda: 2.0
            )

    def test_ef_17_refuses_a_default_that_cannot_take_the_kwargs(self):
        """EF-17"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(
                key="movement_cost", return_type=float, default=lambda value: 2.0
            )


class EffectTypeRequiresTests(TestCase):
    """EF-18 — EF-19. What a call site has to supply for this key."""

    def test_ef_18_requires_defaults_to_empty(self):
        """EF-18"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", return_type=float, default=_constant(1.0)
        )

        self.assertEqual(tuple(effect_type.requires), ())

    def test_ef_19_refuses_a_requires_that_is_not_names(self):
        """EF-19"""
        for not_names in ("actor", 42, (42,), (None,)):
            with self.subTest(requires=not_names):
                with self.assertRaises(ValueError):
                    EnvironmentEffectType(
                        key="movement_cost",
                        return_type=float,
                        default=_constant(1.0),
                        requires=not_names,
                    )


class EffectTypeRefusalTests(TestCase):
    """EF-12. Every refusal is one exception class, and it names the key."""

    def test_ef_12_every_refusal_is_a_value_error_naming_the_key(self):
        """EF-12"""
        bad_declarations = (
            {"key": 42, "return_type": float, "default": _constant(1.0)},
            {"key": "", "return_type": float, "default": _constant(1.0)},
            {"key": "movement_cost", "return_type": "float", "default": _constant(1.0)},
            {"key": "movement_cost", "return_type": float, "default": 1.0},
            {
                "key": "movement_cost",
                "return_type": float,
                "default": _constant(1.0),
                "requires": (42,),
            },
        )

        for declaration in bad_declarations:
            with self.subTest(declaration=declaration):
                with self.assertRaises(ValueError) as caught:
                    EnvironmentEffectType(**declaration)
                # A key that is not a string still has to appear, so the
                # consumer can find the declaration that is wrong.
                self.assertIn(str(declaration["key"]), str(caught.exception))


class StockHelperConstantTests(TestCase):
    """SH-01 — SH-02. A fixed answer, whatever came before."""

    def test_sh_01_returns_its_own_value_ignoring_what_came_before(self):
        """SH-01"""
        self.assertEqual(Constant(2.0)(99.0), 2.0)

    def test_sh_02_carries_a_value_of_any_type(self):
        """SH-02"""
        for answer in ("bare", True, None, ("a", "b")):
            with self.subTest(value=answer):
                self.assertEqual(Constant(answer)(1.0), answer)


class StockHelperArithmeticTests(TestCase):
    """SH-03 — SH-06. Scaling and offsetting what was handed in."""

    def test_sh_03_multiply_scales_what_it_was_handed(self):
        """SH-03"""
        self.assertEqual(Multiply(1.5)(2.0), 3.0)

    def test_sh_04_multiply_refuses_a_factor_that_is_not_a_number(self):
        """SH-04"""
        # True is refused deliberately: isinstance(True, int) is True, so a
        # plain numeric check would take it and scale by one.
        for factor in ("1.5", None, True, ("1.5",)):
            with self.subTest(factor=factor):
                with self.assertRaises(ValueError):
                    Multiply(factor)

    def test_sh_05_add_offsets_what_it_was_handed(self):
        """SH-05"""
        self.assertEqual(Add(0.5)(2.0), 2.5)

    def test_sh_06_add_refuses_an_amount_that_is_not_a_number(self):
        """SH-06"""
        for amount in ("0.5", None, True, ("0.5",)):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    Add(amount)


class StockHelperRoundingTests(TestCase):
    """SH-07 — SH-08. Landing back on a whole number."""

    def test_sh_07_round_up_goes_up_and_returns_an_int(self):
        """SH-07"""
        self.assertEqual(RoundUp()(2.1), 3)
        self.assertIsInstance(RoundUp()(2.1), int)
        self.assertEqual(RoundUp()(3.0), 3)
        # Up from a negative means toward zero.
        self.assertEqual(RoundUp()(-1.5), -1)

    def test_sh_08_round_down_goes_down_and_returns_an_int(self):
        """SH-08"""
        self.assertEqual(RoundDown()(2.9), 2)
        self.assertIsInstance(RoundDown()(2.9), int)
        self.assertEqual(RoundDown()(3.0), 3)
        # Down from a negative means away from zero.
        self.assertEqual(RoundDown()(-1.5), -2)


class StockHelperChainTests(TestCase):
    """SH-09 — SH-12. Composing helpers in order."""

    def test_sh_09_runs_its_helpers_left_to_right(self):
        """SH-09"""
        # 2.0 -> x1.5 -> 3.0 -> +0.6 -> 3.6 -> up -> 4
        self.assertEqual(Chain(Multiply(1.5), Add(0.6), RoundUp())(2.0), 4)

        # Order is proved by reversing it: up first gives 2 -> 3.0 -> 3.6.
        self.assertEqual(Chain(RoundUp(), Multiply(1.5), Add(0.6))(2.0), 3.6)

    def test_sh_10_passes_the_kwargs_to_every_member(self):
        """SH-10"""
        seen = []

        def _watching(value, **kwargs):
            seen.append(kwargs)
            return value

        Chain(_watching, _watching)(1.0, actor="someone", door="a door")

        self.assertEqual(
            seen, [{"actor": "someone", "door": "a door"}] * 2
        )

    def test_sh_11_refuses_a_member_that_is_not_a_helper(self):
        """SH-11"""
        for not_a_helper in (2.5, None, lambda: 2.5, lambda value: 2.5):
            with self.subTest(member=not_a_helper):
                with self.assertRaises(ValueError):
                    Chain(Multiply(1.5), not_a_helper)

    def test_sh_12_an_empty_chain_returns_what_it_was_handed(self):
        """SH-12"""
        self.assertEqual(Chain()(2.5), 2.5)


class StockHelperContractTests(TestCase):
    """SH-13. Every stock helper is usable where a helper is required."""

    def test_sh_13_every_stock_helper_satisfies_the_helper_contract(self):
        """SH-13"""
        # They are classes with __call__, and the declaration check reads a
        # signature — so this pins that a bound __call__ satisfies it.
        helpers = (
            Constant(1.0),
            Multiply(1.5),
            Add(0.5),
            RoundUp(),
            RoundDown(),
            Chain(Multiply(1.5)),
        )

        for helper in helpers:
            with self.subTest(helper=helper):
                effect_type = EnvironmentEffectType(
                    key="movement_cost", return_type=float, default=helper
                )
                EnvironmentEffect(effect_type, helper)


class WeatherBandTests(TestCase):
    """WB-01 — WB-04, WB-08 — WB-10. One number a day, for the whole game."""

    def test_wb_01_the_band_is_one_to_ten(self):
        """WB-01"""
        from evennia_calendar.config import Season

        for day in range(1, 100):
            for season in Season:
                with self.subTest(day=day, season=season):
                    band = weather_band(day, season)
                    self.assertIsInstance(band, int)
                    # Whatever the season, it names a slot a terrain has.
                    self.assertIn(band, range(1, 11))

    def test_wb_02_the_same_day_and_seed_always_give_the_same_band(self):
        """WB-02"""
        from evennia_calendar.config import Season

        # Derived rather than rolled, so nothing has to be stored and no two
        # processes have to agree on anything.
        self.assertEqual(
            weather_band(4218, Season.SUMMER, "fcm"),
            weather_band(4218, Season.SUMMER, "fcm"),
        )

    def test_wb_03_consecutive_days_do_not_walk_in_step(self):
        """WB-03"""
        from evennia_calendar.config import Season

        run = [weather_band(day, Season.SPRING) for day in range(1, 61)]

        # Every band turns up: a sawtooth would too, so also check it is not
        # ascending in step, which is what hash() on an int would give.
        self.assertEqual(set(run), set(range(3, 9)))
        self.assertNotEqual(run, [((day - 1) % 6) + 3 for day in range(1, 61)])

    def test_wb_04_a_different_seed_gives_a_different_band(self):
        """WB-04"""
        from evennia_calendar.config import Season

        # Not for every day — two seeds agree one day in six by chance — so
        # this asks across a run.
        one = [weather_band(day, Season.SPRING, "fcm") for day in range(1, 40)]
        other = [
            weather_band(day, Season.SPRING, "another-game") for day in range(1, 40)
        ]

        self.assertNotEqual(one, other)

    def test_wb_08_winter_shifts_the_band_down(self):
        """WB-08"""
        from evennia_calendar.config import Season

        run = [weather_band(day, Season.WINTER) for day in range(1, 61)]

        self.assertEqual(set(run), set(range(1, 7)))

    def test_wb_09_summer_shifts_the_band_up(self):
        """WB-09"""
        from evennia_calendar.config import Season

        run = [weather_band(day, Season.SUMMER) for day in range(1, 61)]

        self.assertEqual(set(run), set(range(5, 11)))

    def test_wb_10_spring_and_autumn_do_not_shift_the_band(self):
        """WB-10"""
        from evennia_calendar.config import Season

        spring = [weather_band(day, Season.SPRING) for day in range(1, 61)]
        autumn = [weather_band(day, Season.AUTUMN) for day in range(1, 61)]

        self.assertEqual(set(spring), set(range(3, 9)))
        # The same as each other, not merely in the same range — which is what
        # would break if the two were ever given different shifts.
        self.assertEqual(spring, autumn)


class CurrentWeatherBandTests(TestCase):
    """WB-05 — WB-07. Today's band, held between rollovers."""

    def setUp(self):
        from evennia_environment import weather

        weather._held_band = None
        weather._held_day = None

    tearDown = setUp

    def test_wb_05_a_read_with_nothing_held_computes_it(self):
        """WB-05"""
        # The lazy trigger: what answers between a restart and the next
        # rollover, when no signal has fired yet.
        self.assertIn(current_weather_band(), range(3, 9))

    def test_wb_06_a_second_read_does_not_recompute(self):
        """WB-06"""
        from evennia_environment import weather

        current_weather_band()

        with mock.patch.object(
            weather, "weather_band", side_effect=AssertionError("recomputed")
        ):
            current_weather_band()

    def test_wb_07_day_changed_refreshes_what_is_held(self):
        """WB-07"""
        from evennia_calendar.signals import day_changed

        from evennia_environment import weather

        current_weather_band()
        weather._held_band = 99

        day_changed.send(sender=None, previous=None, current=None)

        self.assertIn(weather._held_band, range(3, 9))
        self.assertNotEqual(weather._held_band, 99)


class IsDarkTests(TestCase):
    """DN-01 — DN-05. Whether it is dark, held between watches."""

    def setUp(self):
        from evennia_environment import weather

        dark_watches.cache_clear()
        weather._held_dark = None
        weather._held_phase = None

    tearDown = setUp

    def _at_watch(self, phase):
        """Patch the calendar so a case can sit in a chosen watch."""
        from evennia_environment import weather

        return mock.patch.object(
            weather, "game_date", return_value=mock.Mock(phase=phase)
        )

    def test_dn_01_a_declared_watch_is_dark(self):
        """DN-01"""
        # The suite declares (6, 1).
        with self._at_watch(6):
            self.assertIs(is_dark(), True)

    def test_dn_02_a_watch_not_declared_is_light(self):
        """DN-02"""
        with self._at_watch(3):
            self.assertIs(is_dark(), False)

    def test_dn_03_a_read_with_nothing_held_works_it_out(self):
        """DN-03"""
        from evennia_environment import weather

        with self._at_watch(1):
            is_dark()

        self.assertIsNotNone(weather._held_dark)

    def test_dn_04_a_second_read_does_not_ask_the_calendar_again(self):
        """DN-04"""
        from evennia_environment import weather

        with self._at_watch(1):
            is_dark()

        with mock.patch.object(
            weather, "game_date", side_effect=AssertionError("asked again")
        ):
            self.assertIs(is_dark(), True)

    def test_dn_05_phase_changed_refreshes_what_is_held(self):
        """DN-05"""
        from evennia_calendar.signals import phase_changed

        from evennia_environment import weather

        with self._at_watch(6):
            is_dark()
        self.assertIs(weather._held_dark, True)

        with self._at_watch(3):
            phase_changed.send(sender=None, previous=None, current=None)

        self.assertIs(weather._held_dark, False)


class CurrentWeatherTests(TestCase):
    """WB-11 — WB-12. The weather the band names."""

    def test_wb_11_the_band_names_the_slot(self):
        """WB-11"""
        from evennia_environment import weather
        from tests.terrain_tables import MOUNTAINS

        for band in range(1, 11):
            with self.subTest(band=band):
                with mock.patch.object(
                    weather, "current_weather_band", return_value=band
                ):
                    found = current_weather(MOUNTAINS, dark=False)

                # Slot 4 alone carries a different day weather.
                expected = "scorching" if band == 4 else f"band_{band}"
                self.assertEqual(found.key, expected)

    def test_wb_12_dark_reads_the_slots_night_weather(self):
        """WB-12"""
        from evennia_environment import weather
        from tests.terrain_tables import MOUNTAINS

        with mock.patch.object(weather, "current_weather_band", return_value=4):
            self.assertEqual(current_weather(MOUNTAINS, dark=False).key, "scorching")
            self.assertEqual(
                current_weather(MOUNTAINS, dark=True).key, "freezing_clear"
            )

            # A slot with no night declared answers the same either way.
            with mock.patch.object(
                weather, "current_weather_band", return_value=5
            ):
                self.assertEqual(
                    current_weather(MOUNTAINS, dark=True).key,
                    current_weather(MOUNTAINS, dark=False).key,
                )


MOVEMENT_COST = EnvironmentEffectType(
    key="movement_cost", return_type=float, default=_constant(1.0)
)


class EffectTypeRegistryTests(TestCase):
    """ER-01 — ER-03, ER-11. Registering, and reading back what was registered.

    Every case builds its own registry rather than touching the module-level
    ``ENVIRONMENT_EFFECT_TYPES``, so nothing leaks between runs.
    """

    def test_er_01_a_registered_effect_type_is_returned_by_its_key(self):
        """ER-01"""
        registry = EnvironmentEffectTypeRegistry()
        registry.register(MOVEMENT_COST)

        self.assertIs(registry.get("movement_cost"), MOVEMENT_COST)

    def test_er_02_refuses_something_that_is_not_an_effect_type(self):
        """ER-02"""
        registry = EnvironmentEffectTypeRegistry()

        for not_an_effect_type in ("movement_cost", {"movement_cost": 1.0}, None):
            with self.subTest(value=not_an_effect_type):
                with self.assertRaises(ValueError):
                    registry.register(not_an_effect_type)

    def test_er_03_a_fresh_registry_has_nothing_registered(self):
        """ER-03"""
        self.assertIsNone(EnvironmentEffectTypeRegistry().get("movement_cost"))

    def test_er_11_an_unregistered_key_returns_none(self):
        """ER-11"""
        registry = EnvironmentEffectTypeRegistry()
        registry.register(MOVEMENT_COST)

        self.assertIsNone(registry.get("health_effect"))


class EffectTypeRegistryDuplicateTests(TestCase):
    """ER-04, ER-06. One key, one declaration, whatever it holds."""

    def test_er_04_refuses_a_second_effect_type_under_a_taken_key(self):
        """ER-04"""
        registry = EnvironmentEffectTypeRegistry()
        registry.register(MOVEMENT_COST)

        with self.assertRaises(ValueError):
            registry.register(
                EnvironmentEffectType(
                    key="movement_cost", return_type=int, default=_constant(1)
                )
            )

    def test_er_06_the_duplicate_refusal_names_the_key(self):
        """ER-06"""
        registry = EnvironmentEffectTypeRegistry()
        registry.register(MOVEMENT_COST)

        with self.assertRaises(ValueError) as caught:
            registry.register(
                EnvironmentEffectType(
                    key="movement_cost", return_type=int, default=_constant(1)
                )
            )

        self.assertIn("movement_cost", str(caught.exception))


class EffectTypeRegistryIsolationTests(TestCase):
    """ER-10. The store is per-instance, not a mutable class attribute."""

    def test_er_10_two_registries_do_not_share_state(self):
        """ER-10"""
        registry = EnvironmentEffectTypeRegistry()
        other = EnvironmentEffectTypeRegistry()

        registry.register(MOVEMENT_COST)

        self.assertIsNone(other.get("movement_cost"))


class EffectConstructionTests(TestCase):
    """EE-01 — EE-02. What a valid pairing gives back."""

    def test_ee_01_carries_its_type_and_helper(self):
        """EE-01"""
        helper = _constant(2.5)
        effect = EnvironmentEffect(MOVEMENT_COST, helper)

        self.assertIs(effect.effect_type, MOVEMENT_COST)
        self.assertIs(effect.helper, helper)

    def test_ee_02_is_frozen(self):
        """EE-02"""
        effect = EnvironmentEffect(MOVEMENT_COST, _constant(2.5))

        with self.assertRaises(dataclasses.FrozenInstanceError):
            effect.helper = _constant(3.0)


class EffectTypeReferenceTests(TestCase):
    """EE-03. The pairing takes the declared type, not a stand-in for one."""

    def test_ee_03_refuses_a_type_that_is_not_an_effect_type(self):
        """EE-03"""
        for not_a_type in ("movement_cost", 42, None):
            with self.subTest(effect_type=not_a_type):
                with self.assertRaises(ValueError):
                    EnvironmentEffect(not_a_type, _constant(2.5))


class EffectHelperTests(TestCase):
    """EE-09. The helper is checked the way the type's default is.

    The rule is pinned by EF-15 to EF-17. This is here to prove the same check
    runs on a contribution, not to test it a second time.
    """

    def test_ee_09_refuses_a_helper_that_cannot_be_called_as_one(self):
        """EE-09"""
        not_helpers = (
            2.5,                        # not callable at all
            None,                       # nor this
            lambda: 2.5,                # nowhere for the running value
            lambda value: 2.5,          # nowhere for the caller's kwargs
        )

        for not_a_helper in not_helpers:
            with self.subTest(helper=not_a_helper):
                with self.assertRaises(ValueError):
                    EnvironmentEffect(MOVEMENT_COST, not_a_helper)


class EffectRefusalTests(TestCase):
    """EE-08. One exception class, and it says which declaration is wrong."""

    def test_ee_08_every_refusal_is_a_value_error_naming_the_key(self):
        """EE-08"""
        for not_a_helper in (2.5, lambda: 2.5):
            with self.subTest(helper=not_a_helper):
                with self.assertRaises(ValueError) as caught:
                    EnvironmentEffect(MOVEMENT_COST, not_a_helper)
                self.assertIn("movement_cost", str(caught.exception))

        # With no real type there is no key to name, so the refusal names what
        # it was handed instead.
        with self.assertRaises(ValueError) as caught:
            EnvironmentEffect(42, _constant(2.5))

        self.assertIn("42", str(caught.exception))


# A weather is never built at module scope here: every case constructs its own,
# so a refusal cannot take the whole suite down at import time.
BLIZZARD_DESCRIPTION = "Snow drives across the ridge in sheets."
BLIZZARD_TRANSITION = "The wind rises, and the snow begins to drive."

VISIBILITY = EnvironmentEffectType(
    key="visibility", return_type=float, default=_constant(1.0)
)


class WeatherTypeConstructionTests(TestCase):
    """WT-01 — WT-02. What a valid declaration gives back."""

    def test_wt_01_carries_its_key_effects_and_both_strings(self):
        """WT-01"""
        effects = (EnvironmentEffect(MOVEMENT_COST, _constant(2.5)),)
        weather = WeatherType(
            key="blizzard",
            effects=effects,
            description=BLIZZARD_DESCRIPTION,
            transition_in=BLIZZARD_TRANSITION,
        )

        self.assertEqual(weather.key, "blizzard")
        self.assertEqual(weather.effects, effects)
        self.assertEqual(weather.description, BLIZZARD_DESCRIPTION)
        self.assertEqual(weather.transition_in, BLIZZARD_TRANSITION)

    def test_wt_02_is_frozen(self):
        """WT-02"""
        weather = WeatherType(key="blizzard")

        with self.assertRaises(dataclasses.FrozenInstanceError):
            weather.key = "thunderstorm"


class WeatherTypeKeyTests(TestCase):
    """WT-03 — WT-04. The key names the weather, so it has to be a name.

    Nothing constrains it beyond being a non-empty string — a space is legal,
    as it is for an effect key. The key is a mapping handle and a player never
    sees it.
    """

    def test_wt_03_refuses_a_key_that_is_not_a_string(self):
        """WT-03"""
        with self.assertRaises(ValueError):
            WeatherType(key=42)

    def test_wt_04_refuses_an_empty_key(self):
        """WT-04"""
        with self.assertRaises(ValueError):
            WeatherType(key="")


class WeatherTypeEffectsTests(TestCase):
    """WT-05 — WT-06, WT-11 — WT-12. What a weather may declare."""

    def test_wt_05_accepts_a_weather_declaring_no_effects(self):
        """WT-05"""
        weather = WeatherType(key="sunny_with_some_clouds")

        self.assertEqual(weather.effects, ())

    def test_wt_06_refuses_effects_that_are_not_environment_effects(self):
        """WT-06"""
        not_effects = (
            (MOVEMENT_COST,),                   # the type, not a declaration
            ("movement_cost",),                 # nor its key
            (EnvironmentEffect(MOVEMENT_COST, _constant(2.5)), 42),
            42,                                 # not iterable at all
            EnvironmentEffect(MOVEMENT_COST, _constant(2.5)),   # nor is one
        )

        for not_an_effect in not_effects:
            with self.subTest(effects=not_an_effect):
                with self.assertRaises(ValueError):
                    WeatherType(key="blizzard", effects=not_an_effect)

    def test_wt_11_refuses_two_effects_for_one_effect_type(self):
        """WT-11"""
        with self.assertRaises(ValueError) as caught:
            WeatherType(
                key="blizzard",
                effects=(
                    EnvironmentEffect(MOVEMENT_COST, _constant(2.5)),
                    EnvironmentEffect(MOVEMENT_COST, _constant(3.0)),
                ),
            )

        self.assertIn("movement_cost", str(caught.exception))

    def test_wt_12_stores_effects_as_a_tuple(self):
        """WT-12"""
        weather = WeatherType(
            key="blizzard",
            effects=[EnvironmentEffect(MOVEMENT_COST, _constant(2.5))],
        )

        self.assertIsInstance(weather.effects, tuple)


class WeatherTypeStringTests(TestCase):
    """WT-07 — WT-09. Two optional strings the library only carries."""

    def test_wt_07_both_strings_default_to_none(self):
        """WT-07"""
        weather = WeatherType(key="blizzard")

        self.assertIsNone(weather.description)
        self.assertIsNone(weather.transition_in)

    def test_wt_08_refuses_a_description_that_is_not_a_string(self):
        """WT-08"""
        with self.assertRaises(ValueError):
            WeatherType(key="blizzard", description=42)

    def test_wt_09_refuses_a_transition_in_that_is_not_a_string(self):
        """WT-09"""
        with self.assertRaises(ValueError):
            WeatherType(key="blizzard", transition_in=42)


class WeatherTypeRefusalTests(TestCase):
    """WT-10. Every refusal is one exception class, and it names the key."""

    def test_wt_10_every_refusal_is_a_value_error_naming_the_key(self):
        """WT-10"""
        bad_declarations = (
            {"key": 42},
            {"key": ""},
            {"key": "blizzard", "effects": ("movement_cost",)},
            {"key": "blizzard", "description": 42},
            {"key": "blizzard", "transition_in": 42},
        )

        for declaration in bad_declarations:
            with self.subTest(declaration=declaration):
                with self.assertRaises(ValueError) as caught:
                    WeatherType(**declaration)
                # A key that is not a string still has to appear, so the
                # consumer can find the declaration that is wrong.
                self.assertIn(str(declaration["key"]), str(caught.exception))


class WeatherSlotTests(TestCase):
    """WS-01 — WS-05. One slot: what occurs there, day and night.

    Weather types are built inside each case rather than at module scope, so a
    refusal cannot take the whole suite down at import time.
    """

    def test_ws_01_carries_its_day_and_night(self):
        """WS-01"""
        day = WeatherType(key="scorching")
        night = WeatherType(key="freezing_clear")

        slot = WeatherSlot(day, night=night)

        self.assertIs(slot.day, day)
        self.assertIs(slot.night, night)

    def test_ws_02_night_defaults_to_the_day_weather(self):
        """WS-02"""
        day = WeatherType(key="blizzard")

        slot = WeatherSlot(day)

        # The same object, not an equal one: it is what makes "does this slot
        # differ at night" answerable as slot.night is slot.day.
        self.assertIs(slot.night, day)
        self.assertIs(slot.night, slot.day)

    def test_ws_03_is_frozen(self):
        """WS-03"""
        slot = WeatherSlot(WeatherType(key="blizzard"))

        with self.assertRaises(dataclasses.FrozenInstanceError):
            slot.day = WeatherType(key="clear")

    def test_ws_04_refuses_a_day_that_is_not_a_weather_type(self):
        """WS-04"""
        for not_a_weather in ("blizzard", 42, None):
            with self.subTest(day=not_a_weather):
                with self.assertRaises(ValueError):
                    WeatherSlot(not_a_weather)

    def test_ws_05_refuses_a_night_that_is_not_a_weather_type(self):
        """WS-05"""
        day = WeatherType(key="scorching")

        for not_a_weather in ("freezing_clear", 42):
            with self.subTest(night=not_a_weather):
                with self.assertRaises(ValueError):
                    WeatherSlot(day, night=not_a_weather)


def _ten_slots(**overrides):
    """Ten filled slots, so a case can change one and leave the rest valid.

    Keys arrive as ``slot_1`` and so on because a keyword cannot be a number.
    """
    slots = {n: WeatherType(key=f"weather_{n}") for n in range(1, 11)}
    for name, value in overrides.items():
        slots[int(name.removeprefix("slot_"))] = value
    return slots


class TerrainTypeConstructionTests(TestCase):
    """TT-01 — TT-02. What a valid declaration gives back."""

    def test_tt_01_carries_its_key_description_effects_and_slots(self):
        """TT-01"""
        effects = (EnvironmentEffect(MOVEMENT_COST, _constant(1.5)),)
        slots = {n: WeatherSlot(WeatherType(key=f"weather_{n}")) for n in range(1, 11)}

        terrain = TerrainType(
            key="desert",
            description="Dunes run to the horizon.",
            effects=effects,
            weather_slots=slots,
        )

        self.assertEqual(terrain.key, "desert")
        self.assertEqual(terrain.description, "Dunes run to the horizon.")
        self.assertEqual(terrain.effects, effects)
        self.assertEqual(terrain.weather_slots, tuple(slots[n] for n in range(1, 11)))

    def test_tt_02_is_frozen(self):
        """TT-02"""
        terrain = TerrainType(key="desert", weather_slots=_ten_slots())

        with self.assertRaises(dataclasses.FrozenInstanceError):
            terrain.key = "swamp"


class TerrainTypeKeyTests(TestCase):
    """TT-03 — TT-04. The key names the terrain, so it has to be a name."""

    def test_tt_03_refuses_a_key_that_is_not_a_string(self):
        """TT-03"""
        with self.assertRaises(ValueError):
            TerrainType(key=42, weather_slots=_ten_slots())

    def test_tt_04_refuses_an_empty_key(self):
        """TT-04"""
        with self.assertRaises(ValueError):
            TerrainType(key="", weather_slots=_ten_slots())


class TerrainTypeEffectsTests(TestCase):
    """TT-05 — TT-06. The same effects rule a weather follows."""

    def test_tt_05_accepts_a_terrain_declaring_no_effects(self):
        """TT-05"""
        terrain = TerrainType(key="desert", weather_slots=_ten_slots())

        self.assertEqual(terrain.effects, ())

    def test_tt_06_applies_the_shared_effects_rule(self):
        """TT-06"""
        bad_effects = (
            ("movement_cost",),
            (
                EnvironmentEffect(MOVEMENT_COST, _constant(1.5)),
                EnvironmentEffect(MOVEMENT_COST, _constant(2.0)),
            ),
        )

        for effects in bad_effects:
            with self.subTest(effects=effects):
                with self.assertRaises(ValueError):
                    TerrainType(
                        key="desert", effects=effects, weather_slots=_ten_slots()
                    )


class TerrainTypeWeatherSlotTests(TestCase):
    """TT-07 — TT-10. Exactly ten slots, keyed one to ten."""

    def test_tt_07_refuses_slot_keys_that_are_not_one_to_ten(self):
        """TT-07"""
        nine = _ten_slots()
        del nine[10]

        eleven = _ten_slots()
        eleven[11] = WeatherType(key="weather_11")

        gap = _ten_slots()
        del gap[4]
        gap[0] = WeatherType(key="weather_0")

        not_an_integer = _ten_slots()
        del not_an_integer[1]
        not_an_integer["1"] = WeatherType(key="weather_1")

        for slots in (nine, eleven, gap, not_an_integer, {}):
            with self.subTest(keys=sorted(map(str, slots))):
                with self.assertRaises(ValueError):
                    TerrainType(key="desert", weather_slots=slots)

    def test_tt_08_wraps_a_bare_weather_type_in_a_slot(self):
        """TT-08"""
        blizzard = WeatherType(key="blizzard")

        terrain = TerrainType(
            key="mountains", weather_slots=_ten_slots(slot_1=blizzard)
        )

        first = terrain.weather_slots[0]
        self.assertIsInstance(first, WeatherSlot)
        self.assertIs(first.day, blizzard)
        self.assertIs(first.night, blizzard)

    def test_tt_09_refuses_a_slot_that_is_neither_slot_nor_weather(self):
        """TT-09"""
        for not_a_slot in ("blizzard", 42, None):
            with self.subTest(slot=not_a_slot):
                with self.assertRaises(ValueError):
                    TerrainType(
                        key="desert", weather_slots=_ten_slots(slot_3=not_a_slot)
                    )

    def test_tt_10_stores_the_slots_as_a_tuple_in_slot_order(self):
        """TT-10"""
        # Declared out of order, so the ordering is proved rather than inherited
        # from how the literal happened to be written.
        slots = {n: WeatherType(key=f"weather_{n}") for n in reversed(range(1, 11))}

        terrain = TerrainType(key="desert", weather_slots=slots)

        self.assertIsInstance(terrain.weather_slots, tuple)
        self.assertEqual(
            [slot.day.key for slot in terrain.weather_slots],
            [f"weather_{n}" for n in range(1, 11)],
        )


class TerrainTypeDescriptionTests(TestCase):
    """TT-12 — TT-13. One optional string the library only carries."""

    def test_tt_12_description_defaults_to_none(self):
        """TT-12"""
        terrain = TerrainType(key="desert", weather_slots=_ten_slots())

        self.assertIsNone(terrain.description)

    def test_tt_13_refuses_a_description_that_is_not_a_string(self):
        """TT-13"""
        with self.assertRaises(ValueError):
            TerrainType(key="desert", weather_slots=_ten_slots(), description=42)


class TerrainTypeRefusalTests(TestCase):
    """TT-11. Every refusal is one exception class, and it names the key."""

    def test_tt_11_every_refusal_is_a_value_error_naming_the_key(self):
        """TT-11"""
        bad_declarations = (
            {"key": 42, "weather_slots": _ten_slots()},
            {"key": "", "weather_slots": _ten_slots()},
            {"key": "desert", "weather_slots": {}},
            {"key": "desert", "weather_slots": _ten_slots(), "description": 42},
            {
                "key": "desert",
                "weather_slots": _ten_slots(),
                "effects": ("movement_cost",),
            },
        )

        for declaration in bad_declarations:
            with self.subTest(key=declaration["key"]):
                with self.assertRaises(ValueError) as caught:
                    TerrainType(**declaration)
                self.assertIn(str(declaration["key"]), str(caught.exception))


def _ten_still_slots():
    """Ten slots of one weather, for a terrain whose weather is beside the point."""
    still = WeatherType(key="still_air")
    return {n: still for n in range(1, 11)}


class ResolveTests(TestCase):
    """RS-01 — RS-05. What a key answers, given who declares it."""

    def _type(self, default=None, requires=()):
        return EnvironmentEffectType(
            key="movement_cost",
            return_type=float,
            default=default or _constant(1.0),
            requires=requires,
        )

    def _terrain(self, *effects):
        return TerrainType(
            key="swamp", effects=effects, weather_slots=_ten_still_slots()
        )

    def test_rs_01_with_neither_contributor_the_default_answers(self):
        """RS-01"""
        self.assertEqual(resolve(self._type()), 1.0)

    def test_rs_02_a_terrain_is_handed_the_defaults_answer(self):
        """RS-02"""
        effect_type = self._type()
        terrain = self._terrain(EnvironmentEffect(effect_type, Add(1.0)))

        self.assertEqual(resolve(effect_type, terrain_type=terrain), 2.0)

    def test_rs_03_a_weather_is_handed_the_defaults_answer(self):
        """RS-03"""
        effect_type = self._type()
        weather = WeatherType(
            key="blizzard", effects=(EnvironmentEffect(effect_type, Add(1.0)),)
        )

        self.assertEqual(resolve(effect_type, weather_type=weather), 2.0)

    def test_rs_04_terrain_runs_then_weather(self):
        """RS-04"""
        effect_type = self._type()
        terrain = self._terrain(EnvironmentEffect(effect_type, Add(1.0)))
        weather = WeatherType(
            key="blizzard", effects=(EnvironmentEffect(effect_type, Multiply(3.0)),)
        )

        # 1.0 -> +1 -> 2.0 -> x3 -> 6.0. The other order would give 4.0, so the
        # number proves the sequence rather than only the arithmetic.
        self.assertEqual(
            resolve(effect_type, terrain_type=terrain, weather_type=weather), 6.0
        )

    def test_rs_05_a_contributor_declaring_other_keys_changes_nothing(self):
        """RS-05"""
        effect_type = self._type()
        other = EnvironmentEffectType(
            key="visibility", return_type=float, default=_constant(1.0)
        )
        terrain = self._terrain(EnvironmentEffect(other, Constant(0.2)))
        weather = WeatherType(
            key="fog", effects=(EnvironmentEffect(other, Constant(0.1)),)
        )

        self.assertEqual(
            resolve(effect_type, terrain_type=terrain, weather_type=weather), 1.0
        )


class ResolveKwargTests(TestCase):
    """RS-06 — RS-08. What the call site passes, and what is required."""

    def test_rs_06_the_kwargs_reach_every_helper(self):
        """RS-06"""
        seen = []

        def _watching(value, **kwargs):
            seen.append(kwargs)
            # The default is handed None, nothing having run before it, so it
            # has to produce the starting value rather than pass one on.
            return 1.0 if value is None else value

        effect_type = EnvironmentEffectType(
            key="movement_cost", return_type=float, default=_watching
        )
        terrain = TerrainType(
            key="swamp",
            effects=(EnvironmentEffect(effect_type, _watching),),
            weather_slots=_ten_still_slots(),
        )
        weather = WeatherType(
            key="blizzard", effects=(EnvironmentEffect(effect_type, _watching),)
        )

        resolve(
            effect_type,
            terrain_type=terrain,
            weather_type=weather,
            actor="someone",
        )

        self.assertEqual(seen, [{"actor": "someone"}] * 3)

    def test_rs_07_refuses_a_missing_required_kwarg(self):
        """RS-07"""
        effect_type = EnvironmentEffectType(
            key="movement_cost",
            return_type=float,
            default=_constant(1.0),
            requires=("actor", "door"),
        )

        with self.assertRaises(ValueError) as caught:
            resolve(effect_type, actor="someone")

        message = str(caught.exception)
        self.assertIn("movement_cost", message)
        self.assertIn("door", message)

    def test_rs_08_passes_through_kwargs_beyond_what_is_required(self):
        """RS-08"""
        effect_type = EnvironmentEffectType(
            key="movement_cost",
            return_type=float,
            default=_constant(1.0),
            requires=("actor",),
        )

        self.assertEqual(
            resolve(effect_type, actor="someone", door="a door"), 1.0
        )


class ResolveReturnTypeTests(TestCase):
    """RS-09 — RS-11. A wrong answer names whichever helper gave it."""

    def test_rs_09_refuses_a_default_returning_the_wrong_type(self):
        """RS-09"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", return_type=float, default=_constant("fast")
        )

        with self.assertRaises(ValueError) as caught:
            resolve(effect_type)

        self.assertIn("default", str(caught.exception))

    def test_rs_10_refuses_a_terrain_helper_returning_the_wrong_type(self):
        """RS-10"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", return_type=float, default=_constant(1.0)
        )
        terrain = TerrainType(
            key="swamp",
            effects=(EnvironmentEffect(effect_type, _constant("fast")),),
            weather_slots=_ten_still_slots(),
        )

        with self.assertRaises(ValueError) as caught:
            resolve(effect_type, terrain_type=terrain)

        self.assertIn("swamp", str(caught.exception))

    def test_rs_11_refuses_a_weather_helper_returning_the_wrong_type(self):
        """RS-11"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", return_type=float, default=_constant(1.0)
        )
        weather = WeatherType(
            key="blizzard",
            effects=(EnvironmentEffect(effect_type, _constant("fast")),),
        )

        with self.assertRaises(ValueError) as caught:
            resolve(effect_type, weather_type=weather)

        self.assertIn("blizzard", str(caught.exception))


class ConfigTests(TestCase):
    """CF-01 — CF-09. The setting, and the boot check that refuses a bad one.

    Every case swaps the setting, so each clears the accessor's cache first —
    it is resolved once for the life of a process and a test is the one thing
    that changes a setting mid-flight.
    """

    def setUp(self):
        terrain_enum.cache_clear()
        terrain_types.cache_clear()
        dark_watches.cache_clear()

    tearDown = setUp

    def _refusal(self, value, setting=SETTING_TERRAIN_ENUM):
        """Return the message from checking with ``setting`` at ``value``."""
        with override_settings(**{setting: value}):
            with self.assertRaises(ImproperlyConfigured) as caught:
                check_settings()

        return str(caught.exception)

    def test_cf_01_refuses_an_absent_setting(self):
        """CF-01"""
        message = self._refusal(None)

        self.assertIn(SETTING_TERRAIN_ENUM, message)
        # The refusal shows what a value looks like, so a consumer reading it
        # does not have to find the documentation to act on it.
        self.assertIn("world.environment.Terrain", message)

    def test_cf_02_refuses_a_setting_that_is_empty_or_not_a_string(self):
        """CF-02"""
        for value in ("", 42, ["world.environment.Terrain"]):
            with self.subTest(value=value):
                self.assertIn(SETTING_TERRAIN_ENUM, self._refusal(value))

    def test_cf_03_refuses_a_path_that_cannot_be_imported(self):
        """CF-03"""
        with override_settings(
            **{SETTING_TERRAIN_ENUM: "tests.nothing_here.Terrain"}
        ):
            with self.assertRaises(ImproperlyConfigured) as caught:
                check_settings()

        # Chained, not swallowed: the consumer gets the setting that is wrong
        # and the import error underneath it.
        self.assertIsNotNone(caught.exception.__cause__)
        self.assertIn("tests.nothing_here.Terrain", str(caught.exception))

    def test_cf_04_refuses_a_path_naming_something_that_is_not_an_enum(self):
        """CF-04"""
        message = self._refusal("tests.terrain_enums.NOT_AN_ENUM")

        self.assertIn("Enum", message)

    def test_cf_05_accepts_an_enum_with_no_members(self):
        """CF-05"""
        # Nothing declared yet: an empty enum and no terrain types together.
        # An empty enum beside a populated table would make every terrain
        # unreachable, which CF-12 refuses.
        with override_settings(
            **{
                SETTING_TERRAIN_ENUM: "tests.terrain_enums.EmptyTerrain",
                SETTING_TERRAIN_TYPES: "tests.terrain_tables.NO_TERRAINS",
            }
        ):
            check_settings()

    def test_cf_06_refuses_duplicate_values(self):
        """CF-06"""
        message = self._refusal("tests.terrain_enums.AliasedTerrain")

        # Named, because Python has already folded JUNGLE into FOREST by the
        # time anything looks at the members.
        self.assertIn("JUNGLE", message)

    def test_cf_07_refuses_values_that_are_not_strings(self):
        """CF-07"""
        message = self._refusal("tests.terrain_enums.NumberedTerrain")

        self.assertIn("SWAMP", message)
        self.assertIn("MOUNTAINS", message)

    def test_cf_08_reports_two_independent_problems_together(self):
        """CF-08"""
        message = self._refusal("tests.terrain_enums.DoublyWrongTerrain")

        self.assertEqual(message.count(PROBLEM_PREFIX), 2)
        self.assertIn("JUNGLE", message)
        self.assertIn("SWAMP", message)

    def test_cf_10_refuses_an_absent_terrain_types_setting(self):
        """CF-10"""
        message = self._refusal(None, setting=SETTING_TERRAIN_TYPES)

        self.assertIn(SETTING_TERRAIN_TYPES, message)
        self.assertIn("world.environment.TERRAINS", message)

    def test_cf_11_refuses_terrain_types_that_are_not_terrain_types(self):
        """CF-11"""
        message = self._refusal(
            "tests.terrain_tables.NOT_TERRAIN_TYPES", setting=SETTING_TERRAIN_TYPES
        )

        self.assertIn("TerrainType", message)

    def test_cf_12_refuses_a_terrain_type_no_enum_member_names(self):
        """CF-12"""
        message = self._refusal(
            "tests.terrain_tables.UNREACHABLE_TERRAINS",
            setting=SETTING_TERRAIN_TYPES,
        )

        # Unreachable: a room can only ever store a member's value, so nothing
        # could arrive at this terrain.
        self.assertIn("tundra", message)

    def test_cf_13_accepts_an_enum_member_with_no_terrain_type(self):
        """CF-13"""
        with override_settings(
            **{SETTING_TERRAIN_TYPES: "tests.terrain_tables.PARTIAL_TERRAINS"}
        ):
            check_settings()

    def test_cf_14_reports_a_problem_in_each_setting_together(self):
        """CF-14"""
        with override_settings(
            **{
                SETTING_TERRAIN_ENUM: "tests.terrain_enums.NumberedTerrain",
                SETTING_TERRAIN_TYPES: None,
            }
        ):
            with self.assertRaises(ImproperlyConfigured) as caught:
                check_settings()

        message = str(caught.exception)
        self.assertEqual(message.count(PROBLEM_PREFIX), 2)
        self.assertIn(SETTING_TERRAIN_TYPES, message)

    def test_cf_15_refuses_absent_dark_watches(self):
        """CF-15"""
        message = self._refusal(None, setting=SETTING_DARK_WATCHES)

        self.assertIn(SETTING_DARK_WATCHES, message)

    def test_cf_16_refuses_dark_watches_that_are_not_watch_numbers(self):
        """CF-16"""
        for value in ("6,1", 6, ("Dog",)):
            with self.subTest(value=value):
                self.assertIn(
                    SETTING_DARK_WATCHES,
                    self._refusal(value, setting=SETTING_DARK_WATCHES),
                )

    def test_cf_17_refuses_a_watch_outside_one_to_six(self):
        """CF-17"""
        message = self._refusal((0, 7), setting=SETTING_DARK_WATCHES)

        self.assertIn("0", message)
        self.assertIn("7", message)

    def test_cf_18_accepts_no_dark_watches_at_all(self):
        """CF-18"""
        # A game with no night is a correct reading; not declaring is not.
        with override_settings(**{SETTING_DARK_WATCHES: ()}):
            check_settings()

    def test_cf_09_a_valid_setting_resolves_to_the_enum(self):
        """CF-09"""
        from tests.terrain_enums import Terrain

        check_settings()

        self.assertIs(terrain_enum(), Terrain)


class RoomTerrainDescriptionTests(DjangoTestCase):
    """RM-03, RM-04, RM-08. What a room says about its terrain.

    The room stores a member; the description lives on the TerrainType whose
    key matches that member's value. These need a real object, so the fixtures
    are imported inside each case.
    """

    def _room(self):
        from evennia import create_object

        from tests.game_typeclasses import TerrainRoom

        return create_object(TerrainRoom, key="room", nohome=True)

    def test_rm_03_returns_the_terrains_description(self):
        """RM-03"""
        from tests.terrain_enums import Terrain
        from tests.terrain_tables import SWAMP

        room = self._room()
        room.terrain = Terrain.SWAMP

        self.assertEqual(room.get_terrain_description(), SWAMP.description)

    def test_rm_04_a_room_with_no_terrain_has_no_description(self):
        """RM-04"""
        self.assertIsNone(self._room().get_terrain_description())

    def test_rm_08_a_terrain_with_no_description_returns_none(self):
        """RM-08"""
        from tests.terrain_enums import Terrain

        room = self._room()
        # MOUNTAINS declares no description, which is legal.
        room.terrain = Terrain.MOUNTAINS

        self.assertIsNone(room.get_terrain_description())


class RoomWeatherDescriptionTests(DjangoTestCase):
    """RM-05 — RM-07, RM-09. What a room says about its weather."""

    def _room(self, terrain=None):
        from evennia import create_object

        from tests.game_typeclasses import TerrainRoom

        room = create_object(TerrainRoom, key="room", nohome=True)
        if terrain is not None:
            room.terrain = terrain
        return room

    def test_rm_05_returns_the_active_weathers_description(self):
        """RM-05"""
        from evennia_environment import weather
        from tests.terrain_enums import Terrain

        room = self._room(Terrain.MOUNTAINS)

        # Band 4 is the slot that carries a description on both sides.
        with mock.patch.object(weather, "current_weather_band", return_value=4):
            with mock.patch.object(weather, "is_dark", return_value=False):
                self.assertEqual(
                    room.get_weather_description(), "The air shimmers."
                )

    def test_rm_06_day_false_forces_the_night_weather(self):
        """RM-06"""
        from evennia_environment import weather
        from tests.terrain_enums import Terrain

        room = self._room(Terrain.MOUNTAINS)

        with mock.patch.object(weather, "current_weather_band", return_value=4):
            # Light outside, and the argument overrides it anyway.
            with mock.patch.object(weather, "is_dark", return_value=False):
                self.assertEqual(
                    room.get_weather_description(day=False), "The cold bites."
                )

    def test_rm_07_a_weather_with_no_description_returns_none(self):
        """RM-07"""
        from evennia_environment import weather
        from tests.terrain_enums import Terrain

        room = self._room(Terrain.MOUNTAINS)

        # Slot 5 is a bare weather with no description, which is legal.
        with mock.patch.object(weather, "current_weather_band", return_value=5):
            with mock.patch.object(weather, "is_dark", return_value=False):
                self.assertIsNone(room.get_weather_description())

    def test_rm_09_a_room_with_no_terrain_has_no_weather(self):
        """RM-09"""
        # No terrain means no slot table to read a band against.
        self.assertIsNone(self._room().get_weather_description())


class TerrainPropertyTests(DjangoTestCase):
    """TP-01 — TP-14. A room's terrain: enum in, string stored, enum out.

    These need a real object — ``AttributeProperty`` is a descriptor over an
    attribute handler, and there is nothing to validate without one. The
    fixtures import Evennia, so they are imported inside each test rather than
    at module scope.
    """

    def _room(self):
        from evennia import create_object

        from tests.game_typeclasses import TerrainRoom

        return create_object(TerrainRoom, key="room", nohome=True)

    def test_tp_01_an_unassigned_room_has_no_terrain(self):
        """TP-01"""
        self.assertIsNone(self._room().terrain)

    def test_tp_03_accepts_a_member_and_reads_it_back(self):
        """TP-03"""
        from tests.terrain_enums import Terrain

        room = self._room()
        room.terrain = Terrain.SWAMP

        self.assertIs(room.terrain, Terrain.SWAMP)

    def test_tp_08_accepts_the_members_value_as_a_string(self):
        """TP-08"""
        from tests.terrain_enums import Terrain

        room = self._room()
        # The world-builder path: a YAML file can only supply a string.
        room.terrain = "swamp"

        self.assertIs(room.terrain, Terrain.SWAMP)

    def test_tp_10_stores_the_plain_string(self):
        """TP-10"""
        from tests.terrain_enums import Terrain

        room = self._room()
        room.terrain = Terrain.SWAMP

        # Read through the handler, not the property: the property would
        # resolve it back to the member and hide what is actually stored.
        stored = room.attributes.get("terrain", strattr=True)

        self.assertEqual(stored, "swamp")
        self.assertNotIsInstance(stored, Terrain)

    def test_tp_11_accepts_none_while_nothing_is_stored(self):
        """TP-11"""
        room = self._room()
        room.terrain = None

        self.assertIsNone(room.terrain)

    def test_tp_04_refuses_a_member_of_a_different_enum(self):
        """TP-04"""
        from tests.terrain_enums import Season

        room = self._room()

        with self.assertRaises(AttributeError):
            room.terrain = Season.WINTER

    def test_tp_09_refuses_a_string_matching_no_member(self):
        """TP-09"""
        room = self._room()

        with self.assertRaises(AttributeError):
            room.terrain = "swmap"

    def test_tp_05_refuses_a_value_that_is_neither_member_nor_string(self):
        """TP-05"""
        room = self._room()

        for not_a_terrain in (42, 2.5, object(), ["swamp"]):
            with self.subTest(value=not_a_terrain):
                with self.assertRaises(AttributeError):
                    room.terrain = not_a_terrain

    def test_tp_12_refuses_a_different_terrain_over_a_stored_one(self):
        """TP-12"""
        from tests.terrain_enums import Terrain

        room = self._room()
        room.terrain = Terrain.SWAMP

        with self.assertRaises(AttributeError):
            room.terrain = Terrain.MOUNTAINS

        self.assertIs(room.terrain, Terrain.SWAMP)

    def test_tp_13_accepts_the_same_terrain_assigned_again(self):
        """TP-13"""
        from tests.terrain_enums import Terrain

        room = self._room()
        room.terrain = Terrain.SWAMP
        # Both forms, since re-applied content may arrive as either.
        room.terrain = Terrain.SWAMP
        room.terrain = "swamp"

        self.assertIs(room.terrain, Terrain.SWAMP)

    def test_tp_14_refuses_none_over_a_stored_terrain(self):
        """TP-14"""
        from tests.terrain_enums import Terrain

        room = self._room()
        room.terrain = Terrain.SWAMP

        with self.assertRaises(AttributeError):
            room.terrain = None

        self.assertIs(room.terrain, Terrain.SWAMP)

    def test_tp_07_the_refusal_names_what_was_assigned(self):
        """TP-07"""
        room = self._room()

        with self.assertRaises(AttributeError) as caught:
            room.terrain = "swmap"

        self.assertIn("swmap", str(caught.exception))
