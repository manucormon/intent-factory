# intent_factory

**Kairos family — Brother 2: Classify observable effort state**

Applies declared rules to observable cycling signals and emits an
ATTACK/MAINTAIN/RECOVER effort-state label. These labels have not been validated
against human-intent ground truth and must not be presented as mind-reading or
reliable future-intent prediction.
Sits between `perception_factory` (what is happening physically) and `planning_factory`
(what to do about it).

**Status:** implementation tested (10/10); construct validity and automation-bias
effects are `NOT_EVALUATED`. Permitted use is experimental/observe-only. Do not
use the labels for time-critical human decisions until the documented study gate
in `CONTRACT.md` is satisfied.

## What it does

Takes a snapshot of observable signals and returns a discrete intent label with
a confidence vocabulary:

| Label | Meaning |
|---|---|
| OBSERVED | Raw sensor reading fed into the classifier |
| CLASSIFIED | Intent label inferred from current state |
| PROJECTED | Future intent sequence over N steps |

## Instances

| Instance | Domain | Input | Output |
|---|---|---|---|
| cycling | Competitive cycling | power_w, ftp_w, gradient_pct, fatigue | ATTACK / MAINTAIN / RECOVER |

## Family position

```
perception_factory  →  intent_factory  →  planning_factory  →  sensory_architecture_factory
 (what is moving)      (effort-state label)   (what to do)          (is the human ready)
```

## Quick start

```python
from core.classifier import IntentClassifier

clf = IntentClassifier(dt=1.0)
state = clf.classify(power_w=330, ftp_w=300, gradient_pct=5.0, fatigue=0.2)
print(state.label)        # "ATTACK"
print(state.confidence)   # "CLASSIFIED"

future = clf.project_ahead(samples=[...], steps=30)
print(future.labels)      # ["ATTACK", "ATTACK", "MAINTAIN", ...]
print(future.dt_ahead)    # 30.0 seconds
```

## Tests

```
pytest instances/cycling/tests/
```

10 tests, all passing. Verified findings documented in `instances/cycling/NOTES.md`.

## Guardrail 8 — latency budget
Every prediction exposes `dt_ahead`: how many seconds into the future the
PROJECTED sequence covers. Consumers must compare `dt_ahead` against their
event horizon before acting on PROJECTED labels.
