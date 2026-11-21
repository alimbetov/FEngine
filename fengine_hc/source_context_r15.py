"""QUAL-R1.5: synthetic-only, fail-closed source-context compatibility gate.

Metadata consistency is NOT evidence of external authorization or payload lineage.
This reference gate deliberately performs no FX, resampling, SKU union, or
methodology migration. FIN, Redis Runtime and Rust are not used.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from fengine_hc.reference import CalculationError, fingerprint

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_CURRENCY = re.compile(r"[A-Z]{3}\Z")
_TOKEN = re.compile(r"[A-Z0-9][A-Z0-9_.-]{0,63}\Z")
_PERIOD = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


@dataclass(frozen=True)
class SourceContext:
    source_id: str
    role: str
    user_id: str
    project_id: str
    currency: str
    period_start: str
    period_end: str
    period_type: str
    sku_set: tuple[str, ...]
    methodology_id: str
    methodology_version: str
    methodology_sha256: str
    payload_sha256: str


def _valid_token(value: object) -> bool:
    return isinstance(value, str) and bool(_TOKEN.fullmatch(value))


def _source_shape(s: SourceContext) -> None:
    from datetime import date

    if not isinstance(s, SourceContext):
        raise CalculationError("SOURCE_CONTEXT_REQUIRED")
    if not all(isinstance(x, str) and x.strip() for x in (
        s.source_id, s.user_id, s.project_id, s.methodology_version
    )):
        raise CalculationError("INVALID_SOURCE_IDENTITY")
    if not _valid_token(s.role) or not _valid_token(s.methodology_id):
        raise CalculationError("INVALID_SOURCE_IDENTITY")
    if not isinstance(s.currency, str) or not _CURRENCY.fullmatch(s.currency):
        raise CalculationError("INVALID_CURRENCY_CONTEXT")
    if s.period_type not in ("DAY", "WEEK", "MONTH", "QUARTER", "HALF_YEAR", "YEAR", "AS_OF"):
        raise CalculationError("INVALID_PERIOD_CONTEXT")
    if not all(isinstance(x, str) and _PERIOD.fullmatch(x) for x in (
        s.period_start, s.period_end
    )):
        raise CalculationError("INVALID_PERIOD_CONTEXT")
    try:
        start, end = date.fromisoformat(s.period_start), date.fromisoformat(s.period_end)
    except ValueError as exc:
        raise CalculationError("INVALID_PERIOD_CONTEXT") from exc
    if start > end or (s.period_type == "AS_OF" and start != end):
        raise CalculationError("INVALID_PERIOD_CONTEXT")
    if not isinstance(s.sku_set, tuple) or not s.sku_set or any(
        not _valid_token(x) for x in s.sku_set
    ) or tuple(sorted(set(s.sku_set))) != s.sku_set:
        raise CalculationError("NONCANONICAL_SKU_CONTEXT")
    if not isinstance(s.methodology_sha256, str) or not _SHA.fullmatch(s.methodology_sha256):
        raise CalculationError("INVALID_METHODOLOGY_DIGEST")
    if not isinstance(s.payload_sha256, str) or not _SHA.fullmatch(s.payload_sha256):
        raise CalculationError("INVALID_PAYLOAD_DIGEST")


def validate_contexts(
    sources: Sequence[SourceContext],
    *,
    required_roles: frozenset[str],
    single_sku: bool = False,
) -> str:
    """Return deterministic context receipt only for an exact compatible cohort.

    Source periods are required to be IDENTICAL, not merely overlapping; any
    controlled cross-period operation requires a separately reviewed policy.
    """
    if not isinstance(sources, (list, tuple)) or not sources:
        raise CalculationError("SOURCE_CONTEXT_REQUIRED")
    if not isinstance(required_roles, frozenset) or not required_roles:
        raise CalculationError("REQUIRED_SOURCE_ROLES")
    for s in sources:
        _source_shape(s)
    roles = [s.role for s in sources]
    if len(set(roles)) != len(roles) or set(roles) != required_roles:
        raise CalculationError("SOURCE_ROLE_MISMATCH")
    if len({s.source_id for s in sources}) != len(sources):
        raise CalculationError("DUPLICATE_SOURCE_ID")
    first = sources[0]
    for s in sources[1:]:
        if (s.user_id, s.project_id) != (first.user_id, first.project_id):
            raise CalculationError("CROSS_SCOPE_DATASET")
        if s.currency != first.currency:
            raise CalculationError("CROSS_CURRENCY_DATASET")
        if (s.period_type, s.period_start, s.period_end) != (
            first.period_type, first.period_start, first.period_end
        ):
            raise CalculationError("CROSS_PERIOD_DATASET")
        if s.sku_set != first.sku_set:
            raise CalculationError("CROSS_SKU_DATASET")
        if (s.methodology_id, s.methodology_version, s.methodology_sha256) != (
            first.methodology_id, first.methodology_version, first.methodology_sha256
        ):
            raise CalculationError("CROSS_METHODOLOGY_DATASET")
    if single_sku and len(first.sku_set) != 1:
        raise CalculationError("MULTI_SKU_POOL_UNSUPPORTED")
    return fingerprint([
        {
            "sourceId": s.source_id, "role": s.role,
            "userId": s.user_id, "projectId": s.project_id,
            "currency": s.currency, "periodStart": s.period_start,
            "periodEnd": s.period_end, "periodType": s.period_type,
            "skuSet": list(s.sku_set), "methodologyId": s.methodology_id,
            "methodologyVersion": s.methodology_version,
            "methodologySha256": s.methodology_sha256,
            "payloadSha256": s.payload_sha256,
        }
        for s in sorted(sources, key=lambda x: x.role)
    ])


def execute_guarded(
    sources: Sequence[SourceContext],
    payloads_by_role: Mapping[str, Any],
    *,
    required_roles: frozenset[str],
    executor: Callable[[Mapping[str, Any]], Any],
    single_sku: bool = False,
) -> tuple[str, Any]:
    """Validate metadata and locally recompute source payload hashes BEFORE execution.

    The executor receives ONLY verified role-keyed synthetic payloads. This is
    not an external signature/permission check or a production API.
    """
    receipt = validate_contexts(sources, required_roles=required_roles, single_sku=single_sku)
    if not isinstance(payloads_by_role, Mapping) or set(payloads_by_role) != required_roles:
        raise CalculationError("SOURCE_PAYLOAD_ROLES")
    for s in sources:
        if fingerprint(payloads_by_role[s.role]) != s.payload_sha256:
            raise CalculationError("SOURCE_PAYLOAD_DIGEST_MISMATCH")
    return receipt, executor(payloads_by_role)
