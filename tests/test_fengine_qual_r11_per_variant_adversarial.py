"""QUAL-R1.1 per-variant executable adversarial qualification probe.

Unlike a TSV mention, this suite PROVES each inventoried HC variant executed
successfully in existing independent model tests, then runs real tampering
against that same accepted model/variant/input/config.

It does NOT claim 48 independent mathematical S2 approvals: a later gate
must still check family-specific financial oracles, signed upstream sources,
and real production integration. No FIN/Redis/Rust.
"""
from __future__ import annotations

import copy
import csv
import re
import unittest
from decimal import Decimal, localcontext
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

from fengine_hc.reference import CalculationError, ReferenceEngine

ROOT = Path(__file__).resolve().parents[1]
TEST_MODULES = (
    "test_fengine_hc_reference",
    "test_fengine_hc_r02_math",
    "test_fengine_hc_r03_reference",
    "test_fengine_hc_r04_reference",
    "test_fengine_hc_r05_cashflow",
    "test_fengine_hc_r06_fcfe",
    "test_fengine_hc_r07_pvm",
)
DECIMAL_LITERAL = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\Z")


def clone_reference_input(value):
    """Clone accepted nested MappingProxyType without mutating model fixtures."""
    if isinstance(value, Mapping):
        return {clone_reference_input(key): clone_reference_input(part)
                for key, part in value.items()}
    if isinstance(value, list):
        return [clone_reference_input(part) for part in value]
    if isinstance(value, tuple):
        return tuple(clone_reference_input(part) for part in value)
    return copy.deepcopy(value)


def mutate_one_known_numeric(value):
    """Purely change ONE existing numeric leaf, without changing field schema."""
    if isinstance(value, dict):
        for key, item in value.items():
            changed, accepted = mutate_one_known_numeric(item)
            if accepted:
                update = copy.deepcopy(value)
                update[key] = changed
                return update, True
    elif isinstance(value, list):
        for index, item in enumerate(value):
            changed, accepted = mutate_one_known_numeric(item)
            if accepted:
                update = copy.deepcopy(value)
                update[index] = changed
                return update, True
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            changed, accepted = mutate_one_known_numeric(item)
            if accepted:
                update = list(copy.deepcopy(value))
                update[index] = changed
                return tuple(update), True
    elif isinstance(value, str) and DECIMAL_LITERAL.fullmatch(value):
        return format(Decimal(value) + Decimal("1"), "f"), True
    elif type(value) is int:
        return value + 1, True
    elif isinstance(value, Decimal):
        return value + Decimal(1), True
    return value, False


def successful_variant_fixtures(inventory):
    """Capture accepted real calls from all seven existing HC unit suites.

    The suite runs under a patch only while the original math tests execute.
    Exceptions from intentional negative tests are NOT added as success proof.
    """
    original = ReferenceEngine.calculate
    collected = {}

    def record(self, model, variant, inputs, config, *, reference_mode=False):
        outcome = original(self, model, variant, inputs, config,
                           reference_mode=reference_mode)
        key = (model, variant)
        if reference_mode and key not in collected:
            collected[key] = (clone_reference_input(inputs), clone_reference_input(config))
        return outcome

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(module))
    with localcontext() as decimal_ctx, patch.object(
        ReferenceEngine, "calculate", record
    ):
        # The seven independent golden suites expect >32 significant digits.
        # They must not depend on an unrelated test setting global Decimal
        # precision during the surrounding unittest discovery process.
        decimal_ctx.prec = 60
        nested = unittest.TestResult()
        suite.run(nested)
    if not nested.wasSuccessful():
        messages = [
            (case.id(), error[-500:])
            for case, error in nested.errors + nested.failures
        ]
        raise AssertionError(f"INDEPENDENT_MODEL_SUITE_FAILED: {messages[:8]}")
    return collected, nested.testsRun


class PerVariantAdversarialQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "catalog" / "hc_reference_execution_inventory_r1.tsv").open(
            encoding="utf-8", newline=""
        ) as stream:
            records = list(csv.DictReader(stream, delimiter="\t"))
        cls.inventory = {(r["modelCode"], r["variantCode"]) for r in records}
        if len(records) != 48 or len(cls.inventory) != 48:
            raise AssertionError("EXPECTED_48_UNIQUE_REFERENCE_VARIANTS")
        cls.samples, cls.existing_test_count = successful_variant_fixtures(cls.inventory)
        cls.engine = ReferenceEngine(ROOT)

    def test_every_variant_has_an_observed_successful_real_mathematical_execution(self):
        missing = sorted(self.inventory - self.samples.keys())
        unexpected = sorted(self.samples.keys() - self.inventory)
        self.assertEqual(missing, [], msg=f"NO_SUCCESSFUL_MODEL_EXECUTION: {missing}")
        self.assertEqual(unexpected, [],
                         msg=f"SUCCESSFUL_VARIANT_NOT_DECLARED_IN_QUALIFICATION_INVENTORY: {unexpected}")
        self.assertEqual(len(self.samples), 48)
        self.assertGreater(self.existing_test_count, 50)

    def test_each_variant_accepts_exact_replay_and_has_stable_result_hash(self):
        for (model, variant), (inputs, config) in sorted(self.samples.items()):
            with self.subTest(model=model, variant=variant):
                expected = self.engine.calculate(model, variant, inputs, config,
                                                 reference_mode=True)
                repeated = self.engine.calculate(model, variant,
                                                 copy.deepcopy(inputs),
                                                 copy.deepcopy(config),
                                                 reference_mode=True)
                self.assertEqual(expected.output_sha256, repeated.output_sha256)
                self.assertEqual(expected.inputs_sha256, repeated.inputs_sha256)
                self.assertEqual(expected.config_sha256, repeated.config_sha256)
                self.assertEqual(expected.execution_class,
                                 "PYTHON_REFERENCE_NOT_S2")

    def test_each_variant_blocks_unsigned_financial_production_execution(self):
        for (model, variant), (inputs, config) in sorted(self.samples.items()):
            with self.subTest(model=model, variant=variant):
                with self.assertRaises(CalculationError) as exception:
                    self.engine.calculate(model, variant, inputs, config)
                self.assertEqual(exception.exception.code, "FINANCIAL_S2_REQUIRED")

    def test_each_variant_blocks_unknown_config_injection(self):
        for (model, variant), (inputs, config) in sorted(self.samples.items()):
            with self.subTest(model=model, variant=variant):
                injected = {**config, "__qual_r1_unknown_policy__": "TRUE"}
                with self.assertRaises(CalculationError) as exception:
                    self.engine.calculate(model, variant, inputs, injected,
                                          reference_mode=True)
                self.assertEqual(exception.exception.code, "UNKNOWN_PARAMETER")

    def test_each_variant_blocks_unknown_input_injection_instead_of_ignoring_it(self):
        for (model, variant), (inputs, config) in sorted(self.samples.items()):
            with self.subTest(model=model, variant=variant):
                injected = {**inputs, "__qual_r1_unconsumed_input__": "999999"}
                with self.assertRaises(CalculationError) as exception:
                    self.engine.calculate(model, variant, injected, config,
                                          reference_mode=True)
                self.assertTrue(exception.exception.code,
                                msg="UNTYPED_MODEL_INPUT_ERROR")

    def test_each_variant_binds_known_numeric_mutation_to_result_or_blocks_it(self):
        for (model, variant), (inputs, config) in sorted(self.samples.items()):
            with self.subTest(model=model, variant=variant):
                changed, has_numeric = mutate_one_known_numeric(inputs)
                self.assertTrue(has_numeric,
                                msg="NO_MUTABLE_NUMERIC_INPUT_IN_ACCEPTED_FIXTURE")
                previous = self.engine.calculate(model, variant, inputs, config,
                                                 reference_mode=True)
                try:
                    mutated = self.engine.calculate(model, variant, changed, config,
                                                    reference_mode=True)
                except CalculationError as exception:
                    self.assertTrue(exception.code,
                                    msg="MISSING_FAIL_CLOSED_CODE")
                else:
                    self.assertNotEqual(previous.inputs_sha256, mutated.inputs_sha256)
                    self.assertNotEqual(previous.output_sha256, mutated.output_sha256,
                                        msg="KNOWN_INPUT_TAMPER_NOT_BOUND_TO_RECEIPT")

    def test_all_48_variants_execute_with_no_binary_float_acceptance(self):
        for (model, variant), (inputs, config) in sorted(self.samples.items()):
            with self.subTest(model=model, variant=variant):
                # Even when the field is injected at top level, the canonical
                # request fingerprint must reject binary floating-point data.
                injected = {**inputs, "__qual_r1_binary_float__": 0.1}
                with self.assertRaises(CalculationError) as exception:
                    self.engine.calculate(model, variant, injected, config,
                                          reference_mode=True)
                self.assertEqual(exception.exception.code, "BINARY_FLOAT_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
