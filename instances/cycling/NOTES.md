# NOTES — cycling instance

**Status:** verified
**Data:** DECLARED (synthetic ride generator)

## Data provenance

| Variable | Label | Source |
|---|---|---|
| power_w, gradient_pct | OBSERVED | `data_loader.generate_ride()`, physics-plausible ranges |
| fatigue | OBSERVED (DECLARED) | linear model: t / 3600s, same as sensory_architecture_factory ENMAX |
| intent label | CLASSIFIED | `core/classifier.py` — threshold rules |
| future intent sequence | PROJECTED | `classifier.project_ahead()` |

## Verified findings

1. **ATTACK suppression works in two independent paths:**
   - Gradient path: gradient > 15% → physically implausible to sustain attack power
   - Fatigue path: fatigue ≥ 0.85 → body cannot sustain attack output
   - Both paths tested independently; `attack_suppressed=True` signals the caller

2. **Extreme fatigue override (fatigue ≥ 0.90):** forces RECOVER regardless of
   observed power. Rationale: above this threshold the power reading is unreliable
   as an intent signal — the athlete may be in distress, not deliberate recovery.

3. **Synthetic 600s ride covers all zones:** seed=42 produces warm-up, tempo,
   attack, and recovery phases. All three labels appear in the classification sequence.

## Key design decision
Classifier is **stateless** — each sample is classified independently.
Temporal smoothing (e.g., "ATTACK must persist for 3s before triggering") is
the consumer's responsibility (`sensory_architecture_factory` or `planning_factory`).
This keeps the classifier's contract simple and testable.

## Connection to the family
- **Upstream:** `perception_factory` — if the physical state of the athlete were
  tracked (position on a climb, speed), that TRACKED state could feed this classifier.
- **Downstream:** `planning_factory` — CLASSIFIED intent → pacing plan
- **Downstream:** `sensory_architecture_factory` cycling instance — CLASSIFIED intent
  modulates attention budget (attack intent → higher cognitive load)
