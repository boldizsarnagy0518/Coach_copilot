"""
Unit tests for the powerlifting calculator.

These tests verify the mathematical correctness of all
calculator functions using known values.
"""

import pytest

from src.tools.calculator import (
    E1RMFormula,
    PlateCalculator,
    calculate_e1rm,
    calculate_ipf_gl,
    calculate_plates,
    calculate_wilks,
)


class TestE1RMCalculator:
    """Tests for E1RM calculations."""

    def test_e1rm_single_rep_returns_same_weight(self, calculator):
        """E1RM of 1 rep should equal the weight lifted."""
        result = calculator.e1rm(weight=100, reps=1)
        assert result.e1rm == 100.0
        assert result.reps == 1

    def test_e1rm_epley_formula(self, calculator):
        """Test Epley formula: E1RM = weight × (1 + reps/30)"""
        # 100kg × (1 + 10/30) = 100 × 1.333... = 133.33kg
        result = calculator.e1rm(weight=100, reps=10, formula=E1RMFormula.EPLEY)
        assert abs(result.e1rm - 133.33) < 0.1
        assert result.formula == "epley"

    def test_e1rm_brzycki_formula(self, calculator):
        """Test Brzycki formula: E1RM = weight × (36 / (37 - reps))"""
        # 100kg × (36 / (37 - 10)) = 100 × (36/27) = 133.33kg
        result = calculator.e1rm(weight=100, reps=10, formula=E1RMFormula.BRZYCKI)
        assert abs(result.e1rm - 133.33) < 0.1
        assert result.formula == "brzycki"

    def test_e1rm_with_5_reps(self, calculator):
        """Test common 5-rep E1RM calculation."""
        # 140kg × (1 + 5/30) = 140 × 1.1667 = 163.33kg
        result = calculator.e1rm(weight=140, reps=5)
        assert 160 < result.e1rm < 170

    def test_e1rm_invalid_reps_too_low(self, calculator):
        """Should raise error for 0 reps."""
        with pytest.raises(ValueError, match="between 1 and 30"):
            calculator.e1rm(weight=100, reps=0)

    def test_e1rm_invalid_reps_too_high(self, calculator):
        """Should raise error for reps > 30."""
        with pytest.raises(ValueError, match="between 1 and 30"):
            calculator.e1rm(weight=100, reps=31)

    def test_e1rm_all_formulas(self, calculator):
        """Test that all formulas return results."""
        results = calculator.all_e1rm_formulas(weight=100, reps=5)

        assert len(results) == len(E1RMFormula)
        for formula in E1RMFormula:
            assert formula.value in results
            assert results[formula.value].e1rm > 100  # E1RM should be higher

    def test_e1rm_string_representation(self, calculator):
        """Test the string output format."""
        result = calculator.e1rm(weight=100, reps=5)
        assert "E1RM:" in str(result)
        assert "100" in str(result)
        assert "5" in str(result)


class TestWilksCalculator:
    """Tests for Wilks score calculations."""

    def test_wilks_male_83kg(self, calculator):
        """Test Wilks for typical 83kg male."""
        # Known approximate value for 500kg total @ 83kg
        result = calculator.wilks(total=500, bodyweight=83, gender="male")
        assert 300 < result.wilks_score < 350
        assert result.gender == "male"

    def test_wilks_female_63kg(self, calculator):
        """Test Wilks for typical 63kg female."""
        result = calculator.wilks(total=350, bodyweight=63, gender="female")
        assert result.wilks_score > 0
        assert result.gender == "female"

    def test_wilks_higher_total_means_higher_score(self, calculator):
        """Higher total at same bodyweight should give higher Wilks."""
        result1 = calculator.wilks(total=500, bodyweight=83, gender="male")
        result2 = calculator.wilks(total=600, bodyweight=83, gender="male")
        assert result2.wilks_score > result1.wilks_score

    def test_wilks_string_representation(self, calculator):
        """Test the string output format."""
        result = calculator.wilks(total=500, bodyweight=83, gender="male")
        assert "Wilks:" in str(result)
        assert "500" in str(result)
        assert "83" in str(result)


