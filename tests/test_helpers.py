"""
Unit tests for tm_helpers.py functions.
"""

import pytest
from types import SimpleNamespace
from tm_helpers import isSamePoint, isSameCircle, calc_blind_hole_depth


class TestIsSamePoint:
    """Test isSamePoint function with simple point objects."""

    def test_identical_points(self):
        """Identical points should return True."""
        p1 = SimpleNamespace(x=1.0, y=2.0, z=3.0)
        p2 = SimpleNamespace(x=1.0, y=2.0, z=3.0)
        assert isSamePoint(p1, p2, tol=1e-6) is True

    def test_points_within_tolerance(self):
        """Points within tolerance should return True."""
        p1 = SimpleNamespace(x=1.0, y=2.0, z=3.0)
        p2 = SimpleNamespace(x=1.0 + 1e-7, y=2.0 + 1e-7, z=3.0 + 1e-7)
        assert isSamePoint(p1, p2, tol=1e-6) is True

    def test_points_outside_tolerance(self):
        """Points outside tolerance should return False."""
        p1 = SimpleNamespace(x=1.0, y=2.0, z=3.0)
        p2 = SimpleNamespace(x=1.0 + 1e-5, y=2.0, z=3.0)
        assert isSamePoint(p1, p2, tol=1e-6) is False

    def test_different_x_coordinate(self):
        """Different X should return False."""
        p1 = SimpleNamespace(x=1.0, y=2.0, z=3.0)
        p2 = SimpleNamespace(x=2.0, y=2.0, z=3.0)
        assert isSamePoint(p1, p2, tol=1e-6) is False

    def test_different_y_coordinate(self):
        """Different Y should return False."""
        p1 = SimpleNamespace(x=1.0, y=2.0, z=3.0)
        p2 = SimpleNamespace(x=1.0, y=3.0, z=3.0)
        assert isSamePoint(p1, p2, tol=1e-6) is False

    def test_different_z_coordinate(self):
        """Different Z should return False."""
        p1 = SimpleNamespace(x=1.0, y=2.0, z=3.0)
        p2 = SimpleNamespace(x=1.0, y=2.0, z=4.0)
        assert isSamePoint(p1, p2, tol=1e-6) is False

    def test_custom_tolerance(self):
        """Should use custom tolerance if provided."""
        p1 = SimpleNamespace(x=0.0, y=0.0, z=0.0)
        p2 = SimpleNamespace(x=0.01, y=0.0, z=0.0)
        assert isSamePoint(p1, p2, tol=0.02) is True
        assert isSamePoint(p1, p2, tol=0.001) is False


class TestIsSameCircle:
    """Test isSameCircle function with mocked circle objects."""

    def _make_circle(self, cx, cy, cz, radius):
        """Helper to create a mock circle object."""
        center_point = SimpleNamespace(x=cx, y=cy, z=cz)
        circle = SimpleNamespace(
            centerSketchPoint=SimpleNamespace(geometry=center_point),
            radius=radius
        )
        return circle

    def test_identical_circles(self):
        """Identical circles should return True."""
        c1 = self._make_circle(1.0, 2.0, 3.0, 5.0)
        c2 = self._make_circle(1.0, 2.0, 3.0, 5.0)
        assert isSameCircle(c1, c2, tol=1e-6) is True

    def test_different_center(self):
        """Different center should return False."""
        c1 = self._make_circle(1.0, 2.0, 3.0, 5.0)
        c2 = self._make_circle(2.0, 2.0, 3.0, 5.0)
        assert isSameCircle(c1, c2, tol=1e-6) is False

    def test_different_radius(self):
        """Different radius should return False."""
        c1 = self._make_circle(1.0, 2.0, 3.0, 5.0)
        c2 = self._make_circle(1.0, 2.0, 3.0, 6.0)
        assert isSameCircle(c1, c2, tol=1e-6) is False

    def test_radius_within_tolerance(self):
        """Radius within tolerance should return True."""
        c1 = self._make_circle(1.0, 2.0, 3.0, 5.0)
        c2 = self._make_circle(1.0, 2.0, 3.0, 5.0 + 1e-7)
        assert isSameCircle(c1, c2, tol=1e-6) is True


class TestCalcBlindHoleDepth:
    """Test calc_blind_hole_depth function."""

    def test_m3_standard(self):
        """M3 standard: 5.7mm + 1.0mm = 6.7mm = 0.67cm."""
        result = calc_blind_hole_depth(5.7, 1.0)
        assert result == pytest.approx(0.67, abs=1e-9)

    def test_m4_standard(self):
        """M4 standard: 8.1mm + 1.0mm = 9.1mm = 0.91cm."""
        result = calc_blind_hole_depth(8.1, 1.0)
        assert result == pytest.approx(0.91, abs=1e-9)

    def test_zero_extra_depth(self):
        """No extra depth: 5.7mm = 0.57cm."""
        result = calc_blind_hole_depth(5.7, 0.0)
        assert result == pytest.approx(0.57, abs=1e-9)

    def test_zero_insert_length(self):
        """No insert length: 1.0mm extra = 0.1cm."""
        result = calc_blind_hole_depth(0.0, 1.0)
        assert result == pytest.approx(0.1, abs=1e-9)

    def test_m6_insert(self):
        """M6: 12.7mm + 1.0mm = 13.7mm = 1.37cm."""
        result = calc_blind_hole_depth(12.7, 1.0)
        assert result == pytest.approx(1.37, abs=1e-9)

    def test_custom_extra_depth(self):
        """Custom extra depth: 5.0mm + 2.5mm = 7.5mm = 0.75cm."""
        result = calc_blind_hole_depth(5.0, 2.5)
        assert result == pytest.approx(0.75, abs=1e-9)
