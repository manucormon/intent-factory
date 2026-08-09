# CONTRACT.md — cycling instance

## Instance identity
- **Domain:** competitive cycling — intent classification from power meter data
- **Data source:** synthetic (DECLARED) — physics-plausible ride generator
- **Status:** verified

## Capability declarations

| Capability | Value | Evidence |
|---|---|---|
| HAS_ATTACK_SUPPRESSION | True | gradient ceiling + fatigue ceiling; tested |
| HAS_EXTREME_FATIGUE_OVERRIDE | True | fatigue ≥ 0.90 forces RECOVER; tested |
| HAS_PROJECTION | True | `project_ahead(samples, steps)` → PROJECTED sequence |
| DATA_LABEL | DECLARED | synthetic ride generator; no real power meter |

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

## Key verified findings (DECLARED thresholds, seed=42, ftp=300W, 600s)
- ATTACK fires at power > 1.05 FTP on gradient ≤ 15% and fatigue < 0.85
- ATTACK is suppressed (→ MAINTAIN) when gradient > 15% or fatigue ≥ 0.85
- Extreme fatigue (≥ 0.90) forces RECOVER regardless of power output
- Synthetic 600s ride contains all three intent labels (warm-up → tempo → attack → recover)

## What this instance does NOT do
- Does not infer intent from heart rate or cadence (not in input)
- Does not model race tactics (breakaway, drafting) — those belong in 03_planning
- Does not learn thresholds from data — all thresholds are DECLARED
- Classifier is stateless — each call is independent; no temporal smoothing
