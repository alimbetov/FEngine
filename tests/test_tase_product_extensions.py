"""Product extensibility and catalog/parameter completeness checks for TASE.

This verifies the reference architecture is declarative. It does not approve
draft Product Packs, financial formulas, signatures, or production tenants.
"""
from __future__ import annotations

import csv
import io
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from shutil import copyfile

from tase import Catalog, Dataset, Observation, PeriodRequest, TaseError, calculate

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "tase_operator_candidates_r0.tsv",
    "tase_input_predicates_r0.tsv",
    "tase_product_pack_candidates_r0.tsv",
    "tase_metric_semantics_candidates_r0.tsv",
)


class ProductExtensibilityTests(unittest.TestCase):
    def test_new_product_and_metric_without_python_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "catalog"
            directory.mkdir()
            for filename in NAMES:
                copyfile(ROOT / "catalog" / filename, directory / filename)
            with (directory / "tase_product_pack_candidates_r0.tsv").open("a", encoding="utf-8") as f:
                f.write("EXPERIMENT\tTENANT.EXPERIMENT\tEXPERIMENT.R0.1\tOTHER\t"
                        "MONTH,QUARTER\tSUM\tBASIC\tclient-defined typed flow only\t"
                        "YES\tDRAFT_NO_SIGNATURE_NO_ADMISSION\n")
            with (directory / "tase_metric_semantics_candidates_r0.tsv").open("a", encoding="utf-8") as f:
                f.write("EXPERIMENT\tNET_FLOW\tMONEY\tKZT\tFLOW\tINTERVAL_FLOW\tSUM\t"
                        "SUM\t\t\tqualified economic flows\tDRAFT_SEMANTIC_CANDIDATE\n")
            catalog = Catalog.load(Path(tmp), reference_mode=True)
            self.assertIn("EXPERIMENT", catalog.products)
            self.assertIn(("EXPERIMENT", "NET_FLOW"), catalog.metrics)
            observations = tuple(
                Observation("EXPERIMENT", "NET_FLOW", "S", start, value, "KZT",
                            "a"*64, end=end)
                for start, end, value in (
                    (date(2026, 1, 1), date(2026, 2, 1), "100"),
                    (date(2026, 2, 1), date(2026, 3, 1), "120"),
                    (date(2026, 3, 1), date(2026, 4, 1), "80"),
                )
            )
            out = calculate(catalog, PeriodRequest(
                "EXPERIMENT", "NET_FLOW", "SUM", "S",
                date(2026, 1, 1), date(2026, 4, 1), "QUARTER"),
                Dataset("S", "b"*64, observations,
                        interval_coverage_attested=True, watermark=date(2026, 4, 1)))
            self.assertEqual(out.rows[0].value, "300")
            self.assertEqual(out.execution_class, "PYTHON_REFERENCE_NOT_S2")
            with self.assertRaises(TaseError) as cm:
                Catalog.load(Path(tmp))
            self.assertEqual(cm.exception.code, "UNAPPROVED_PRODUCT_PACK")

    def test_unapproved_new_operator_rejected_at_catalog_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "catalog"
            directory.mkdir()
            for filename in NAMES:
                copyfile(ROOT / "catalog" / filename, directory / filename)
            path = directory / "tase_product_pack_candidates_r0.tsv"
            lines = path.read_text(encoding="utf-8").splitlines()
            columns = lines[0].split("\t")
            idx = columns.index("candidateOperators")
            for line_index in range(1, len(lines)):
                parts = lines[line_index].split("\t")
                if parts[0] == "FIN":
                    parts[idx] += ",UNREVIEWED_EVAL"
                    lines[line_index] = "\t".join(parts)
                    break
            else:
                self.fail("FIN Product Pack not found")
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(TaseError) as cm:
                Catalog.load(Path(tmp), reference_mode=True)
            self.assertEqual(cm.exception.code, "PRODUCT_UNKNOWN_OPERATOR")

    def test_all_62_metric_operator_edges_have_typed_predicates(self):
        catalog = Catalog.load(ROOT, reference_mode=True)
        edges = 0
        for metric in catalog.metrics.values():
            for op_code in metric.operators:
                edges += 1
                op = catalog.operators[op_code]
                self.assertTrue(any(
                    metric.kind in catalog.predicates[p].quantity_kinds
                    and metric.logical_type in catalog.predicates[p].logical_types
                    and metric.time_kind in catalog.predicates[p].time_kinds
                    for p in op.predicates
                ), msg=f"{metric.product}:{metric.code}:{op_code}")
        self.assertEqual(edges, 62)

    def test_invalid_semantic_operator_edge_blocks_product_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "catalog"
            directory.mkdir()
            for filename in NAMES:
                copyfile(ROOT / "catalog" / filename, directory / filename)
            path = directory / "tase_metric_semantics_candidates_r0.tsv"
            lines = path.read_text(encoding="utf-8").splitlines()
            idx = lines[0].split("\t").index("allowedOperatorIds")
            for line_number in range(1, len(lines)):
                fields = lines[line_number].split("\t")
                if fields[0] == "FIN" and fields[1] == "REVENUE":
                    fields[idx] += ",LAST_AS_OF"
                    lines[line_number] = "\t".join(fields)
                    break
            else:
                self.fail("FIN.REVENUE not found")
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(TaseError) as cm:
                Catalog.load(Path(tmp), reference_mode=True)
            self.assertEqual(cm.exception.code, "METRIC_OPERATOR_TYPE_MISMATCH")

    def test_physical_unit_intensity_not_percentage(self):
        catalog = Catalog.load(ROOT, reference_mode=True)
        observations = (
            Observation("INDUSTRY", "ENERGY_KWH", "S", date(2026, 1, 1),
                        "300", "kWh", "a"*64, end=date(2026, 2, 1)),
            Observation("INDUSTRY", "OUTPUT_UNITS", "S", date(2026, 1, 1),
                        "100", "unit", "a"*64, end=date(2026, 2, 1)),
        )
        r = PeriodRequest("INDUSTRY", "ENERGY_INTENSITY", "RATIO_OF_SUMS",
                          "S", date(2026, 1, 1), date(2026, 2, 1), "MONTH")
        out = calculate(catalog, r, Dataset(
            "S", "b"*64, observations,
            interval_coverage_attested=True, watermark=date(2026, 2, 1)))
        self.assertEqual(out.rows[0].value, "3")
        self.assertEqual(out.rows[0].unit, "kWh/unit")

    def test_parameter_inventory_116_417_candidates_not_approved(self):
        path = ROOT / "catalog" / "model_parameter_inventory_116_r0.tsv"
        with path.open(encoding="utf-8", newline="") as fp:
            rows = list(csv.DictReader(fp, delimiter="\t"))
        self.assertEqual(len(rows), 417)
        self.assertEqual(len({r["modelCode"] for r in rows}), 116)
        self.assertEqual(len({(r["modelCode"], r["parameterCode"]) for r in rows}), 417)
        self.assertEqual(sum(r["sourceRegistry"] == "R95_PARAMS_R1" for r in rows), 310)
        self.assertEqual(sum(r["sourceRegistry"] == "W5_FORMULA_R2" for r in rows), 107)
        self.assertTrue(all(r["domainReview"] == "PENDING" for r in rows))
        self.assertTrue(all(r["financialS2"] == "NOT_APPROVED" for r in rows))

    def test_all_operator_input_predicate_references_resolve(self):
        catalog = Catalog.load(ROOT, reference_mode=True)
        for operator in catalog.operators.values():
            self.assertTrue(operator.predicates)
            self.assertTrue(operator.predicates <= catalog.predicates.keys())


if __name__ == "__main__":
    unittest.main()
