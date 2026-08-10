# CONTRACT.md — cycling instance

## Instance identity
- **Domain:** competitive cycling — intent classification from power meter data
- **Data source:** REAL power (GoldenCheetah OpenData, CC BY 4.0, anonymous athlete) + DECLARED gradient/fatigue
- **Status:** implementation verified; construct validity `NOT_EVALUATED`

## Capability declarations

| Capability | Value | Evidence |
|---|---|---|
| HAS_ATTACK_SUPPRESSION | True | gradient ceiling + fatigue ceiling; tested |
| HAS_EXTREME_FATIGUE_OVERRIDE | True | fatigue ≥ 0.90 forces RECOVER; tested |
| HAS_PROJECTION | True | `project_ahead(samples, steps)` → PROJECTED sequence (see limit below) |
| DATA_LABEL | REAL + DECLARED | power=REAL (GoldenCheetah); gradient/fatigue=DECLARED (GPS-derived) |

## Confidence vocabulary

| Label | Meaning |
|---|---|
| OBSERVED | Raw sensor reading (power_w, gradient_pct) |
| CLASSIFIED | Intent label inferred from current state |
| PROJECTED | Future intent sequence over N steps |

## Latency contract (Guardrail 8)
- Single classify(): O(1), < 0.1ms
- project_ahead(N steps): O(N), < 1ms for N ≤ 600
- **Exposed variable:** `projected.dt_ahead` — seconds the projected sequence covers
- Consumer must compare `dt_ahead` against event horizon before acting on PROJECTED labels

## Honest limit: what project_ahead() actually does

`project_ahead(samples, steps)` classifies a **caller-supplied** future
sequence of sensor samples. It does NOT forecast from the current state
into the future — it has no predictive model of what sensor values will
be at t+1, t+2, etc.

**Why:** real intent forecasting would require labeled intent data over
time (e.g., "rider was about to attack" ground truth). No such public
dataset exists. The current name reflects the consumer's use pattern
(plan N steps ahead) rather than an autoregressive forecast.

**Consumer responsibility:** if you call `project_ahead(future_samples, N)`,
you are supplying the hypothetical future state. The classifier returns
what the intent *would be* if those samples occurred — not what *will*
occur.

This limit is by design and documented honestly, not as a temporary gap.

## Construct-validity gate

The tests verify deterministic threshold behavior and data provenance. They do
not establish that ATTACK/MAINTAIN/RECOVER corresponds to the rider's actual
intent; no labeled intent ground truth is available. Human-facing or
time-critical use remains blocked until the automation-bias comparison required
by the root `CONTRACT.md` is completed and reviewed.

## Key verified findings

Thresholds are DECLARED. Findings are verified against real data.

- ATTACK fires at power > 1.05 FTP on gradient ≤ 15% and fatigue < 0.85
- ATTACK is suppressed (→ MAINTAIN) when gradient > 15% or fatigue ≥ 0.85
- Extreme fatigue (≥ 0.90) forces RECOVER regardless of power output
- Real GoldenCheetah ride (t=300-900s, FTP=208W): all three labels present
  — ATTACK 55.9% / MAINTAIN 35.6% / RECOVER 8.5% (plausible for climbing segment)

## What this instance does NOT do
- Does not forecast future sensor values — `project_ahead()` classifies
  caller-supplied hypothetical samples, not self-generated predictions
- Does not infer intent from heart rate or cadence (not in input)
- Does not model race tactics (breakaway, drafting) — those belong in 03_planning
- Does not learn thresholds from data — all thresholds are DECLARED
- Classifier is stateless — each call is independent; no temporal smoothing
