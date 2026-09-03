"""Late-Cenozoic vertical physical/environment providers."""

from .paleogeography import *  # noqa: F401,F403
from .environment import *  # noqa: F401,F403

from .sealed_120ka_boundary import (
    reconstruct_v061_spatial_at_year,
    verify_generalizer_against_materialized_snapshot,
    conservative_nested_remap,
    remap_exact_120ka_to_a1,
    boundary_state_from_remapped_120ka,
)
from .sealed_120ka_boundary import load_materialized_a1_boundary

from .eustatic_land_bridge import (
    EustaticLandBridgeResult,
    bridge_relative_eustatic_anomaly,
    apply_effective_land_to_boundary,
)

from .integrated_provider import (
    IntegratedProviderConfig,
    IntegratedLateCenozoicProvider,
    SealedRecentA1Provider,
    age_ma_to_model_seconds,
    model_seconds_to_age_ma,
)
from .adaptive_clock import (
    AdaptiveClockConfig,
    build_adaptive_late_cenozoic_clock,
    validate_adaptive_late_cenozoic_clock,
    environmental_activity_score,
    recent_max_dt_years,
)

# v0.6.4C1 derived CHA-2 50-year nested authority
from .cha2_nested_50y import (
    CHA2Nested50YRecentProvider,
    IntegratedLateCenozoicProviderC1,
    Nested50YConfig,
)
from .adaptive_clock_c1 import (
    build_adaptive_late_cenozoic_clock_c1,
    recent_max_dt_years_c1,
    validate_adaptive_late_cenozoic_clock_c1,
)

from .late_pleistocene_boundary import (
    LatePleistoceneBoundaryConfig,
    LatePleistoceneBoundaryContinuation,
    IntegratedLateCenozoicProviderC2,
    boundary_progress,
)
from .adaptive_clock_c2 import build_adaptive_late_cenozoic_clock_c2

# v0.6.4D production replay interface (non-invasive to SEALED D3)
from .production_interface import (
    D3LateCenozoicSubstrateAdapter,
    build_production_adapter,
    patched_sealed_d3_substrate,
)