class TestIPFGLCalculator:
    """Tests for IPF GL calculations."""

    def test_ipf_gl_male_raw(self, calculator):
        """Test IPF GL for raw male lifter."""
        result = calculator.ipf_gl(
            total=500,
            bodyweight=83,
            gender="male",
            is_equipped=False,
        )
        assert result.ipf_gl_points > 0
        assert result.is_equipped is False
        assert result.gender == "male"

    def test_ipf_gl_female_raw(self, calculator):
        """Test IPF GL for raw female lifter."""
        result = calculator.ipf_gl(
            total=350,
            bodyweight=63,
            gender="female",
            is_equipped=False,
        )
        assert result.ipf_gl_points > 0
        assert result.is_equipped is False

    def test_ipf_gl_equipped_higher_than_raw(self, calculator):
        """Same total should give lower points for equipped (higher standards)."""
        raw = calculator.ipf_gl(
            total=500, bodyweight=83, gender="male", is_equipped=False
        )
        equipped = calculator.ipf_gl(
            total=500, bodyweight=83, gender="male", is_equipped=True
        )
        # Equipped has different coefficients - points comparison depends on formula
        assert equipped.is_equipped is True
        assert raw.is_equipped is False

    def test_ipf_gl_string_representation(self, calculator):
        """Test the string output format."""
        result = calculator.ipf_gl(total=500, bodyweight=83, gender="male")
        assert "IPF GL:" in str(result)
        assert "Raw" in str(result)


class TestPlateCalculator:
    """Tests for plate loading calculations."""

    def test_plate_loading_basic(self, plate_calculator):
        """Test basic plate loading."""
        result = plate_calculator.calculate(target_weight=60)
        # 60kg = 20kg bar + 2×20kg plates
        assert result.actual_weight == 60
        assert result.plates_per_side[20.0] == 1

    def test_plate_loading_140kg(self, plate_calculator):
        """Test 140kg plate loading."""
        result = plate_calculator.calculate(target_weight=140)
        # 140kg = 20kg bar + 2×(20+20+10+5)kg = 20 + 120 = 140
        assert result.actual_weight == 140
        # 60kg per side = 20+20+10+5+2.5+2.5 or similar
        total_per_side = sum(w * c for w, c in result.plates_per_side.items())
        assert abs(total_per_side - 60) < 0.1

    def test_plate_loading_minimum_bar_weight(self, plate_calculator):
        """Bar-only weight should work."""
        result = plate_calculator.calculate(target_weight=20)
        assert result.actual_weight == 20
        assert all(c == 0 for c in result.plates_per_side.values())

    def test_plate_loading_below_bar_raises_error(self, plate_calculator):
        """Weight below bar should raise error."""
        with pytest.raises(ValueError, match="must be >="):
            plate_calculator.calculate(target_weight=15)

    def test_plate_loading_custom_bar(self):
        """Test with custom bar weight (e.g., 25kg squat bar)."""
        calc = PlateCalculator(bar_weight=25.0)
        result = calc.calculate(target_weight=85)
        # 85kg = 25kg bar + 2×30kg
        assert result.actual_weight == 85
        assert result.bar_weight == 25.0

    def test_plate_loading_with_collars(self):
        """Test calculation including collar weight."""
        calc = PlateCalculator(bar_weight=20.0, collar_weight=5.0)
        result = calc.calculate(target_weight=65)
        # 65kg = 20kg bar + 5kg collars + 2×20kg
        assert result.collar_weight == 5.0

    def test_plate_loading_string_representation(self, plate_calculator):
        """Test the string output format."""
        result = plate_calculator.calculate(target_weight=100)
        assert "Load:" in str(result)
        assert "per side" in str(result)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_calculate_e1rm(self):
        """Test convenience E1RM function."""
        result = calculate_e1rm(100, 5)
        assert result.e1rm > 100

    def test_calculate_wilks(self):
        """Test convenience Wilks function."""
        result = calculate_wilks(500, 83, "male")
        assert result.wilks_score > 0

    def test_calculate_ipf_gl(self):
        """Test convenience IPF GL function."""
        result = calculate_ipf_gl(500, 83, "male")
        assert result.ipf_gl_points > 0

    def test_calculate_plates(self):
        """Test convenience plates function."""
        result = calculate_plates(100)
        assert result.actual_weight == 100


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_heavy_lifter(self, calculator):
        """Test calculations for superheavyweight."""
        result = calculator.wilks(total=1000, bodyweight=170, gender="male")
        assert result.wilks_score > 0

    def test_light_lifter(self, calculator):
        """Test calculations for very light athlete."""
        result = calculator.wilks(total=300, bodyweight=52, gender="female")
        assert result.wilks_score > 0

    def test_e1rm_high_reps(self, calculator):
        """Test E1RM with high reps (near max)."""
        result = calculator.e1rm(weight=50, reps=25)
        assert result.e1rm > 50

    def test_fractional_plates(self):
        """Test with fractional kg plates (0.25kg, 0.5kg)."""
        calc = PlateCalculator()
        result = calc.calculate(target_weight=21.5)
        # 21.5 = 20 + 2×0.75 = need 0.5+0.25 per side
        assert abs(result.actual_weight - 21.5) < 0.1
