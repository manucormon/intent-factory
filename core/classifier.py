"""
Intent classifier — infers current athletic intent from sensor state.

State vector: power_w, ftp_w, gradient_pct, fatigue (0..1)
Output: IntentState with label ATTACK | MAINTAIN | RECOVER

Confidence vocabulary:
  OBSERVED   — raw sensor reading (power, gradient)
  CLASSIFIED — intent label inferred from current state
  PROJECTED  — future intent sequence (see project_ahead)

Classification logic (all thresholds DECLARED):
  ATTACK  : power_ratio > ATTACK_THRESH  AND  gradient < GRADIENT_CEILING
              AND  fatigue < FATIGUE_CEILING
  RECOVER : power_ratio < RECOVER_THRESH  OR  fatigue > FATIGUE_FLOOR_RECOVER
  MAINTAIN: everything else

  ATTACK_THRESH       = 1.05  (105% FTP — clear effort spike)
  RECOVER_THRESH      = 0.55  (55% FTP — deliberate backing off)
  GRADIENT_CEILING    = 15.0  (% grade above which attack is physically implausible)
  FATIGUE_CEILING     = 0.85  (fatigue above this suppresses attack intent)
  FATIGUE_FLOOR_RECOVER = 0.90 (extreme fatigue forces recovery regardless of power)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Optional


IntentLabel = Literal["ATTACK", "MAINTAIN", "RECOVER"]

# --- Thresholds (DECLARED) --------------------------------------------------
_ATTACK_THRESH         = 1.05
_RECOVER_THRESH        = 0.55
_GRADIENT_CEILING      = 15.0
_FATIGUE_CEILING       = 0.85
_FATIGUE_FLOOR_RECOVER = 0.90


@dataclass
class IntentState:
    label: IntentLabel        # CLASSIFIED
    power_ratio: float        # power_w / ftp_w — OBSERVED
    gradient_pct: float       # OBSERVED
    fatigue: float            # OBSERVED (0..1)
    attack_suppressed: bool   # True when fatigue blocked an otherwise-ATTACK reading
    confidence: str = "CLASSIFIED"


@dataclass
class ProjectedIntent:
    steps: int
    labels: list            # list[IntentLabel], length == steps
    dt_ahead: float         # seconds this sequence covers
    confidence: str = "PROJECTED"


class IntentClassifier:
    """
    Stateless intent classifier — each call is independent.

    dt: assumed seconds between samples (used only in project_ahead).
    """

    def __init__(self, dt: float = 1.0):
        if dt <= 0 or not math.isfinite(dt):
            raise ValueError(f"dt must be positive and finite, got {dt}")
        self.dt = dt

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(
        self,
        power_w: float,
        ftp_w: float,
        gradient_pct: float = 0.0,
        fatigue: float = 0.0,
    ) -> IntentState:
        """
        Classify intent from a single OBSERVED sample.
        Raises ValueError on invalid inputs.
        """
        self._validate(power_w, ftp_w, gradient_pct, fatigue)

        ratio = power_w / ftp_w
        attack_suppressed = False

        # Extreme fatigue forces recovery regardless of power
        if fatigue >= _FATIGUE_FLOOR_RECOVER:
            label: IntentLabel = "RECOVER"
        elif ratio < _RECOVER_THRESH:
            label = "RECOVER"
        elif ratio > _ATTACK_THRESH:
            if gradient_pct > _GRADIENT_CEILING or fatigue >= _FATIGUE_CEILING:
                label = "MAINTAIN"
                attack_suppressed = True
            else:
                label = "ATTACK"
        else:
            label = "MAINTAIN"

        return IntentState(
            label=label,
            power_ratio=ratio,
            gradient_pct=gradient_pct,
            fatigue=fatigue,
            attack_suppressed=attack_suppressed,
        )

    def project_ahead(
        self,
        samples: list,
        steps: int,
    ) -> ProjectedIntent:
        """
        Classify intent for each sample in `samples` (list of dicts with
        keys: power_w, ftp_w, gradient_pct, fatigue).
        Returns a PROJECTED sequence of IntentLabels.

        steps must equal len(samples).
        """
        if steps != len(samples):
            raise ValueError(
                f"steps ({steps}) must equal len(samples) ({len(samples)})"
            )
        if steps <= 0:
            raise ValueError(f"steps must be > 0, got {steps}")

        labels = [
            self.classify(
                s["power_w"],
                s["ftp_w"],
                s.get("gradient_pct", 0.0),
                s.get("fatigue", 0.0),
            ).label
            for s in samples
        ]

        return ProjectedIntent(
            steps=steps,
            labels=labels,
            dt_ahead=steps * self.dt,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(
        power_w: float,
        ftp_w: float,
        gradient_pct: float,
        fatigue: float,
    ) -> None:
        if not math.isfinite(power_w) or power_w < 0:
            raise ValueError(f"power_w must be finite and ≥ 0, got {power_w}")
        if not math.isfinite(ftp_w) or ftp_w <= 0:
            raise ValueError(f"ftp_w must be finite and > 0, got {ftp_w}")
        if not math.isfinite(gradient_pct) or not (-20.0 <= gradient_pct <= 20.0):
            raise ValueError(f"gradient_pct must be in [-20, 20], got {gradient_pct}")
        if not math.isfinite(fatigue) or not (0.0 <= fatigue <= 1.0):
            raise ValueError(f"fatigue must be in [0, 1], got {fatigue}")
