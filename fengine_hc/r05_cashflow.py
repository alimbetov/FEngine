"""HC-R0.5: posted ledger direct operating cash-flow reference.

Numerical reference only. Classification mappings and accounting source
authenticity are NOT independently finance S2 approved. No Redis, database,
logging, network, or durable customer-data persistence in this module.
"""
from __future__ import annotations

import re
from decimal import Decimal, localcontext
from typing import Any, Mapping

from .reference import CalculationError, day, fingerprint, number

ZERO = Decimal(0)
_CLASSES = frozenset(("OPERATING", "INVESTING", "FINANCING", "INTERNAL_TRANSFER"))
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,95}\Z")
_CODE_RE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
MAX_POSTINGS = 20000
MAX_CLASSES = 512
MAX_OVERRIDES = 20000

# Static, published arithmetic contract; not an approval of cashflow labels.
RECONCILIATION_POLICY = {
    "basis": "POSTING_DATE_ONLY",
    "closingBalance": "EXACT_OPENING_PLUS_ALL_POSTINGS",
    "internalTransfers": "BALANCED_TWO_LEGS_SAME_PERIOD",
    "unclassified": "REJECT",
    "operatingCashFlow": "OPERATING_RECEIPTS_MINUS_OPERATING_PAYMENTS",
}
RECONCILIATION_SHA256 = fingerprint({
    "contract": "HC_CASH_04_RECON_ARITHMETIC_V1",
    "policy": RECONCILIATION_POLICY,
})


