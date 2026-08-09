# CONTRACT.md — intent_factory

Part of the Kairos family. See `kairos-factory/CONTRACT_FAMILY.md` for shared invariants.

## Brother identity
- **Position:** Brother 2 — Predict-intent
- **Time axis:** near-future intent (what will the agent do in the next N seconds?)
- **Facing:** World-facing (reads sensor state, not human cognitive state)

## Family invariants satisfied

| Invariant | How |
|---|---|
| Confidence vocabulary | OBSERVED / CLASSIFIED / PROJECTED — in every output |
| Latency exposed | `projected.dt_ahead` on every ProjectedIntent |
| Verified finding | All thresholds verified in tests, documented in NOTES.md |
| No full autonomy | Output is a label — actuation is the consumer's responsibility |
| CONTRACT.md gated | This file |
| Scope discipline | Does not plan, does not govern — classifies intent only |

## What this brother does NOT decide
- Does not plan actions (that is `planning_factory`)
- Does not assess human readiness to receive information (that is `sensory_architecture_factory`)
- Does not track physical state (that is `perception_factory`)
