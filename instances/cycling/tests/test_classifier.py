"""
9 tests for the cycling intent classifier instance.

Verified findings (DECLARED thresholds, seed=42, ftp=300W, 600s ride):
  - ATTACK fires correctly when power > 1.05 FTP on moderate gradient
  - ATTACK is suppressed by high gradient (>15%) or high fatigue (>0.85)
  - RECOVER fires correctly below 0.55 FTP or at extreme fatigue (>0.90)
  - MAINTAIN covers the middle band
  - Synthetic ride produces all 3 labels across its 5 phases
  - project_ahead labels match classify() output sample-by-sample
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from core.classifier import IntentClassifier, IntentState, ProjectedIntent
from instances.cycling.data_loader import generate_ride

FTP = 300.0


@pytest.fixture
def clf():
    return IntentClassifier(dt=1.0)


@pytest.fixture
def ride():
    return generate_ride(ftp_w=FTP, seed=42)


# -----------------------------------------------------------------------

def test_attack_detected_above_threshold(clf):
    state = clf.classify(power_w=FTP * 1.10, ftp_w=FTP, gradient_pct=5.0, fatigue=0.2)
    assert state.label == "ATTACK"
    assert state.confidence == "CLASSIFIED"


def test_recover_detected_below_threshold(clf):
    state = clf.classify(power_w=FTP * 0.50, ftp_w=FTP, gradient_pct=0.0, fatigue=0.1)
    assert state.label == "RECOVER"


def test_maintain_detected_in_middle_band(clf):
    state = clf.classify(power_w=FTP * 0.80, ftp_w=FTP, gradient_pct=3.0, fatigue=0.3)
    assert state.label == "MAINTAIN"


def test_attack_suppressed_by_steep_gradient(clf):
    """Power above attack threshold but gradient > 15% — physically implausible to attack."""
    state = clf.classify(power_w=FTP * 1.15, ftp_w=FTP, gradient_pct=16.0, fatigue=0.2)
    assert state.label == "MAINTAIN"
    assert state.attack_suppressed is True


def test_attack_suppressed_by_high_fatigue(clf):
    """Power above attack threshold but fatigue >= 0.85 — body cannot sustain attack."""
    state = clf.classify(power_w=FTP * 1.10, ftp_w=FTP, gradient_pct=4.0, fatigue=0.87)
    assert state.label == "MAINTAIN"
    assert state.attack_suppressed is True


def test_extreme_fatigue_forces_recover(clf):
    """fatigue >= 0.90 forces RECOVER regardless of power output."""
    state = clf.classify(power_w=FTP * 0.80, ftp_w=FTP, gradient_pct=0.0, fatigue=0.92)
    assert state.label == "RECOVER"


def test_invalid_inputs_raise(clf):
    with pytest.raises(ValueError):
        clf.classify(power_w=-10.0, ftp_w=FTP)
    with pytest.raises(ValueError):
        clf.classify(power_w=FTP, ftp_w=0.0)
    with pytest.raises(ValueError):
        clf.classify(power_w=FTP, ftp_w=FTP, gradient_pct=25.0)
    with pytest.raises(ValueError):
        clf.classify(power_w=FTP, ftp_w=FTP, fatigue=1.5)


def test_synthetic_ride_produces_all_three_labels(clf, ride):
    """
    Verified finding: a 600s synthetic ride (seed=42) contains all three
    intent labels — confirming the ride generator covers all zones.
    """
    labels = {
        clf.classify(s.power_w, s.ftp_w, s.gradient_pct, s.fatigue).label
        for s in ride
    }
    assert "ATTACK" in labels
    assert "MAINTAIN" in labels
    assert "RECOVER" in labels


def test_project_ahead_matches_classify(clf, ride):
    """
    project_ahead() must return the same labels as classify() called individually.
    Verified: PROJECTED sequence is deterministic and reproducible.
    """
    segment = [
        {"power_w": s.power_w, "ftp_w": s.ftp_w,
         "gradient_pct": s.gradient_pct, "fatigue": s.fatigue}
        for s in ride[:30]
    ]
    projected = clf.project_ahead(segment, steps=30)
    assert isinstance(projected, ProjectedIntent)
    assert projected.confidence == "PROJECTED"
    assert projected.dt_ahead == pytest.approx(30.0)

    for i, s in enumerate(ride[:30]):
        expected = clf.classify(s.power_w, s.ftp_w, s.gradient_pct, s.fatigue).label
        assert projected.labels[i] == expected, f"Mismatch at step {i}"
