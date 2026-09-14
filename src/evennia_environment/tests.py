# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for evennia-environment, run via ``python runtests.py``.

Every case the library commits to lives in docs/test-plan.md, and every test
function here carries its case ID as its docstring so the trail reads both ways.
"""

import dataclasses
from unittest import TestCase

# The TP cases create real objects, so they need a database around them. The
# rest are pure Python and stay on the lighter base.
from django.test import TestCase as DjangoTestCase

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

    def test_tp_02_refuses_a_declaration_that_is_not_an_enum(self):
        """TP-02"""
        from evennia_environment.room import TerrainProperty

        for not_an_enum in ("Terrain", 42, object()):
            with self.subTest(terrain_enum=not_an_enum):
                with self.assertRaises(ValueError):
                    TerrainProperty(not_an_enum)

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
