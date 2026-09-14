# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for evennia-environment, run via ``python runtests.py``.

Every case the library commits to lives in docs/test-plan.md, and every test
function here carries its case ID as its docstring so the trail reads both ways.
"""

import dataclasses
from unittest import TestCase

import evennia_environment
from evennia_environment import (
    EnvironmentEffect,
    EnvironmentEffectType,
    EnvironmentEffectTypeRegistry,
    TerrainType,
    WeatherType,
)


class ScaffoldTests(TestCase):
    """The install and the test runner work end to end."""

    def test_sc_01_package_imports_and_reports_its_version(self):
        """SC-01"""
        self.assertEqual(evennia_environment.__version__, "0.0.1")


class EffectTypeConstructionTests(TestCase):
    """EF-01 — EF-02. What a valid declaration gives back."""

    def test_ef_01_carries_its_key_datatype_and_default(self):
        """EF-01"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", datatype=float, default=1.0
        )

        self.assertEqual(effect_type.key, "movement_cost")
        self.assertIs(effect_type.datatype, float)
        self.assertEqual(effect_type.default, 1.0)

    def test_ef_02_is_frozen(self):
        """EF-02"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", datatype=float, default=1.0
        )

        with self.assertRaises(dataclasses.FrozenInstanceError):
            effect_type.default = 2.0


class EffectTypeKeyTests(TestCase):
    """EF-03 — EF-04. The key names the effect type, so it has to be a name."""

    def test_ef_03_refuses_a_key_that_is_not_a_string(self):
        """EF-03"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key=42, datatype=float, default=1.0)

    def test_ef_04_refuses_an_empty_key(self):
        """EF-04"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key="", datatype=float, default=1.0)


class EffectTypeDatatypeTests(TestCase):
    """EF-05. The datatype is a type, not the name of one."""

    def test_ef_05_refuses_a_datatype_that_is_not_a_type(self):
        """EF-05"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key="movement_cost", datatype="float", default=1.0)


