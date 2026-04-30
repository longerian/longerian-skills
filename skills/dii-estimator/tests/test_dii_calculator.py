"""Tests for DII calculator."""
import math
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dii_calculator import norm_cdf, calculate_dii, interpret_dii


def test_norm_cdf_at_zero():
    """norm_cdf(0) should return 0.5."""
    assert abs(norm_cdf(0) - 0.5) < 1e-10


def test_norm_cdf_positive():
    """norm_cdf(1.96) should be approximately 0.975."""
    assert abs(norm_cdf(1.96) - 0.975) < 0.001


def test_norm_cdf_negative():
    """norm_cdf(-1.96) should be approximately 0.025."""
    assert abs(norm_cdf(-1.96) - 0.025) < 0.001


def test_norm_cdf_large_positive():
    """norm_cdf(10) should be approximately 1.0."""
    assert abs(norm_cdf(10) - 1.0) < 1e-10


def test_norm_cdf_large_negative():
    """norm_cdf(-10) should be approximately 0.0."""
    assert abs(norm_cdf(-10) - 0.0) < 1e-10


def test_calculate_dii_at_global_mean():
    """When all nutrient values equal global mean, DII should be 0."""
    params = {
        "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
        "VITB12": {"inflammatory_score": 0.106, "global_mean": 5.15, "sd": 2.7},
    }
    nutrients = {
        "ALCOHOL": 13.98,
        "VITB12": 5.15,
    }
    score, components = calculate_dii(nutrients, params)
    assert abs(score) < 1e-10


def test_calculate_dii_anti_inflammatory():
    """High fiber (anti-inflammatory) should produce negative DII."""
    params = {
        "FIBER": {"inflammatory_score": -0.663, "global_mean": 18.8, "sd": 4.9},
    }
    nutrients = {"FIBER": 30}  # Well above mean
    score, components = calculate_dii(nutrients, params)
    assert score < 0
    assert components["FIBER"]["direction"] == "anti"


def test_calculate_dii_pro_inflammatory():
    """High saturated fat (pro-inflammatory) should produce positive DII."""
    params = {
        "SATFAT": {"inflammatory_score": 0.373, "global_mean": 28.6, "sd": 8},
    }
    nutrients = {"SATFAT": 50}  # Well above mean
    score, components = calculate_dii(nutrients, params)
    assert score > 0
    assert components["SATFAT"]["direction"] == "pro"


def test_calculate_dii_skips_missing_params():
    """Missing nutrient keys should be skipped, not cause errors."""
    params = {
        "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
        "VITB12": {"inflammatory_score": 0.106, "global_mean": 5.15, "sd": 2.7},
    }
    nutrients = {"ALCOHOL": 10}  # VITB12 not provided
    score, components = calculate_dii(nutrients, params)
    assert "ALCOHOL" in components
    assert "VITB12" not in components


def test_interpret_dii_strong_anti():
    """DII < -1 should be anti-inflammatory."""
    level, label = interpret_dii(-2.0)
    assert level == "anti_inflammatory"
    assert "抗炎饮食" in label


def test_interpret_dii_mild_anti():
    """-1 <= DII < 0 should be mild anti-inflammatory."""
    level, label = interpret_dii(-0.5)
    assert level == "mild_anti_inflammatory"
    assert "轻度抗炎饮食" in label


def test_interpret_dii_mild_pro():
    """0 <= DII < 1 should be mild pro-inflammatory."""
    level, label = interpret_dii(0.5)
    assert level == "mild_pro_inflammatory"
    assert "轻度促炎饮食" in label


def test_interpret_dii_strong_pro():
    """DII >= 1 should be pro-inflammatory."""
    level, label = interpret_dii(2.0)
    assert level == "pro_inflammatory"
    assert "促炎饮食" in label


def test_interpret_dii_zero():
    """DII = 0 should be mild pro-inflammatory (boundary)."""
    level, label = interpret_dii(0.0)
    assert level == "mild_pro_inflammatory"


def test_direction_neutral():
    """A score of exactly 0 should be classified as neutral."""
    params = {
        "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
    }
    nutrients = {"ALCOHOL": 13.98}  # Exactly at mean -> percentile=0 -> score=0
    score, components = calculate_dii(nutrients, params)
    assert components["ALCOHOL"]["direction"] == "neutral"


def test_calculate_dii_all_45_params():
    """Test with all 45 parameters provided (full coverage)."""
    import json
    params_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dii_params.json')
    with open(params_path, 'r') as f:
        params = json.load(f)
    # Use global mean values -> DII should be ~0
    nutrients = {name: p['global_mean'] for name, p in params.items()}
    score, components = calculate_dii(nutrients, params)
    assert len(components) == 45
    assert abs(score) < 0.01  # Should be very close to 0


def test_calculate_dii_10_params():
    """Test with only 10 parameters (partial coverage)."""
    params = {
        "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
        "VITB12": {"inflammatory_score": 0.106, "global_mean": 5.15, "sd": 2.7},
        "VITB6": {"inflammatory_score": -0.365, "global_mean": 1.47, "sd": 0.74},
        "BCAROTENE": {"inflammatory_score": -0.584, "global_mean": 3718, "sd": 1720},
        "CAFFEINE": {"inflammatory_score": -0.11, "global_mean": 8.05, "sd": 6.67},
        "CARB": {"inflammatory_score": 0.097, "global_mean": 272.2, "sd": 40},
        "CHOLES": {"inflammatory_score": 0.11, "global_mean": 279.4, "sd": 51.2},
        "KCAL": {"inflammatory_score": 0.18, "global_mean": 2056, "sd": 338},
        "FIBER": {"inflammatory_score": -0.663, "global_mean": 18.8, "sd": 4.9},
        "SATFAT": {"inflammatory_score": 0.373, "global_mean": 28.6, "sd": 8},
    }
    nutrients = {name: p['global_mean'] for name, p in params.items()}
    score, components = calculate_dii(nutrients, params)
    assert len(components) == 10
    assert abs(score) < 0.01


def test_calculate_dii_extreme_high():
    """Test with extreme high values (should not crash)."""
    params = {
        "KCAL": {"inflammatory_score": 0.18, "global_mean": 2056, "sd": 338},
        "SATFAT": {"inflammatory_score": 0.373, "global_mean": 28.6, "sd": 8},
    }
    nutrients = {"KCAL": 10000, "SATFAT": 200}
    score, components = calculate_dii(nutrients, params)
    assert isinstance(score, float)
    assert score > 0  # Extreme high pro-inflammatory values should give positive DII


def test_calculate_dii_extreme_low():
    """Test with extreme low values (should not crash)."""
    params = {
        "FIBER": {"inflammatory_score": -0.663, "global_mean": 18.8, "sd": 4.9},
        "VITC": {"inflammatory_score": -0.424, "global_mean": 118.2, "sd": 43.46},
    }
    nutrients = {"FIBER": 0, "VITC": 0}
    score, components = calculate_dii(nutrients, params)
    assert isinstance(score, float)
    assert score > 0  # Low anti-inflammatory values should give positive DII
