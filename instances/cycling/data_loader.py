"""
Synthetic cycling ride generator for the cycling intent instance.

Produces a sequence of samples simulating a realistic ride segment:
  - warm-up (RECOVER zone)
  - tempo effort (MAINTAIN zone)
  - attack surge (ATTACK zone)
  - recovery after surge (RECOVER zone)
  - final push (ATTACK zone)

All power values are DECLARED — physics-plausible but not from real hardware.
Fatigue grows linearly with elapsed time (same model as sensory_architecture_factory
ENMAX instance: vigilance decrement analog for muscular fatigue).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class RideSample:
    t: float           # elapsed seconds
    power_w: float     # DECLARED
    ftp_w: float       # DECLARED — constant for this rider
    gradient_pct: float  # DECLARED
    fatigue: float     # DECLARED (0..1, linear over max_duration)


def generate_ride(
    ftp_w: float = 300.0,
    duration_s: float = 600.0,
    sample_rate_hz: float = 1.0,
    seed: int = 42,
) -> List[RideSample]:
    """
    Generate a synthetic ride with 5 phases.
    Returns one RideSample per second (or per 1/sample_rate_hz).
    """
    import random
    rng = random.Random(seed)

    dt = 1.0 / sample_rate_hz
    n = int(duration_s / dt)
    max_fatigue_duration = 3600.0  # fatigue model: full fatigue after 1h

    # Phase boundaries (fraction of duration)
    phases = [
        (0.00, 0.15, "warmup"),    # easy spin
        (0.15, 0.45, "tempo"),     # steady effort
        (0.45, 0.55, "attack1"),   # surge
        (0.55, 0.70, "recover1"),  # back off
        (0.70, 0.85, "tempo2"),    # back to work
        (0.85, 1.00, "attack2"),   # final push
    ]

    _POWER = {
        "warmup":  (0.45, 0.55),   # 45-55% FTP
        "tempo":   (0.72, 0.88),   # 72-88% FTP
        "attack1": (1.06, 1.25),   # 106-125% FTP
        "recover1": (0.40, 0.52),  # 40-52% FTP
        "tempo2":  (0.75, 0.90),
        "attack2": (1.08, 1.30),
    }

    _GRADIENT = {
        "warmup":  (-1.0, 2.0),
        "tempo":   (0.0, 4.0),
        "attack1": (3.0, 8.0),
        "recover1": (-2.0, 1.0),
        "tempo2":  (1.0, 5.0),
        "attack2": (4.0, 10.0),
    }

    samples = []
    for i in range(n):
        t = i * dt
        frac = t / duration_s

        phase_name = phases[-1][2]
        for start, end, name in phases:
            if start <= frac < end:
                phase_name = name
                break

        plo, phi = _POWER[phase_name]
        glo, ghi = _GRADIENT[phase_name]

        power = ftp_w * (plo + rng.random() * (phi - plo))
        gradient = glo + rng.random() * (ghi - glo)
        fatigue = min(t / max_fatigue_duration, 1.0)

        samples.append(RideSample(
            t=round(t, 3),
            power_w=round(power, 1),
            ftp_w=ftp_w,
            gradient_pct=round(gradient, 2),
            fatigue=round(fatigue, 4),
        ))

    return samples
