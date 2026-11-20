"""One public temporal model reference API; versioned strategy registries beneath.

V1 and V1.1 share the same TASE calendar/coverage engine. No caller-supplied
algorithm selection and no automatic admission of arbitrary HC model outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from tase.model_temporal import (
    ModelTemporalRegistry, ModelTemporalRequest, ModelTemporalRun,
    ModelTemporalResult, calculate_model_temporal,
)
from tase.model_temporal_v11 import (
    ModelTemporalRegistryV11, ModelTemporalRunV11,
    calculate_model_temporal_v11,
)
from tase.model_temporal_v12 import (
    ModelTemporalRegistryV12, ModelTemporalRunV12,
    calculate_model_temporal_v12,
)
from tase.reference import TaseError


@dataclass(frozen=True)
class UnifiedModelTemporalRegistry:
    sum_stock: ModelTemporalRegistry
    model_derived: ModelTemporalRegistryV11
    dated_weighted_pvm: ModelTemporalRegistryV12 | None = None

    @classmethod
    def load(cls, root: Path, *, reference_mode: bool = False
             ) -> "UnifiedModelTemporalRegistry":
        if not reference_mode:
            raise TaseError("FINANCIAL_S2_REQUIRED")
        first = ModelTemporalRegistry.load(root, reference_mode=True)
        second = ModelTemporalRegistryV11.load(root, reference_mode=True)
        third = ModelTemporalRegistryV12.load(root, reference_mode=True)
        overlap = ((set(first.capabilities) & set(second.capabilities))
                   | (set(first.capabilities) & set(third.capabilities))
                   | (set(second.capabilities) & set(third.capabilities)))
        if overlap:
            raise TaseError("TEMPORAL_STRATEGY_REGISTRY_AMBIGUOUS")
        return cls(first,second,third)

    def select(self, req: ModelTemporalRequest) -> str:
        key = req.model_code, req.variant_code, req.output_field
        first = key in self.sum_stock.capabilities
        second = key in self.model_derived.capabilities
        third = (self.dated_weighted_pvm is not None
                 and key in self.dated_weighted_pvm.capabilities)
        if (int(first) + int(second) + int(third)) > 1:
            raise TaseError("TEMPORAL_STRATEGY_REGISTRY_AMBIGUOUS")
        if first:
            self.sum_stock.resolve(
                *key, source_grain=req.source_grain, output_grain=req.output_grain,
            )
            return "V1_TYPED"
        if second:
            self.model_derived.resolve(req)
            return "V11_DERIVED"
        if third:
            self.dated_weighted_pvm.resolve(req)
            return "V12_DATED_WEIGHTED_PVM"
        raise TaseError("TEMPORAL_CAPABILITY_NOT_ADMITTED")


def calculate_universal_model_temporal(
    registry: UnifiedModelTemporalRegistry,
    request: ModelTemporalRequest,
    runs: (Sequence[ModelTemporalRun] | Sequence[ModelTemporalRunV11]
           | Sequence[ModelTemporalRunV12]),
    *, reference_mode: bool = False,
) -> ModelTemporalResult:
    if not reference_mode:
        raise TaseError("FINANCIAL_S2_REQUIRED")
    if not isinstance(registry, UnifiedModelTemporalRegistry):
        raise TaseError("TEMPORAL_UNIFIED_REGISTRY_REQUIRED")
    strategy = registry.select(request)
    if not isinstance(runs,(list,tuple)):
        raise TaseError("TEMPORAL_MODEL_RUN_BUDGET")
    if strategy == "V1_TYPED":
        if any(not isinstance(r,ModelTemporalRun) for r in runs):
            raise TaseError("TEMPORAL_INPUT_CONTRACT_MISMATCH")
        return calculate_model_temporal(
            registry.sum_stock, request, runs, reference_mode=True,
        )
    if strategy == "V11_DERIVED":
        if any(not isinstance(r,ModelTemporalRunV11) for r in runs):
            raise TaseError("TEMPORAL_INPUT_CONTRACT_MISMATCH")
        return calculate_model_temporal_v11(
            registry.model_derived, request, runs, reference_mode=True,
        )
    if strategy == "V12_DATED_WEIGHTED_PVM":
        if any(not isinstance(r, ModelTemporalRunV12) for r in runs):
            raise TaseError("TEMPORAL_INPUT_CONTRACT_MISMATCH")
        return calculate_model_temporal_v12(
            registry.dated_weighted_pvm, request, runs, reference_mode=True,
        )
    raise TaseError("TEMPORAL_STRATEGY_UNREVIEWED")
