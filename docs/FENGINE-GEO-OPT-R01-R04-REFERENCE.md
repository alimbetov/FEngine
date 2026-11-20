# GEO-OPT R0.1–R0.4 — Python reference vertical slice

Status: **local reference implementation; not a FIN-qualified production runtime**.

## Scope

This small package is the first executable slice of `FENGINE_MASTER_SPEC.md` sections 19–20. It deliberately does not create a second control plane, persistent store, API, migrations, PostGIS schema, or financial writer. It is designed to be embedded later in the **existing** FEngine Python Calculation Hub task dispatcher, once that hub is implemented and its DTOs qualified.

### Implemented

- Immutable typed `GeoNode`, `GeoEdge`, `GeoHierarchyRelation`, `GeoWeightDefinition`, `GeoWeightValue`, `GeoWeightProfile`, `GeoGraphRevision` contracts using `dataclass(frozen=True, slots=True)` and `Decimal`/decimal string inputs (no binary float).
- Single scope, static directed routing topology, a **separate strict tree** for hierarchy, optional WGS84 coordinates, cost/demand/capacity typed definitions, nonnegative-cost validation and explicit missing-vs-zero behavior.
- `compile_graph`: known endpoints, unique identities, strict parenthood, disconnected/cyclic hierarchy, depth and size limits, materialized depth/outgoing/children indexes, immutable `MappingProxyType` indexes, stable SHA-256 of canonical sorted graph data, scope and weight values.
- Iterative, nonrecursive sum of **additive** node weights for subtrees; aggregating other weight kinds without an approved operator is rejected.
- Directed Dijkstra and A* (A* requires supplied **consistent, nonnegative, target-zero** heuristic; default routing distances are **not** inferred from GPS coordinates).
- Yen's top-K **loopless** shortest paths, default K=3, deterministic ordering, without fabricating additional alternatives if they do not exist; `RoutingPolicy` filters nodes/edges and optional node-entry COST. Resource ceilings raise `SearchLimitExceeded` rather than misrepresent a partial result as proven optimal.
- `verify_route`: independent directed continuity, policy eligibility, looplessness and exact additive objective re-evaluation.
- Python 3.11+ standard library only; no runtime dependencies.

### Not implemented / intentionally blocked

- Persistent GraphRevision and business admission; multi-tenant *authorization* (scope identity is included in fingerprints but ACL is not implemented); durable Hub sessions/jobs/leases/outbox and financial S2.
- Transactional graph diffs, time-variant weights, CRS transforms, geodesic/distance-from-roads, PostGIS/pgRouting/road ingestion, alternate route diversity/disjointness, routing under flow constraints, VRP/MILP, general nonlinear/negative-cost optimization, height/3D and geofences.
- Full time-dependent, reliability or probabilistic weight semantics, null/NA distinction beyond present/null, branch aggregation in DAG hierarchies, efficient solver behavior for production-sized networks.
- Complete independent 22-case GEO spec qualification: tests cover the R0.1–R0.4 subset only. No benchmark or production SLO claim.

**Contract decisions:** each `GeoEdge` is directed; bidirectional travel requires two edge records. Routing topology can have cycles while hierarchy cannot. Coordinates establish only point position; they do not create traversable edges or trusted travel-time estimates. First node is not charged for visit; every subsequent node, including the target, is charged if `node_visit_cost_code` is set. Edge and node COST units must match. `GeoGraphRevision.scope_id` is a logical fingerprint component, not an ACL enforcement mechanism.

## Test command

```bash
python -m unittest discover -s tests -v
```

## First golden reference

ROOT → A → T costs 2+3=5; ROOT → B → T 3+4=7; ROOT → C → T 4+5=9. `yen_top_k(..., k=3)` must produce exactly those three ordered paths. Reversing edges is forbidden unless separate directed reverse edges exist. Changing A's node visit fee by 4 results in routes 7,9,9. For a fully branched strict hierarchy of 60 levels, compilation is iterative and bounded.

## Integration plan

1. Publish DTO schema with versioned `InputContractDTO`/`OutputSchemaRevision` bindings and scope access control.
2. Adapt `compile_graph` to Hub immutable typed datasets, preserving source/graph/weight/scenario SHA, precision, measured runtime quota and exact solver artifact build.
3. Return `GEO_ROUTE_PATH_SET` through existing `CalculationResponseDTO` root; implement independent output validation and archival receipts.
4. Add PostGIS/pgRouting or specialized route providers only for verified data sources/road-network use cases; qualify dynamic weights, diversity and large-graph benchmarks separately.
