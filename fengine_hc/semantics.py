"""HC-R0.2A — pre-freeze typed parameter semantics and bounded variant resolver.

Legacy R3 rows are candidate *bindings*, never global semantic identities or
finance approvals. Matching name/type is not sufficient to merge semantics.
Only explicitly reviewed reference-mode rules may resolve a variant. The
result is a non-admitted immutable snapshot, NOT a MethodologyRevision.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .reference import CalculationError, ContractRegistry, day, fingerprint, integer, number, _freeze

# Known name collisions must be disambiguated until actual finance semantics
# and contract-type migration are reviewed. Never rewrite legacy R3 TSVs.
KNOWN_TYPE_COLLISIONS = frozenset({
    "calendarPolicy", "taxShieldEligibility", "horizon", "dayCount", "capitalBudget",
})
SUPPORTED_TYPES = frozenset({
    "REFERENCE", "CODE", "ENUM", "BOOLEAN", "INTEGER", "INT64", "RATE", "MONEY",
    "DECIMAL", "RATIO", "MONEY_PER_UNIT", "DATE", "LOCAL_DATE", "PERIOD", "QUANTITY", "LIST",
    "STRUCT", "FX", "ISO4217", "PERCENTAGE", "DISTRIBUTION", "CURVE",
})


@dataclass(frozen=True)
class ParameterBinding:
    model_code: str
    name: str
    logical_type: str
    semantic_candidate_id: str
    approval: str


@dataclass(frozen=True)
class ResolvedVariant:
    model_code: str
    variant_code: str
    config: Mapping[str, Any]
    config_sha256: str
    status: str = "REFERENCE_NOT_S2"


@dataclass(frozen=True)
class VariantRule:
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    enums: tuple[tuple[str, tuple[str, ...]], ...] = ()
    sha256_references: tuple[str, ...] = ()


# No generic permissive fallback: a rule must exist before an R3 variant can
# be *resolved*. A registered variant without a rule remains draft-only.
RULES: dict[tuple[str, str], VariantRule] = {
    ("HC.DCF.01", "PERIOD_END_NPV"):
        VariantRule((), ("timingConvention",), (("timingConvention", ("PERIOD_END",)),)),
    ("HC.DCF.01", "MIDPERIOD_NPV"):
        VariantRule((), ("timingConvention",), (("timingConvention", ("MIDPERIOD",)),)),
    ("HC.DCF.02", "EXACT_DATE_XNPV"):
        VariantRule(("dayCount",), (), (("dayCount", ("ACT_365_FIXED",)),)),
    ("HC.DCF.03", "ALL_REAL_IRR_ROOTS"):
        VariantRule(("rootDomain", "rootCompletenessPolicy"), (),
                    (("rootCompletenessPolicy", ("CERTIFIED_ALL",)),)),
    ("HC.DCF.03", "SINGLE_IF_UNAMBIGUOUS"):
        VariantRule(("rootDomain", "rootCompletenessPolicy"), (),
                    (("rootCompletenessPolicy", ("CERTIFIED_ALL",)),)),
    ("HC.LOAN.03", "EIR_ORIGINAL"):
        VariantRule(("discountOrigin", "rootCompletenessPolicy"), (),
                    (("rootCompletenessPolicy", ("CERTIFIED_ALL",)),)),
    ("HC.RISK.02", "EMPIRICAL_LEFT_QUANTILE"):
        VariantRule(("alpha", "lossSignPolicy", "quantileDefinition"), (),
                    (("lossSignPolicy", ("POSITIVE_LOSS",)),
                     ("quantileDefinition", ("NEAREST_RANK",)),)),
    ("HC.RISK.03", "QUANTILE_INTEGRAL_ES"):
        VariantRule(("confidenceAlpha", "esTailMassRule"), (),
                    (("esTailMassRule", ("QUANTILE_INTEGRAL_FRACTIONAL_ATOM",)),)),
    ("HC.ECL.02", "FIRST_12_MONTH_DEFAULT_EVENTS"):
        VariantRule(("defaultEventWindow",), (),
                    (("defaultEventWindow", ("FIRST_12_MONTHS",)),)),
    ("HC.ECL.03", "LIFETIME_TERM_PD"):
        VariantRule(("hazardConditionality",), (),
                    (("hazardConditionality", ("CONDITIONAL_PD",)),)),
    ("HC.CASH.03", "DETERMINISTIC_RUNWAY"):
        VariantRule(("floorValue", "firstPassageRule"), (),
                    (("firstPassageRule", ("STRICT_BELOW_FLOOR", "AT_OR_BELOW_FLOOR")),)),
    ("HC.CASH.03", "SCENARIO_RUNWAY"):
        VariantRule(("floorValue", "firstPassageRule"), (),
                    (("firstPassageRule", ("STRICT_BELOW_FLOOR", "AT_OR_BELOW_FLOOR")),)),
    ("HC.COST.04", "SINGLE_PRODUCT_BREAKEVEN"):
        VariantRule(("minimumLotRule",), (),
                    (("minimumLotRule", ("WHOLE_UNITS",)),)),
    ("HC.COST.04", "PRODUCT_MIX_BREAKEVEN"):
        VariantRule(("minimumLotRule", "mixtureBundleIntegrality"), (),
                    (("minimumLotRule", ("WHOLE_BUNDLES",)),
                     ("mixtureBundleIntegrality", (True,)),)),
    ("HC.COST.07", "EVM_BAC_CPI"):
        VariantRule(("earnedValueRule", "eacFormula"), (),
                    (("earnedValueRule", ("EXTERNALLY_SUPPLIED_EV",)),
                     ("eacFormula", ("BAC_DIV_CPI",)),)),
    ("HC.COST.07", "EVM_EAC_FORECAST"):
        VariantRule(("earnedValueRule", "eacFormula"), (),
                    (("earnedValueRule", ("EXTERNALLY_SUPPLIED_EV",)),
                     ("eacFormula", ("AC_PLUS_REMAINING_AT_BUDGET",)),)),
    ("HC.DCF.07", "GORDON_FCFF_TERMINAL"):
        VariantRule(("terminalMethod", "terminalGrowth"), (),
                    (("terminalMethod", ("GORDON_FCFF",)),)),
    ("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT"):
        VariantRule(("netIncomeBasis", "noncashAdjustment", "workingCapitalSign"), (),
                    (("netIncomeBasis", ("REPORTED_AFTER_TAX_NET_INCOME",)),
                     ("noncashAdjustment", ("SIGNED_NONCASH_LINES",)),
                     ("workingCapitalSign", ("INCREASE_OF_NWC_IS_OUTFLOW",)),)),
    ("HC.CASH.05", "INDIRECT_CFO_RECONCILED"):
        VariantRule(("netIncomeBasis", "noncashAdjustment", "workingCapitalSign",
                     "directIndirectComparisonPolicy"), (),
                    (("netIncomeBasis", ("REPORTED_AFTER_TAX_NET_INCOME",)),
                     ("noncashAdjustment", ("SIGNED_NONCASH_LINES",)),
                     ("workingCapitalSign", ("INCREASE_OF_NWC_IS_OUTFLOW",)),
                     ("directIndirectComparisonPolicy", ("EXACT_EQUALITY",)),)),
    ("HC.DCF.05", "FCFF_UNLEVERED"):
        VariantRule(("taxPolicy", "capitalExpenditurePolicy", "workingCapitalBasis"), (),
                    (("taxPolicy", ("EBIT_TIMES_EFFECTIVE_TAX_REFERENCE",)),
                     ("capitalExpenditurePolicy", ("CASH_CAPEX_POSITIVE_OUTFLOW",)),
                     ("workingCapitalBasis", ("INCREASE_NWC_IS_OUTFLOW",)),)),
    ("HC.DCF.08", "EV_TO_EQUITY_BRIDGE"):
        VariantRule(("netDebtDefinition", "minorityInterests", "valuationDate"), (),
                    (("netDebtDefinition", ("GROSS_DEBT_LESS_UNRESTRICTED_CASH",)),
                     ("minorityInterests", ("NCI_DEDUCT_FROM_ENTERPRISE",)),)),
    ("HC.COST.05", "COMPOUND_ESCALATION"):
        VariantRule(("inflationIndexRev", "compoundingBasis", "contingencyOverlap"), (),
                    (("compoundingBasis", ("DISCRETE_ANNUAL_END",)),
                     ("contingencyOverlap", ("NO_CONTINGENCY_DOUBLE_COUNT",)),),
                    ("inflationIndexRev",)),
}


class ParameterSemantics:
    def __init__(self, root: Path):
        self.registry = ContractRegistry(root)
        with (root / "catalog" / "method_parameter_candidates_116_r3.tsv").open(
            encoding="utf-8", newline=""
        ) as f:
            raw = list(csv.DictReader((line for line in f if line.strip() and
                                        not line.lstrip().startswith("#")), delimiter="\t"))
        if len(raw) != 732:
            raise CalculationError("PARAMETER_COUNT_MISMATCH")
        by_name: dict[str, set[str]] = {}
        self.bindings: dict[tuple[str, str], ParameterBinding] = {}
        for r in raw:
            model, name, kind = r["modelCode"], r["parameterCode"], r["logicalType"]
            if not model or not name or not kind:
                raise CalculationError("EMPTY_PARAMETER")
            if kind not in SUPPORTED_TYPES:
                raise CalculationError("UNKNOWN_PARAMETER_TYPE", kind)
            if (model, name) in self.bindings:
                raise CalculationError("DUPLICATE_PARAMETER_BINDING")
            by_name.setdefault(name, set()).add(kind)
            # Candidate ID distinguishes the *type* but does not falsely
            # claim identical financial semantics across contexts.
            semantic_candidate = "CAND." + kind + "." + name
            self.bindings[(model, name)] = ParameterBinding(
                model, name, kind, semantic_candidate, r["financialS2"]
            )
        self.collisions = MappingProxyType({
            name: tuple(sorted(types)) for name, types in by_name.items()
            if len(types) > 1
        })
        if set(self.collisions) != KNOWN_TYPE_COLLISIONS:
            raise CalculationError("PARAMETER_COLLISION_BASELINE_DRIFT")
        self.unique_names = len(by_name)
        self.typed_candidate_ids = frozenset(
            b.semantic_candidate_id for b in self.bindings.values()
        )
        # Every reference-mode rule must be a real catalog entry with typed
        # model-scoped bindings. A rule never implies financial S2 admission.
        for (model, variant), rule in RULES.items():
            if (model, variant) not in self.registry.variants:
                raise CalculationError("VARIANT_RULE_MISSING_FROM_CATALOG", model + ":" + variant)
            declared_names = (*rule.required, *rule.optional)
            if len(declared_names) != len(set(declared_names)):
                raise CalculationError("VARIANT_RULE_DUPLICATE_PARAMETER")
            for name in declared_names:
                if (model, name) not in self.bindings:
                    raise CalculationError("VARIANT_RULE_UNBOUND_PARAMETER", model + ":" + name)
            for name, allowed in rule.enums:
                if name not in declared_names or not allowed:
                    raise CalculationError("VARIANT_RULE_INVALID_ENUM", name)
                if self.bindings[(model, name)].logical_type not in (
                    "REFERENCE", "CODE", "ENUM", "BOOLEAN"
                ):
                    raise CalculationError("VARIANT_RULE_ENUM_TYPE_MISMATCH", name)
            for name in rule.sha256_references:
                if name not in declared_names or name in dict(rule.enums):
                    raise CalculationError("VARIANT_RULE_INVALID_SHA_REFERENCE", name)
                if self.bindings[(model, name)].logical_type != "REFERENCE":
                    raise CalculationError("VARIANT_RULE_SHA_TYPE_MISMATCH", name)

    def resolve_unique(self, model_code: str, config: Mapping[str, Any],
                       *, reference_mode: bool = False) -> ResolvedVariant:
        """Automatically select exactly one executable candidate rule.

        Ambiguous or unmatched configurations never choose a default variant.
        This is not financial method qualification and does not create any new
        catalog variant; unreviewed catalog templates stay blocked.
        """
        if not reference_mode:
            raise CalculationError("FINANCIAL_S2_REQUIRED")
        if model_code not in self.registry.models:
            raise CalculationError("UNKNOWN_MODEL", model_code)
        if not isinstance(config, Mapping):
            raise CalculationError("INVALID_CONFIGURATION")
        matches = []
        for model, variant in RULES:
            if model != model_code:
                continue
            try:
                matches.append(self.resolve(model, variant, config, reference_mode=True))
            except CalculationError:
                pass
        if not matches:
            raise CalculationError("NO_COMPATIBLE_VARIANT", model_code)
        if len(matches) != 1:
            raise CalculationError("AMBIGUOUS_VARIANT", ",".join(
                sorted(result.variant_code for result in matches)))
        return matches[0]

    def resolve(self, model_code: str, variant_code: str,
                config: Mapping[str, Any], *, reference_mode: bool = False) -> ResolvedVariant:
        if not reference_mode:
            raise CalculationError("FINANCIAL_S2_REQUIRED")
        if model_code not in self.registry.models:
            raise CalculationError("UNKNOWN_MODEL", model_code)
        if (model_code, variant_code) not in self.registry.variants:
            raise CalculationError("UNKNOWN_VARIANT", variant_code)
        rule = RULES.get((model_code, variant_code))
        if rule is None:
            raise CalculationError("VARIANT_RULE_NOT_IMPLEMENTED")
        if not isinstance(config, Mapping):
            raise CalculationError("INVALID_CONFIGURATION")
        allowed = set(rule.required) | set(rule.optional)
        for name in config:
            if name not in allowed:
                raise CalculationError("UNCONSUMED_CONFIGURATION", name)
            if (model_code, name) not in self.bindings:
                raise CalculationError("UNKNOWN_PARAMETER", name)
        for name in rule.required:
            if name not in config or config[name] is None:
                raise CalculationError("REQUIRED_PARAMETER_MISSING", name)
        choices = dict(rule.enums)
        cleaned: dict[str, Any] = {}
        for name in sorted(config):
            value = config[name]
            declared = self.bindings[(model_code, name)].logical_type
            if name in choices:
                if not any(type(value) is type(option) and value == option
                           for option in choices[name]):
                    raise CalculationError("ENUM_OUT_OF_RANGE", name)
            elif name in rule.sha256_references:
                if declared != "REFERENCE" or not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                    raise CalculationError("PINNED_REFERENCE_SHA_REQUIRED", name)
            elif declared in ("RATE", "MONEY", "DECIMAL", "PERCENTAGE"):
                value = format(number(value), "f")
                if declared in ("RATE", "PERCENTAGE") and not (-1 < number(value) < 100):
                    raise CalculationError("RATE_OUT_OF_DOMAIN", name)
            elif declared in ("DATE", "LOCAL_DATE"):
                value = day(value).isoformat()
            elif declared == "INTEGER":
                value = integer(value)
            elif declared == "BOOLEAN":
                if not isinstance(value, bool):
                    raise CalculationError("BOOLEAN_REQUIRED", name)
            elif declared == "STRUCT":
                if not isinstance(value, Mapping):
                    raise CalculationError("STRUCT_REQUIRED", name)
                if name == "rootDomain":
                    if set(value) != {"minRate", "maxRate"}:
                        raise CalculationError("ROOT_DOMAIN_FIELDS_REQUIRED")
                    lo, hi = number(value["minRate"]), number(value["maxRate"])
                    if lo <= -1 or hi <= lo or hi > 1000:
                        raise CalculationError("INVALID_ROOT_DOMAIN")
                    value = {"minRate": format(lo, "f"), "maxRate": format(hi, "f")}
                else:
                    raise CalculationError("UNREVIEWED_STRUCT_SEMANTICS")
            elif declared in ("CODE", "ENUM"):
                if not isinstance(value, str) or not value:
                    raise CalculationError("CODE_REQUIRED", name)
            else:
                raise CalculationError("PARAMETER_SEMANTICS_UNREVIEWED", name)
            cleaned[name] = value
        sha = fingerprint({
            "modelCode": model_code, "variantCode": variant_code,
            "candidateConfig": cleaned, "referenceContract": "HC_R04_REFERENCE_RULES_V1"
        })
        return ResolvedVariant(
            model_code, variant_code, _freeze(cleaned), sha
        )
