# CONTRACT.md — intent_factory

Part of the Kairos family. See `kairos-factory/CONTRACT_FAMILY.md` for shared invariants.

## Brother identity
- **Position:** Brother 2 — classify observable effort state (predict-intent is aspirational)
- **Time axis:** present classification; PROJECTED labels require caller-supplied future samples
- **Facing:** World-facing (reads sensor state, not human cognitive state)

## Family invariants satisfied

| Invariant | How |
|---|---|
| Automation bias / construct validity | `NOT_EVALUATED` — experimental/observe-only only |
| Confidence vocabulary | OBSERVED / CLASSIFIED / PROJECTED — in every output |
| Latency exposed | `projected.dt_ahead` on every ProjectedIntent |
| Verified finding | All thresholds verified in tests, documented in NOTES.md |
| No full autonomy | Output is a label — actuation is the consumer's responsibility |
| CONTRACT.md gated | This file |
| Scope discipline | Does not plan, does not govern — classifies intent only |

## Automation bias evaluation — PROCESS DEVIATION

**Status:** `CONSTRUCT_VALIDITY: NOT_EVALUATED`

Guardrail 1 (FAMILY.md) required evaluating whether this brother improves
or worsens human judgment under time pressure before writing code. The
guardrail existed on August 8, 2026. Intent code was written on August 9,
2026. The evaluation was not performed first.

This is documented as a process deviation. It is not corrected retroactively.
A documentary review of thresholds is not a substitute for empirical evidence.

**What is unknown:**
- Whether presenting ATTACK/MAINTAIN/RECOVER labels under time pressure
  increases over-reliance on the classifier's output
- Whether the labels improve, degrade, or have no effect on human decisions
  at the decision boundaries (fatigue 0.85–0.90, gradient near 15%)

**Permitted use:** experimental and observe-only contexts only
**Blocked use:** any deployment where the label could influence a time-critical
  human decision before the comparison study is completed

**Unblocks when:** a study comparing human decisions with vs. without intent
  labels, under realistic time pressure, is documented in NOTES.md and
  reviewed by a domain expert.

## What this brother does NOT decide
- Does not plan actions (that is `planning_factory`)
- Does not assess human readiness to receive information (that is `sensory_architecture_factory`)
- Does not track physical state (that is `perception_factory`)
