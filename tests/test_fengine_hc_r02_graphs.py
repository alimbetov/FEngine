"""HC-R0.2C — verified model port bindings, plan fingerprints and immutable inputs."""
import unittest
from pathlib import Path
from decimal import Decimal
from fengine_hc import CalculationError, ReferenceEngine
from fengine_hc.graphs import CalculationJob, InMemoryCalculationPlan, InputBinding

ROOT = Path(__file__).resolve().parents[1]


class ModelPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def capm(self, inputs=None):
        return CalculationJob("capm", "HC.CAP.01", "CAPM_BASE",
                              inputs or {"riskFreeRate": "0.04", "beta": "1.2",
                                         "marketRiskPremium": "0.06"}, {})

    def wacc(self, link="costOfEquity"):
        return CalculationJob(
            "wacc", "HC.CAP.02", "MARKET_VALUE_WACC",
            {"equityValue": "60", "debtValue": "40",
             "costOfDebt": "0.08", "taxRate": "0.25"}, {},
            (InputBinding("capm", "costOfEquity", link),)
        )

    def test_typed_capm_to_wacc_plan(self):
        p = InMemoryCalculationPlan(self.engine, [self.wacc(), self.capm()])
        self.assertEqual(p.order, ("capm", "wacc"))
        self.assertEqual(len(p.plan_sha256), 64)
        output = p.execute(reference_mode=True)
        self.assertEqual(Decimal(output["capm"].output["costOfEquity"]), Decimal("0.112"))
        self.assertEqual(Decimal(output["wacc"].output["wacc"]), Decimal("0.0912"))
        with self.assertRaises(TypeError):
            output["wacc"] = "spoofed"

    def test_unknown_port_pair_rejected_at_compile(self):
        with self.assertRaises(CalculationError) as raised:
            InMemoryCalculationPlan(self.engine, [self.capm(), self.wacc("nonReviewedRate")])
        self.assertEqual(raised.exception.code, "MODEL_BINDING_NOT_REVIEWED")

    def test_plan_deep_snapshot_cannot_be_mutated(self):
        source = {"riskFreeRate": "0.04", "beta": "1.2", "marketRiskPremium": "0.06"}
        plan = InMemoryCalculationPlan(self.engine, [self.capm(source), self.wacc()])
        sha = plan.plan_sha256
        source["beta"] = "4"
        self.assertEqual(plan.plan_sha256, sha)
        self.assertEqual(Decimal(plan.execute(reference_mode=True)["wacc"].output["wacc"]),
                         Decimal("0.0912"))
        with self.assertRaises(TypeError):
            plan.jobs["capm"].inputs["beta"] = "999"

    def test_plan_changes_with_input_snapshot(self):
        a = InMemoryCalculationPlan(self.engine, [self.capm()])
        b = InMemoryCalculationPlan(self.engine, [
            self.capm({"riskFreeRate": "0.04", "beta": "1.3",
                       "marketRiskPremium": "0.06"})
        ])
        self.assertNotEqual(a.plan_sha256, b.plan_sha256)

    def test_non_reference_execution_remains_closed(self):
        plan = InMemoryCalculationPlan(self.engine, [self.capm()])
        with self.assertRaises(CalculationError) as err:
            plan.execute()
        self.assertEqual(err.exception.code, "FINANCIAL_S2_REQUIRED")


if __name__ == "__main__":
    unittest.main()