class EffectTypeDefaultTests(TestCase):
    """EF-06 — EF-11. The default is checked against the declared datatype.

    ``isinstance`` and nothing more: no coercion, no widening, no truncation.
    ``None`` is the one exemption.
    """

    def test_ef_06_accepts_a_default_of_the_declared_type(self):
        """EF-06"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", datatype=float, default=2.5
        )

        self.assertEqual(effect_type.default, 2.5)
        self.assertIsInstance(effect_type.default, float)

    def test_ef_07_refuses_a_default_of_an_unrelated_type(self):
        """EF-07"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key="movement_cost", datatype=float, default="fast")

    def test_ef_08_refuses_an_int_default_for_a_float_datatype(self):
        """EF-08"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key="movement_cost", datatype=float, default=1)

    def test_ef_09_refuses_a_float_default_for_an_int_datatype(self):
        """EF-09"""
        with self.assertRaises(ValueError):
            EnvironmentEffectType(key="crowding", datatype=int, default=2.5)

    def test_ef_10_accepts_a_bool_default_for_an_int_datatype(self):
        """EF-10"""
        effect_type = EnvironmentEffectType(key="crowding", datatype=int, default=True)

        self.assertIs(effect_type.default, True)

    def test_ef_11_accepts_a_none_default_whatever_the_datatype(self):
        """EF-11"""
        effect_type = EnvironmentEffectType(
            key="movement_cost", datatype=float, default=None
        )

        self.assertIsNone(effect_type.default)


class EffectTypeRefusalTests(TestCase):
    """EF-12. Every refusal is one exception class, and it names the key."""

    def test_ef_12_every_refusal_is_a_value_error_naming_the_key(self):
        """EF-12"""
        bad_declarations = (
            {"key": 42, "datatype": float, "default": 1.0},
            {"key": "", "datatype": float, "default": 1.0},
            {"key": "movement_cost", "datatype": "float", "default": 1.0},
            {"key": "movement_cost", "datatype": float, "default": "fast"},
        )

        for declaration in bad_declarations:
            with self.subTest(declaration=declaration):
                with self.assertRaises(ValueError) as caught:
                    EnvironmentEffectType(**declaration)
                # A key that is not a string still has to appear, so the
                # consumer can find the declaration that is wrong.
                self.assertIn(str(declaration["key"]), str(caught.exception))


MOVEMENT_COST = EnvironmentEffectType(key="movement_cost", datatype=float, default=1.0)


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
    """ER-04 — ER-06. One key, one declaration."""

    def test_er_04_refuses_a_different_effect_type_under_a_taken_key(self):
        """ER-04"""
        registry = EnvironmentEffectTypeRegistry()
        registry.register(MOVEMENT_COST)

        with self.assertRaises(ValueError):
            registry.register(
                EnvironmentEffectType(key="movement_cost", datatype=int, default=1)
            )

    def test_er_05_accepts_an_identical_effect_type_registered_twice(self):
        """ER-05"""
        registry = EnvironmentEffectTypeRegistry()
        registry.register(MOVEMENT_COST)
        registry.register(
            EnvironmentEffectType(key="movement_cost", datatype=float, default=1.0)
        )

        self.assertEqual(registry.get("movement_cost"), MOVEMENT_COST)

    def test_er_06_the_duplicate_refusal_names_the_key(self):
        """ER-06"""
        registry = EnvironmentEffectTypeRegistry()
        registry.register(MOVEMENT_COST)

        with self.assertRaises(ValueError) as caught:
            registry.register(
                EnvironmentEffectType(key="movement_cost", datatype=int, default=1)
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


# A second type, declared in a datatype nothing numeric will satisfy, so a
# magnitude of the wrong type has something to be wrong against.
GROUND_COVER = EnvironmentEffectType(key="ground_cover", datatype=str, default="bare")


class EffectConstructionTests(TestCase):
    """EE-01 — EE-02. What a valid pairing gives back."""

    def test_ee_01_carries_its_type_and_magnitude(self):
        """EE-01"""
        effect = EnvironmentEffect(MOVEMENT_COST, 2.5)

        self.assertIs(effect.effect_type, MOVEMENT_COST)
        self.assertEqual(effect.magnitude, 2.5)

    def test_ee_02_is_frozen(self):
        """EE-02"""
        effect = EnvironmentEffect(MOVEMENT_COST, 2.5)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            effect.magnitude = 3.0


class EffectTypeReferenceTests(TestCase):
    """EE-03. The pairing takes the declared type, not a stand-in for one."""

    def test_ee_03_refuses_a_type_that_is_not_an_effect_type(self):
        """EE-03"""
        for not_a_type in ("movement_cost", 42, None):
            with self.subTest(effect_type=not_a_type):
                with self.assertRaises(ValueError):
                    EnvironmentEffect(not_a_type, 2.5)


class EffectMagnitudeTests(TestCase):
    """EE-04 — EE-07. The magnitude is checked against the type's datatype.

    The same ``isinstance`` rule the type applies to its own default, read off
    the type that was handed over. ``None`` is not exempt here as it is there:
    omission from a collection is how absence is said.
    """

    def test_ee_04_accepts_a_magnitude_of_the_declared_datatype(self):
        """EE-04"""
        effect = EnvironmentEffect(MOVEMENT_COST, 2.5)

        self.assertEqual(effect.magnitude, 2.5)
        self.assertIsInstance(effect.magnitude, float)

    def test_ee_05_refuses_a_magnitude_of_an_unrelated_type(self):
        """EE-05"""
        with self.assertRaises(ValueError):
            EnvironmentEffect(GROUND_COVER, 2.5)

    def test_ee_06_refuses_an_int_magnitude_for_a_float_type(self):
        """EE-06"""
        with self.assertRaises(ValueError):
            EnvironmentEffect(MOVEMENT_COST, 1)

    def test_ee_07_refuses_a_none_magnitude(self):
        """EE-07"""
        for effect_type in (MOVEMENT_COST, GROUND_COVER):
            with self.subTest(effect_type=effect_type):
                with self.assertRaises(ValueError):
                    EnvironmentEffect(effect_type, None)


class EffectRefusalTests(TestCase):
    """EE-08. One exception class, and it says which declaration is wrong."""

    def test_ee_08_every_refusal_is_a_value_error_naming_the_key(self):
        """EE-08"""
        for magnitude in ("fast", 1, None):
            with self.subTest(magnitude=magnitude):
                with self.assertRaises(ValueError) as caught:
                    EnvironmentEffect(MOVEMENT_COST, magnitude)
                self.assertIn("movement_cost", str(caught.exception))

        # With no real type there is no key to name, so the refusal names what
        # it was handed instead.
        with self.assertRaises(ValueError) as caught:
            EnvironmentEffect(42, 2.5)

        self.assertIn("42", str(caught.exception))


# A weather is never built at module scope here: every case constructs its own,
# so a refusal cannot take the whole suite down at import time.
BLIZZARD_DESCRIPTION = "Snow drives across the ridge in sheets."
BLIZZARD_TRANSITION = "The wind rises, and the snow begins to drive."


class WeatherTypeConstructionTests(TestCase):
    """WT-01 — WT-02. What a valid declaration gives back."""

    def test_wt_01_carries_its_key_effects_and_both_strings(self):
        """WT-01"""
        weather = WeatherType(
            key="blizzard",
            effects={"movement_cost": 2.5},
            description=BLIZZARD_DESCRIPTION,
            transition_in=BLIZZARD_TRANSITION,
        )

        self.assertEqual(weather.key, "blizzard")
        self.assertEqual(weather.effects, {"movement_cost": 2.5})
        self.assertEqual(weather.description, BLIZZARD_DESCRIPTION)
        self.assertEqual(weather.transition_in, BLIZZARD_TRANSITION)

    def test_wt_02_is_frozen(self):
        """WT-02"""
        weather = WeatherType(key="blizzard", effects={})

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
            WeatherType(key=42, effects={})

    def test_wt_04_refuses_an_empty_key(self):
        """WT-04"""
        with self.assertRaises(ValueError):
            WeatherType(key="", effects={})


class WeatherTypeEffectsTests(TestCase):
    """WT-05 — WT-06. The mapping's presence and shape, not its contents.

    What a value looks like turns on whether weather overrides terrain's value
    or modifies it, which is open — see docs/test-plan.md § Open decisions.
    """

    def test_wt_05_accepts_an_empty_effects_mapping(self):
        """WT-05"""
        weather = WeatherType(key="sunny_with_some_clouds", effects={})

        self.assertEqual(weather.effects, {})

    def test_wt_06_refuses_effects_that_are_not_a_mapping(self):
        """WT-06"""
        not_mappings = ([("movement_cost", 2.5)], "movement_cost", None, 2.5)

        for not_a_mapping in not_mappings:
            with self.subTest(effects=not_a_mapping):
                with self.assertRaises(ValueError):
                    WeatherType(key="blizzard", effects=not_a_mapping)


class WeatherTypeStringTests(TestCase):
    """WT-07 — WT-09. Two optional strings the library only carries."""

    def test_wt_07_both_strings_default_to_none(self):
        """WT-07"""
        weather = WeatherType(key="blizzard", effects={})

        self.assertIsNone(weather.description)
        self.assertIsNone(weather.transition_in)

    def test_wt_08_refuses_a_description_that_is_not_a_string(self):
        """WT-08"""
        with self.assertRaises(ValueError):
            WeatherType(key="blizzard", effects={}, description=42)

    def test_wt_09_refuses_a_transition_in_that_is_not_a_string(self):
        """WT-09"""
        with self.assertRaises(ValueError):
            WeatherType(key="blizzard", effects={}, transition_in=42)


class WeatherTypeRefusalTests(TestCase):
    """WT-10. Every refusal is one exception class, and it names the key."""

    def test_wt_10_every_refusal_is_a_value_error_naming_the_key(self):
        """WT-10"""
        bad_declarations = (
            {"key": 42, "effects": {}},
            {"key": "", "effects": {}},
            {"key": "blizzard", "effects": [("movement_cost", 2.5)]},
            {"key": "blizzard", "effects": {}, "description": 42},
            {"key": "blizzard", "effects": {}, "transition_in": 42},
        )

        for declaration in bad_declarations:
            with self.subTest(declaration=declaration):
                with self.assertRaises(ValueError) as caught:
                    WeatherType(**declaration)
                # A key that is not a string still has to appear, so the
                # consumer can find the declaration that is wrong.
                self.assertIn(str(declaration["key"]), str(caught.exception))


class TerrainTypeTests(TestCase):
    """TT-01 — TT-02. The placeholder the room mixin will validate against.

    It has no fields yet. These two cases exist so the class is real and frozen
    before anything holds one; the rest land as fields are agreed.
    """

    def test_tt_01_a_terrain_type_can_be_constructed(self):
        """TT-01"""
        self.assertIsInstance(TerrainType(), TerrainType)

    def test_tt_02_is_frozen(self):
        """TT-02"""
        terrain_type = TerrainType()

        # Frozen blocks every attribute, not only declared fields, so this
        # holds before there is a field to assign to.
        with self.assertRaises(dataclasses.FrozenInstanceError):
            terrain_type.key = "swamp"
