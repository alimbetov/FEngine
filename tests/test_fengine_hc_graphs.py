"""Reference DAG/strategy tests; candidate links are never admitted bindings."""
from pathlib import Path
from decimal import Decimal
import unittest

from fengine_hc import CalculationError, ContractRegistry, ReferenceEngine
from fengine_hc.graphs import (
    CalculationJob, CandidateModelGraph, InMemoryCalculationPlan,
    InputBinding, StrategyGraph, StrategyState, StrategyTransition,
)

ROOT = Path(__file__).resolve().parents[1]


class ReferenceGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def fails(self, code, thunk):
        with self.assertRaises(CalculationError) as raised:
            thunk()
        self.assertEqual(raised.exception.code, code)

    def test_complete_model_node_set_and_candidate_edges(self):
        graph = CandidateModelGraph(ROOT)
        self.assertEqual(len(graph.models), 116)
        self.assertEqual(len(graph.order), 116)
        self.assertTrue(len(graph.edges) >= 20)
        self.assertTrue(all(e.qualification == "CANDIDATE_NO_TYPED_RESULT_BINDING" for e in graph.edges))
        self.assertIn(("HC.CAP.01", "HC.CAP.02"),
                      {(e.source_model, e.target_model) for e in graph.edges})

    def test_capm_result_to_wacc_bound_plan(self):
        jobs = [
            CalculationJob("capm", "HC.CAP.01", "CAPM_BASE",
                           {"riskFreeRate": "0.04", "beta": "1.2", "marketRiskPremium": "0.06"}, {}),
            CalculationJob("wacc", "HC.CAP.02", "MARKET_VALUE_WACC",
                           {"equityValue": "60", "debtValue": "40", "costOfDebt": "0.08",
                            "taxRate": "0.25"}, {},
                           (InputBinding("capm", "costOfEquity", "costOfEquity"),)),
        ]
        plan = InMemoryCalculationPlan(self.engine, list(reversed(jobs)))
        self.assertEqual(plan.order, ("capm", "wacc"))
        out = plan.execute(reference_mode=True)
        self.assertEqual(Decimal(out["wacc"].output["wacc"]), Decimal("0.0912"))

    def test_cyclic_bindings_fail(self):
        a = CalculationJob("a", "HC.CAP.01", "CAPM_BASE", {}, {},
                           (InputBinding("b", "someOutput", "riskFreeRate"),))
        b = CalculationJob("b", "HC.CAP.02", "MARKET_VALUE_WACC", {}, {},
                           (InputBinding("a", "costOfEquity", "costOfEquity"),))
        self.fails("DAG_CYCLE", lambda: InMemoryCalculationPlan(self.engine, [a, b]))

    def test_binding_override_and_missing_job_fail(self):
        a = CalculationJob("a", "HC.CAP.01", "CAPM_BASE", {"riskFreeRate": "0.02"}, {},
                           (InputBinding("other", "value", "riskFreeRate"),))
        self.fails("INPUT_BINDING_OVERRIDE", lambda: InMemoryCalculationPlan(self.engine, [a]))
        b = CalculationJob("a", "HC.CAP.01", "CAPM_BASE", {}, {},
                           (InputBinding("other", "value", "riskFreeRate"),))
        self.fails("UNKNOWN_DAG_NODE", lambda: InMemoryCalculationPlan(self.engine, [b]))

    def test_strategy_is_distinct_from_calculation_graph(self):
        r = ContractRegistry(ROOT)
        states = [StrategyState("start", frozenset({"CAP"}), "ENTRY"),
                  StrategyState("approve", frozenset({"CAP"}), "ACTION"),
                  StrategyState("reject", frozenset({"CAP"}), "TERMINAL")]
        e = [
            StrategyTransition("start", "approve", "HC.CAP.02", "wacc", "LT", "0.10"),
            StrategyTransition("start", "reject", "HC.CAP.02", "wacc", "GE", "0.10"),
        ]
        graph = StrategyGraph(r, states, e)
        self.assertTrue(graph.condition(e[0], "0.0912"))
        self.assertFalse(graph.condition(e[1], "0.0912"))

    def test_strategy_cycle_rejected(self):
        r = ContractRegistry(ROOT)
        states = [StrategyState("a", frozenset(), "ENTRY"),
                  StrategyState("b", frozenset(), "DECISION")]
        e = [StrategyTransition("a", "b", "HC.CAP.02", "wacc", "LT", "1"),
             StrategyTransition("b", "a", "HC.CAP.02", "wacc", "GE", "1")]
        self.fails("DAG_CYCLE", lambda: StrategyGraph(r, states, e))


if __name__ == "__main__":
    unittest.main()
