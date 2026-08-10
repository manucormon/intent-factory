# NOTES — cycling instance

**Status:** implementation verified; construct validity `NOT_EVALUATED`
**Data:** REAL power (GoldenCheetah OpenData, CC BY 4.0) + DECLARED gradient/fatigue

## Data provenance

| Variable | Label | Source |
|---|---|---|
| power_w | REAL | GoldenCheetah OpenData — anonymous athlete, 363-min ride |
| gradient_pct | DECLARED | derived from GPS alt/km, clipped ±15% for noise |
| fatigue | DECLARED | linear model: t / ride_duration |
| intent label | CLASSIFIED | `core/classifier.py` — threshold rules |
| future intent sequence | PROJECTED | `classifier.project_ahead()` — see honest limit below |

**FTP estimation:** 95% of best 20-minute sliding-window average power = 208W
(industry standard for field-test FTP estimation).

## Honest limit: what project_ahead() does and does NOT do

`project_ahead(samples, steps)` classifies a caller-supplied sequence of
sensor samples — it does **not** forecast what the sensor values will be.
There is no autoregressive model, no time-series prediction, no Kalman filter.

Concretely: if you call `project_ahead(next_30_samples, 30)`, you are
supplying the hypothetical future state yourself. The function returns what
the intent *would be* if those samples occurred.

**Why it's built this way:** labeling "what intent the athlete had at t+1"
requires ground truth that doesn't exist in public cycling datasets. An
alternative name (`classify_sequence`, `label_batch`) would be more
technically precise — but would break the family's conceptual narrative
without adding safety. The limit is documented here; `project_ahead` stays.

## Verified findings

1. **ATTACK suppression works in two independent paths:**
   - Gradient path: gradient > 15% → physically implausible to sustain attack power
   - Fatigue path: fatigue ≥ 0.85 → body cannot sustain attack output
   - Both paths tested independently; `attack_suppressed=True` signals the caller

2. **Extreme fatigue override (fatigue ≥ 0.90):** forces RECOVER regardless of
   observed power. Rationale: above this threshold the power reading is unreliable
   as an intent signal — the athlete may be in distress, not deliberate recovery.

3. **Real GoldenCheetah ride (t=300-900s, FTP=208W):** all three intent labels
   present — ATTACK 55.9% / MAINTAIN 35.6% / RECOVER 8.5%. Plausible distribution
   for an active climbing segment. Power=REAL; gradient/fatigue=DECLARED.

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
