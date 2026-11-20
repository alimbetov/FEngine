"""FEngine TASE Python reference. Not a qualified financial or production runtime."""
from .reference import (Catalog, Dataset, Observation, PeriodRequest, ResultRow,
                        TaseError, TasePlan, TaseResult, calculate, compile_plan)
from .model_temporal import (ModelTemporalCapabilityV1, ModelTemporalRegistry,
                             ModelTemporalRequest, ModelTemporalRun, ModelTemporalResult,
                             calculate_model_temporal)
from .model_temporal_v11 import (
    ModelTemporalCapabilityV11, ModelTemporalRegistryV11, ModelTemporalRunV11,
    temporal_v11_source_sha256, calculate_model_temporal_v11,
)
from .model_temporal_v12 import (
    ModelTemporalCapabilityV12, ModelTemporalRegistryV12, ModelTemporalRunV12,
    temporal_v12_source_sha256, calculate_model_temporal_v12,
)
from .temporal_dispatch import (
    UnifiedModelTemporalRegistry, calculate_universal_model_temporal,
)

__all__ = ["Catalog", "Dataset", "Observation", "PeriodRequest", "ResultRow",
           "TaseError", "TasePlan", "TaseResult", "calculate", "compile_plan",
           "ModelTemporalCapabilityV1", "ModelTemporalRegistry",
           "ModelTemporalRequest", "ModelTemporalRun", "ModelTemporalResult",
           "calculate_model_temporal",
           "ModelTemporalCapabilityV11", "ModelTemporalRegistryV11",
           "ModelTemporalRunV11", "temporal_v11_source_sha256",
           "calculate_model_temporal_v11", "ModelTemporalCapabilityV12",
           "ModelTemporalRegistryV12", "ModelTemporalRunV12",
           "temporal_v12_source_sha256", "calculate_model_temporal_v12",
           "UnifiedModelTemporalRegistry",
           "calculate_universal_model_temporal"]
