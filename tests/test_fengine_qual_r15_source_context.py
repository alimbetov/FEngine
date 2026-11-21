"""QUAL-R1.5 deterministic synthetic adversarial context compatibility."""
from __future__ import annotations

import random
import unittest
from dataclasses import replace

from fengine_hc.reference import CalculationError, fingerprint
from fengine_hc.source_context_r15 import SourceContext, execute_guarded, validate_contexts

SHA = "a" * 64
ROLES = frozenset({"EQUITY", "DEBT"})


def source(role: str, value: str = "100") -> tuple[SourceContext, dict]:
    payload = {"capital": value}
    return SourceContext(
        source_id="synthetic-" + role,
        role=role,
        user_id="synthetic-user",
        project_id="synthetic-project",
        currency="KZT",
        period_start="2026-01-01",
        period_end="2026-01-31",
        period_type="MONTH",
        sku_set=("SKU_A",),
        methodology_id="HC.CAP.02",
        methodology_version="1.0.0",
        methodology_sha256=SHA,
        payload_sha256=fingerprint(payload),
    ), payload


class QualR15SourceContext(unittest.TestCase):
    def setUp(self):
        a, pa = source("EQUITY")
        b, pb = source("DEBT")
        self.base = (a, b)
        self.payloads = {"EQUITY": pa, "DEBT": pb}

    def fail_code(self, sources, expected, *, single_sku=False):
        calls = []
        with self.assertRaises(CalculationError) as err:
            execute_guarded(
                sources, self.payloads, required_roles=ROLES,
                executor=lambda p: calls.append(p), single_sku=single_sku,
            )
        self.assertEqual(err.exception.code, expected)
        self.assertEqual(calls, [], "executor must never run after rejection")

    def test_valid_permutation_and_exact_payload_binding(self):
        calls = []
        def executor(payloads):
            calls.append(1)
            return int(payloads["EQUITY"]["capital"]) + int(payloads["DEBT"]["capital"])
        receipt, result = execute_guarded(
            self.base, self.payloads, required_roles=ROLES, executor=executor, single_sku=True,
        )
        self.assertEqual(result, 200)
        self.assertEqual(calls, [1])
        self.assertEqual(receipt, validate_contexts(self.base[::-1], required_roles=ROLES))
        self.assertEqual(len(receipt), 64)

    def test_800_seeded_single_axis_context_mutations_fail_closed(self):
        rng = random.Random(0xC0151501)
        mutations = (
            ("currency", "USD", "CROSS_CURRENCY_DATASET"),
            ("period_start", "2026-02-01", "INVALID_PERIOD_CONTEXT"),
            ("period_end", "2026-02-28", "CROSS_PERIOD_DATASET"),
            ("period_type", "QUARTER", "CROSS_PERIOD_DATASET"),
            ("sku_set", ("SKU_B",), "CROSS_SKU_DATASET"),
            ("methodology_id", "HC.CAP.03", "CROSS_METHODOLOGY_DATASET"),
            ("methodology_version", "2.0.0", "CROSS_METHODOLOGY_DATASET"),
            ("methodology_sha256", "b" * 64, "CROSS_METHODOLOGY_DATASET"),
        )
        count = 0
        for iteration in range(100):
            for field, value, code in rng.sample(list(mutations), len(mutations)):
                with self.subTest(iteration=iteration, field=field):
                    self.fail_code((self.base[0], replace(self.base[1], **{field: value})), code)
                    count += 1
        self.assertEqual(count, 800)

    def test_scope_identity_and_role_rejections(self):
        self.fail_code((self.base[0], replace(self.base[1], project_id="other")), "CROSS_SCOPE_DATASET")
        self.fail_code((self.base[0], replace(self.base[1], user_id="other")), "CROSS_SCOPE_DATASET")
        self.fail_code((self.base[0], replace(self.base[1], role="EQUITY")), "SOURCE_ROLE_MISMATCH")
        self.fail_code((self.base[0], replace(self.base[1], source_id="synthetic-EQUITY")), "DUPLICATE_SOURCE_ID")
        self.fail_code((self.base[0],), "SOURCE_ROLE_MISMATCH")

    def test_noncanonical_sku_and_unsupported_multi_sku_pool(self):
        self.fail_code(tuple(replace(s, sku_set=("SKU_B", "SKU_A")) for s in self.base), "NONCANONICAL_SKU_CONTEXT")
        self.fail_code(tuple(replace(s, sku_set=("SKU_A", "SKU_B")) for s in self.base), "MULTI_SKU_POOL_UNSUPPORTED", single_sku=True)

    def test_payload_mutation_is_rejected_before_execution(self):
        corrupted = dict(self.payloads)
        corrupted["DEBT"] = {"capital": "999"}
        calls = []
        with self.assertRaises(CalculationError) as err:
            execute_guarded(
                self.base, corrupted, required_roles=ROLES,
                executor=lambda p: calls.append(p),
            )
        self.assertEqual(err.exception.code, "SOURCE_PAYLOAD_DIGEST_MISMATCH")
        self.assertFalse(calls)

    def test_version_and_digest_binding_changes_receipt_for_compatible_sources(self):
        bumped = tuple(replace(s, methodology_version="1.0.1") for s in self.base)
        changed = tuple(replace(s, methodology_sha256="b" * 64) for s in self.base)
        base = validate_contexts(self.base, required_roles=ROLES)
        self.assertNotEqual(base, validate_contexts(bumped, required_roles=ROLES))
        self.assertNotEqual(base, validate_contexts(changed, required_roles=ROLES))

    def test_rejects_malformed_calendar_and_missing_roles(self):
        self.fail_code((self.base[0], replace(self.base[1], period_end="2026-02-30")), "INVALID_PERIOD_CONTEXT")
        self.fail_code((self.base[0], replace(self.base[1], methodology_sha256="INVALID")), "INVALID_METHODOLOGY_DIGEST")
        self.fail_code((self.base[0], replace(self.base[1], currency="kzt")), "INVALID_CURRENCY_CONTEXT")


if __name__ == "__main__":
    unittest.main()
