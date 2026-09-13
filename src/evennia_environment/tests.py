# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for evennia-environment, run via ``python runtests.py``.

Every case the library commits to lives in docs/test-plan.md, and every test
function here carries its case ID as its docstring so the trail reads both ways.
"""

import dataclasses
from unittest import TestCase

import evennia_environment
from evennia_environment import Effect, EffectRegistry


class ScaffoldTests(TestCase):
    """The install and the test runner work end to end."""

    def test_sc_01_package_imports_and_reports_its_version(self):
        """SC-01"""
        self.assertEqual(evennia_environment.__version__, "0.0.1")


class EffectConstructionTests(TestCase):
    """EF-01 — EF-02. What a valid declaration gives back."""

    def test_ef_01_carries_its_key_datatype_and_default(self):
        """EF-01"""
        effect = Effect(key="movement_cost", datatype=float, default=1.0)

        self.assertEqual(effect.key, "movement_cost")
        self.assertIs(effect.datatype, float)
        self.assertEqual(effect.default, 1.0)

    def test_ef_02_is_frozen(self):
        """EF-02"""
        effect = Effect(key="movement_cost", datatype=float, default=1.0)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            effect.default = 2.0


class EffectKeyTests(TestCase):
    """EF-03 — EF-04. The key names the effect, so it has to be a name."""

    def test_ef_03_refuses_a_key_that_is_not_a_string(self):
        """EF-03"""
        with self.assertRaises(ValueError):
            Effect(key=42, datatype=float, default=1.0)

    def test_ef_04_refuses_an_empty_key(self):
        """EF-04"""
        with self.assertRaises(ValueError):
            Effect(key="", datatype=float, default=1.0)


class EffectDatatypeTests(TestCase):
    """EF-05. The datatype is a type, not the name of one."""

    def test_ef_05_refuses_a_datatype_that_is_not_a_type(self):
        """EF-05"""
        with self.assertRaises(ValueError):
            Effect(key="movement_cost", datatype="float", default=1.0)


class EffectDefaultTests(TestCase):
    """EF-06 — EF-11. The default is checked against the declared datatype.

    ``isinstance`` and nothing more: no coercion, no widening, no truncation.
    ``None`` is the one exemption.
    """

    def test_ef_06_accepts_a_default_of_the_declared_type(self):
        """EF-06"""
        effect = Effect(key="movement_cost", datatype=float, default=2.5)

        self.assertEqual(effect.default, 2.5)
        self.assertIsInstance(effect.default, float)

    def test_ef_07_refuses_a_default_of_an_unrelated_type(self):
        """EF-07"""
        with self.assertRaises(ValueError):
            Effect(key="movement_cost", datatype=float, default="fast")

    def test_ef_08_refuses_an_int_default_for_a_float_datatype(self):
        """EF-08"""
        with self.assertRaises(ValueError):
            Effect(key="movement_cost", datatype=float, default=1)

    def test_ef_09_refuses_a_float_default_for_an_int_datatype(self):
        """EF-09"""
        with self.assertRaises(ValueError):
            Effect(key="crowding", datatype=int, default=2.5)

    def test_ef_10_accepts_a_bool_default_for_an_int_datatype(self):
        """EF-10"""
        effect = Effect(key="crowding", datatype=int, default=True)

        self.assertIs(effect.default, True)

    def test_ef_11_accepts_a_none_default_whatever_the_datatype(self):
        """EF-11"""
        effect = Effect(key="movement_cost", datatype=float, default=None)

        self.assertIsNone(effect.default)


class EffectRefusalTests(TestCase):
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
                    Effect(**declaration)
                # A key that is not a string still has to appear, so the
                # consumer can find the declaration that is wrong.
                self.assertIn(str(declaration["key"]), str(caught.exception))


MOVEMENT_COST = Effect(key="movement_cost", datatype=float, default=1.0)


class EffectRegistryTests(TestCase):
    """ER-01 — ER-03, ER-11. Registering, and reading back what was registered.

    Every case builds its own registry rather than touching the module-level
    ``EFFECTS``, so nothing leaks between runs.
    """

    def test_er_01_a_registered_effect_is_returned_by_its_key(self):
        """ER-01"""
        registry = EffectRegistry()
        registry.register(MOVEMENT_COST)

        self.assertIs(registry.get("movement_cost"), MOVEMENT_COST)

    def test_er_02_refuses_something_that_is_not_an_effect(self):
        """ER-02"""
        registry = EffectRegistry()

        for not_an_effect in ("movement_cost", {"movement_cost": 1.0}, None):
            with self.subTest(value=not_an_effect):
                with self.assertRaises(ValueError):
                    registry.register(not_an_effect)

    def test_er_03_a_fresh_registry_has_nothing_registered(self):
        """ER-03"""
        self.assertIsNone(EffectRegistry().get("movement_cost"))

    def test_er_11_an_unregistered_key_returns_none(self):
        """ER-11"""
        registry = EffectRegistry()
        registry.register(MOVEMENT_COST)

        self.assertIsNone(registry.get("health_effect"))


class EffectRegistryDuplicateTests(TestCase):
    """ER-04 — ER-06. One key, one declaration."""

    def test_er_04_refuses_a_different_effect_under_a_taken_key(self):
        """ER-04"""
        registry = EffectRegistry()
        registry.register(MOVEMENT_COST)

        with self.assertRaises(ValueError):
            registry.register(Effect(key="movement_cost", datatype=int, default=1))

    def test_er_05_accepts_an_identical_effect_registered_twice(self):
        """ER-05"""
        registry = EffectRegistry()
        registry.register(MOVEMENT_COST)
        registry.register(Effect(key="movement_cost", datatype=float, default=1.0))

        self.assertEqual(registry.get("movement_cost"), MOVEMENT_COST)

    def test_er_06_the_duplicate_refusal_names_the_key(self):
        """ER-06"""
        registry = EffectRegistry()
        registry.register(MOVEMENT_COST)

        with self.assertRaises(ValueError) as caught:
            registry.register(Effect(key="movement_cost", datatype=int, default=1))

        self.assertIn("movement_cost", str(caught.exception))


class EffectRegistryIsolationTests(TestCase):
    """ER-10. The store is per-instance, not a mutable class attribute."""

    def test_er_10_two_registries_do_not_share_state(self):
        """ER-10"""
        registry = EffectRegistry()
        other = EffectRegistry()

        registry.register(MOVEMENT_COST)

        self.assertIsNone(other.get("movement_cost"))
