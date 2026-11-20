"""Shared QUAL-R1 invariant patterns for every newly qualified reference model.

This is intentionally a reusable *test harness*, not application code.
Never rely on a success-only golden: also perturb identity, source coverage,
time boundary, dimension, magnitude, and/or policy and check fail-closed
semantics with an unchanged/recomputed independent oracle.

Import from actual tests as: from qualification_integrity_patterns import ...
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from decimal import Decimal
from typing import Any

PATTERN_IDS = frozenset({
    "INDEPENDENT_NUMERIC_ORACLE",
    "METAMORPHIC_ORDER",
    "SOURCE_SCOPE_ISOLATION",
    "ATOMIC_DIMENSION_ALIGNMENT",
    "COHORT_PRESERVATION",
    "INTERVAL_NONOVERLAP",
    "WEIGHT_PAIR_ALIGNMENT",
    "SOURCE_REVISION_DRIFT",
    "UNREVIEWED_AGGREGATION_DENIAL",
    "FINANCIAL_BALANCE_CONSERVATION",
    "TEMPORAL_COMPONENT_RECOMPUTE",
    "NONLINEAR_FULL_WINDOW_REEXECUTE",
    "IMMUTABLE_RESULT_RECEIPT",
    "S2_FAIL_CLOSED",
})
# These patterns may be combined. Not every method is temporally aggregatable.
CORE_PATTERNS = frozenset({
    "INDEPENDENT_NUMERIC_ORACLE", "SOURCE_REVISION_DRIFT",
    "IMMUTABLE_RESULT_RECEIPT", "S2_FAIL_CLOSED",
})
FAMILY_PATTERNS = {
    "ASSET": frozenset({"FINANCIAL_BALANCE_CONSERVATION", "METAMORPHIC_ORDER"}),
    "CAP": frozenset({"WEIGHT_PAIR_ALIGNMENT", "ATOMIC_DIMENSION_ALIGNMENT"}),
    "CASH": frozenset({"FINANCIAL_BALANCE_CONSERVATION", "COHORT_PRESERVATION"}),
    "COST": frozenset({"FINANCIAL_BALANCE_CONSERVATION", "SOURCE_REVISION_DRIFT"}),
    "DCF": frozenset({"NONLINEAR_FULL_WINDOW_REEXECUTE", "UNREVIEWED_AGGREGATION_DENIAL"}),
    "ECL": frozenset({"ATOMIC_DIMENSION_ALIGNMENT", "SOURCE_REVISION_DRIFT"}),
    "LOAN": frozenset({"FINANCIAL_BALANCE_CONSERVATION", "INTERVAL_NONOVERLAP"}),
    "PF": frozenset({"TEMPORAL_COMPONENT_RECOMPUTE", "UNREVIEWED_AGGREGATION_DENIAL"}),
    "RISK": frozenset({"NONLINEAR_FULL_WINDOW_REEXECUTE", "SOURCE_REVISION_DRIFT"}),
    "SET": frozenset({"INTERVAL_NONOVERLAP", "ATOMIC_DIMENSION_ALIGNMENT"}),
    "STOCK": frozenset({"FINANCIAL_BALANCE_CONSERVATION", "SOURCE_REVISION_DRIFT"}),
}

def required_patterns(model_code: str) -> frozenset[str]:
    parts = model_code.split(".")
    if len(parts) != 3 or parts[0] != "HC" or parts[1] not in FAMILY_PATTERNS:
        raise ValueError("UNREGISTERED_QUALIFICATION_FAMILY")
    return CORE_PATTERNS | FAMILY_PATTERNS[parts[1]]


def exact_decimal(value: Any) -> Decimal:
    """Never compare financial values as binary floats."""
    if type(value) is float or isinstance(value, bool):
        raise ValueError("BINARY_FLOAT_FORBIDDEN")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("NONFINITE_DECIMAL")
    return result


def same_numeric(actual: Any, expected: Any, *, tolerance: str = "0") -> None:
    if abs(exact_decimal(actual) - exact_decimal(expected)) > Decimal(tolerance):
        raise AssertionError("INDEPENDENT_NUMERIC_ORACLE_MISMATCH")


def conserved(terms: Iterable[Any], expected: Any, *, tolerance: str = "0") -> None:
    with __import__("decimal").localcontext() as ctx:
        ctx.prec = 60
        total = sum((exact_decimal(x) for x in terms), Decimal(0))
        same_numeric(total, expected, tolerance=tolerance)


def rejects_code(run: Callable[[], Any], expected: str,
                 error_type: type[BaseException]) -> None:
    """Wrong error code is a test failure, not a vaguely acceptable refusal."""
    try:
        run()
    except error_type as error:
        if getattr(error, "code", None) != expected:
            raise AssertionError("UNEXPECTED_ERROR_CODE") from error
        return
    raise AssertionError("EXPECTED_FAIL_CLOSED_ERROR")


def same_replay(run: Callable[[list[Any]], Any], rows: list[Any],
                identity: Callable[[Any], Any]) -> None:
    if identity(run(rows)) != identity(run(list(reversed(rows)))):
        raise AssertionError("NONDETERMINISTIC_REPLAY")


def mutation_changes_receipt(
    calculate: Callable[[Any], Any], baseline: Any, mutated: Any,
    identity: Callable[[Any], Any],
) -> None:
    if identity(calculate(baseline)) == identity(calculate(mutated)):
        raise AssertionError("SOURCE_MUTATION_NOT_BOUND_TO_RECEIPT")