def _schema(value: Any, required: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != required:
        raise CalculationError(code)
    return value


def _date(value: Any) -> str:
    # Reject Python date.fromisoformat's accepted noncanonical week/compact forms.
    parsed = day(value)
    if not isinstance(value, str) or value != parsed.isoformat():
        raise CalculationError("CASH_POSTING_DATE_NOT_CANONICAL")
    return value


def _sha(value: Any, code: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise CalculationError(code)
    return value


def _id(value: Any, code: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise CalculationError(code)
    return value


def _code(value: Any, code: str) -> str:
    if not isinstance(value, str) or _CODE_RE.fullmatch(value) is None:
        raise CalculationError(code)
    return value


def _currency(value: Any) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Z]{3}", value) is None:
        raise CalculationError("CASH_CURRENCY_CODE_REQUIRED")
    return value  # lexical guard, not a certified ISO-4217 registry.


def _fmt(value: Decimal) -> str:
    return format(+value, "f")


def classification_rules_sha256(rules: Any) -> str:
    """Compute an exact content SHA for an explicit code->cashflow-class mapping.

    SHA matching means *internal data consistency*, not certified bookkeeping
    treatment, domain suitability or trust in the actor supplying the mapping.
    """
    return fingerprint({
        "contract": "HC_CASH_04_CLASSIFICATION_V1",
        "rules": _classifications(rules)[1],
    })


def posted_source_sha256(snapshot: Mapping[str, Any]) -> str:
    """Bind period, both balances and the complete ordered posted event feed."""
    _schema(snapshot, {"periodStart", "periodEnd", "currency",
                       "openingCash", "closingCash", "postings"},
            "DIRECT_CFO_SOURCE_SCHEMA")
    return fingerprint({"contract": "HC_CASH_04_POSTED_LEDGER_V1", "snapshot": snapshot})


def override_revision_sha256(source_sha: Any, overrides: Any) -> str:
    return fingerprint({
        "contract": "HC_CASH_04_RECLASSIFICATION_V1",
        "postedSourceSha256": _sha(source_sha, "DIRECT_CFO_SOURCE_SHA_REQUIRED"),
        "overrides": _overrides(overrides),
    })


def _classifications(rules: Any) -> tuple[dict[str, str], list[dict[str, str]]]:
    if not isinstance(rules, (list, tuple)) or not (1 <= len(rules) <= MAX_CLASSES):
        raise CalculationError("DIRECT_CFO_CLASSIFICATIONS_REQUIRED")
    table: dict[str, str] = {}
    for item in rules:
        row = _schema(item, {"code", "cashflowClass"}, "DIRECT_CFO_CLASSIFICATION_SCHEMA")
        code = _code(row["code"], "DIRECT_CFO_CLASSIFICATION_CODE")
        category = row["cashflowClass"]
        if not isinstance(category, str) or category not in _CLASSES:
            raise CalculationError("DIRECT_CFO_CLASS_UNKNOWN")
        if code in table:
            raise CalculationError("DIRECT_CFO_DUPLICATE_CLASS_CODE")
        table[code] = category
    if "OPERATING" not in set(table.values()):
        raise CalculationError("DIRECT_CFO_OPERATING_CLASS_REQUIRED")
    ordered = [{"code": code, "cashflowClass": table[code]} for code in sorted(table)]
    return table, ordered


def _overrides(data: Any) -> list[dict[str, str]]:
    if not isinstance(data, (list, tuple)) or not (1 <= len(data) <= MAX_OVERRIDES):
        raise CalculationError("DIRECT_CFO_OVERRIDES_REQUIRED")
    result = []
    seen = set()
    for item in data:
        row = _schema(item, {"postingId", "newClassificationCode", "reasonCode"},
                      "DIRECT_CFO_OVERRIDE_SCHEMA")
        pid = _id(row["postingId"], "DIRECT_CFO_OVERRIDE_POSTING_ID")
        code = _code(row["newClassificationCode"], "DIRECT_CFO_OVERRIDE_CLASS_CODE")
        if row["reasonCode"] != "DOCUMENTED_RECLASSIFICATION":
            raise CalculationError("DIRECT_CFO_OVERRIDE_REASON_UNSUPPORTED")
        if pid in seen:
            raise CalculationError("DIRECT_CFO_OVERRIDE_DUPLICATE")
        seen.add(pid)
        result.append({
            "postingId": pid, "newClassificationCode": code,
            "reasonCode": "DOCUMENTED_RECLASSIFICATION",
        })
    # Order-independent signed revision: consumer cannot swap list ordering to
    # produce a different SHA for identical substantive classification revisions.
    return sorted(result, key=lambda entry: entry["postingId"])


def direct_cfo(inputs: Mapping[str, Any], config: Mapping[str, Any],
               variant: str) -> dict[str, Any]:
    base = {"periodStart", "periodEnd", "currency", "openingCash", "closingCash",
            "postings", "classificationRules", "sourceRevisionSha256"}
    required = (base | {"reclassificationOverrides", "reclassificationRevisionSha256"}
                if variant == "DIRECT_RECLASSIFIED_CFO" else base)
    if variant not in ("DIRECT_POSTED_CFO", "DIRECT_RECLASSIFIED_CFO"):
        raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
    _schema(inputs, required, "DIRECT_CFO_INPUT_SCHEMA")
    first, last = _date(inputs["periodStart"]), _date(inputs["periodEnd"])
    if first > last:
        raise CalculationError("DIRECT_CFO_INVALID_PERIOD")
    if config["periodCutoff"] != last:
        raise CalculationError("DIRECT_CFO_PERIOD_CUTOFF_MISMATCH")
    currency = _currency(inputs["currency"])
    if (config["transferExclusionRule"] != "BALANCED_INTERNAL_TRANSFER_PAIRS"
            or config["valueDateVsPostingDate"] != "POSTING_DATE_ONLY"):
        raise CalculationError("DIRECT_CFO_POSTING_POLICY_UNSUPPORTED")
    if config["reconciliationRule"] != RECONCILIATION_SHA256:
        raise CalculationError("DIRECT_CFO_RECON_REVISION_MISMATCH")
    opening, closing = number(inputs["openingCash"]), number(inputs["closingCash"])
    source = _sha(inputs["sourceRevisionSha256"], "DIRECT_CFO_SOURCE_SHA_REQUIRED")
    source_snapshot = {key: inputs[key] for key in (
        "periodStart", "periodEnd", "currency", "openingCash", "closingCash", "postings"
    )}
    if posted_source_sha256(source_snapshot) != source:
        raise CalculationError("DIRECT_CFO_SOURCE_DIGEST_MISMATCH")

    classified, _ = _classifications(inputs["classificationRules"])
    if classification_rules_sha256(inputs["classificationRules"]) != config["cashClassification"]:
        raise CalculationError("DIRECT_CFO_CLASSIFICATION_SHA_MISMATCH")

    postings = inputs["postings"]
    if not isinstance(postings, (tuple, list)) or not (1 <= len(postings) <= MAX_POSTINGS):
        raise CalculationError("DIRECT_CFO_POSTINGS_REQUIRED")
    parsed: list[tuple[str, Decimal, str, str, str | None]] = []
    seen_ids: set[str] = set()
    for posting in postings:
        row = _schema(posting, {"postingId", "postingDate", "amount",
                                "direction", "classificationCode", "transferId"},
                      "DIRECT_CFO_POSTING_SCHEMA")
        pid = _id(row["postingId"], "DIRECT_CFO_POSTING_ID_INVALID")
        if pid in seen_ids:
            raise CalculationError("DIRECT_CFO_DUPLICATE_POSTING_ID")
        seen_ids.add(pid)
        date_string = _date(row["postingDate"])
        if not first <= date_string <= last:
            raise CalculationError("DIRECT_CFO_POSTING_OUTSIDE_PERIOD")
        direction = row["direction"]
        if direction not in ("IN", "OUT"):
            raise CalculationError("DIRECT_CFO_DIRECTION_INVALID")
        value = number(row["amount"])
        if value <= 0:
            raise CalculationError("DIRECT_CFO_POSTING_AMOUNT_MUST_BE_POSITIVE")
        code = _code(row["classificationCode"], "DIRECT_CFO_CLASSIFICATION_CODE")
        if code not in classified:
            raise CalculationError("DIRECT_CFO_UNCLASSIFIED_POSTING")
        transfer = row["transferId"]
        category = classified[code]
        if category == "INTERNAL_TRANSFER":
            transfer = _id(transfer, "DIRECT_CFO_TRANSFER_ID_REQUIRED")
        elif transfer is not None:
            raise CalculationError("DIRECT_CFO_NONTRANSFER_WITH_TRANSFER_ID")
        parsed.append((pid, value, direction, code, transfer))

    reclassified = 0
    if variant == "DIRECT_RECLASSIFIED_CFO":
        override_items = _overrides(inputs["reclassificationOverrides"])
        override_digest = _sha(inputs["reclassificationRevisionSha256"],
                               "DIRECT_CFO_RECLASS_REVISION_REQUIRED")
        if override_digest != override_revision_sha256(source, override_items):
            raise CalculationError("DIRECT_CFO_RECLASS_REVISION_MISMATCH")
        over = {item["postingId"]: item["newClassificationCode"] for item in override_items}
        if not set(over) <= seen_ids:
            raise CalculationError("DIRECT_CFO_OVERRIDE_UNKNOWN_POSTING")
        updated = []
        for pid, value, direction, code, transfer in parsed:
            next_code = over.get(pid, code)
            if next_code not in classified:
                raise CalculationError("DIRECT_CFO_OVERRIDE_UNKNOWN_CLASS")
            was, now = classified[code], classified[next_code]
            if pid in over:
                if code == next_code or was == "INTERNAL_TRANSFER" or now == "INTERNAL_TRANSFER":
                    raise CalculationError("DIRECT_CFO_FORBIDDEN_OVERRIDE")
                reclassified += 1
            updated.append((pid, value, direction, next_code, transfer))
        parsed = updated

    with localcontext() as ctx:
        ctx.prec = 40
        receipts = payments = investing = financing = net_change = ZERO
        transfers: dict[str, list[tuple[Decimal, str]]] = {}
        operating_count = transfer_count = 0
        for _, value, direction, code, transfer in parsed:
            signed = value if direction == "IN" else -value
            net_change += signed
            cash_class = classified[code]
            if cash_class == "OPERATING":
                operating_count += 1
                if direction == "IN":
                    receipts += value
                else:
                    payments += value
            elif cash_class == "INVESTING":
                investing += signed
            elif cash_class == "FINANCING":
                financing += signed
            else:
                transfer_count += 1
                transfers.setdefault(transfer, []).append((value, direction))
        for legs in transfers.values():
            if (len(legs) != 2 or legs[0][0] != legs[1][0]
                    or {legs[0][1], legs[1][1]} != {"IN", "OUT"}):
                raise CalculationError("DIRECT_CFO_UNBALANCED_INTERNAL_TRANSFER")
        calculated_close = opening + net_change
        if calculated_close != closing:
            raise CalculationError("DIRECT_CFO_CASH_BALANCE_MISMATCH")
        cfo = receipts - payments
        if cfo + investing + financing != net_change:
            raise CalculationError("DIRECT_CFO_CLASSIFICATION_RECONCILIATION_FAILED")
        return {
            "periodStart": first,
            "periodEnd": last,
            "currency": currency,
            "sourceRevisionSha256": source,
            "classificationRevisionSha256": config["cashClassification"],
            "reconciliationRevisionSha256": config["reconciliationRule"],
            "cashFlowFromOperations": _fmt(cfo),
            "operatingReceipts": _fmt(receipts),
            "operatingPayments": _fmt(payments),
            "netInvestingCashFlow": _fmt(investing),
            "netFinancingCashFlow": _fmt(financing),
            "netAllCashFlow": _fmt(net_change),
            "openingCash": _fmt(opening),
            "closingCash": _fmt(closing),
            "internalTransferNet": "0",
            "operatingPostingCount": operating_count,
            "excludedTransferPostingCount": transfer_count,
            "reclassifiedPostingCount": reclassified,
            "postingCount": len(parsed),
            "classification": "POSTED_LEDGER_RECONCILED_REFERENCE_NOT_ACCOUNTING_S2",
        }
