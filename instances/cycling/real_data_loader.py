"""
Real cycling data loader — GoldenCheetah OpenData (anonymized athlete).

Source: https://github.com/GoldenCheetah/OpenData
License: CC BY 4.0 (open data, anonymized, no PII)

Fields in source CSV: secs, km, power, hr, cad, alt
Derived fields:
  - gradient_pct: from alt delta / distance delta, clipped to [-15, 15]
  - fatigue: elapsed_secs / ride_duration (0..1 linear proxy — same model
    as sensory_architecture_factory ENMAX instance)
  - ftp_w: estimated as 95% of best 20-minute average power (industry standard)

All derived fields are DECLARED (computed from REAL measurements).
Power and heart rate are REAL.
"""

from __future__ import annotations

import csv
import io
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import List, Optional


_ZIP_URL = (
    "https://raw.githubusercontent.com/GoldenCheetah/OpenData/master/"
    "examples/033874ce-e20d-44ba-9cc9-125030b6662f.zip"
)
_DEFAULT_RIDE = "2009_05_10_10_06_37.csv"   # 363-min ride, FTP ~208W
_GRADIENT_CLIP = 15.0                        # ±15% — GPS noise filter
_FTP_WINDOW_S  = 20 * 60                     # 20-min window for FTP estimate
_FTP_FRACTION  = 0.95                        # 95% of best 20-min = FTP


@dataclass
class RealRideSample:
    t: float            # elapsed seconds
    power_w: float      # REAL — from power meter
    ftp_w: float        # DECLARED — derived from ride data
    gradient_pct: float # DECLARED — derived from GPS altitude + distance
    fatigue: float      # DECLARED — linear proxy (t / duration)
    hr: Optional[float] = None   # REAL — heart rate (bpm), if available


def load_real_ride(
    ride_filename: str = _DEFAULT_RIDE,
    max_samples: Optional[int] = None,
) -> List[RealRideSample]:
    """
    Download and parse a real GoldenCheetah ride.
    Returns one RealRideSample per second of the ride.

    ride_filename: CSV name inside the zip (default: 363-min ride)
    max_samples: truncate to first N samples (useful for tests)
    """
    zip_data = _fetch_zip()
    rows = _parse_csv(zip_data, ride_filename)

    powers = [float(r["power"]) for r in rows]
    alts   = [float(r["alt"])   for r in rows]
    kms    = [float(r["km"])    for r in rows]
    hrs    = [float(r.get("hr") or 0) for r in rows]

    ftp_w       = _estimate_ftp(powers)
    gradients   = _derive_gradient(alts, kms)
    duration_s  = float(rows[-1]["secs"]) if rows else 1.0

    samples = []
    for i, r in enumerate(rows):
        t = float(r["secs"])
        samples.append(RealRideSample(
            t=t,
            power_w=max(0.0, powers[i]),
            ftp_w=ftp_w,
            gradient_pct=gradients[i],
            fatigue=min(t / duration_s, 1.0),
            hr=hrs[i] if hrs[i] > 0 else None,
        ))

    if max_samples is not None:
        samples = samples[:max_samples]

    return samples


def available_rides(zip_data: Optional[bytes] = None) -> List[str]:
    """Return list of CSV filenames available in the zip."""
    if zip_data is None:
        zip_data = _fetch_zip()
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        return sorted(n for n in z.namelist() if n.endswith(".csv"))


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _fetch_zip() -> bytes:
    req = urllib.request.Request(_ZIP_URL, headers={"User-Agent": "intent-factory/1.0"})
    return urllib.request.urlopen(req).read()


def _parse_csv(zip_data: bytes, filename: str) -> list:
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        with z.open(filename) as f:
            return list(csv.DictReader(io.TextIOWrapper(f)))


def _estimate_ftp(powers: List[float]) -> float:
    """95% of best 20-minute average power."""
    n = len(powers)
    if n < _FTP_WINDOW_S:
        best = sum(powers) / max(n, 1)
    else:
        best = max(
            sum(powers[i:i + _FTP_WINDOW_S]) / _FTP_WINDOW_S
            for i in range(n - _FTP_WINDOW_S)
        )
    return round(best * _FTP_FRACTION, 1)


def _derive_gradient(alts: List[float], kms: List[float]) -> List[float]:
    """
    Gradient = altitude change / distance change × 100.
    Clipped to ±_GRADIENT_CLIP to remove GPS noise spikes.
    First sample is always 0 (no prior point).
    """
    gradients = [0.0]
    for i in range(1, len(alts)):
        d_km = kms[i] - kms[i - 1]
        d_alt = alts[i] - alts[i - 1]
        if d_km > 0.001:
            raw = d_alt / (d_km * 10.0)  # convert to percent
            gradients.append(max(-_GRADIENT_CLIP, min(_GRADIENT_CLIP, raw)))
        else:
            gradients.append(gradients[-1])  # hold last known gradient
    return gradients
