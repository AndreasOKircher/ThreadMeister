"""
Unit tests for tm_ridge.py: Ridge Thread geometry (pure maths, no Fusion).
"""

import math
import pytest
from core.tm_ridge import ridge_geometry, central_profile_area_mm2


def _grid_area_mm2(g, step=0.01):
    """Independent check: count grid cells inside the bore and outside every Ridge circle."""
    R = g.bore_dia / 2.0
    r = g.ridge_dia / 2.0
    centres = [(g.arc_distance * math.cos(2 * math.pi * i / g.count),
                g.arc_distance * math.sin(2 * math.pi * i / g.count)) for i in range(g.count)]
    n = int(math.ceil(R / step))
    hits = 0
    for ix in range(-n, n):
        x = (ix + 0.5) * step
        for iy in range(-n, n):
            y = (iy + 0.5) * step
            if x * x + y * y > R * R:
                continue
            if any((x - cx) ** 2 + (y - cy) ** 2 < r * r for cx, cy in centres):
                continue
            hits += 1
    return hits * step * step


class TestRidgeGeometry:
    """Geometry of one Ridge Thread size, from the PRD decisions table."""

    @pytest.mark.parametrize('size, inner, ridge_dia', [
        ('M3', 2.40, 1.7),
        ('M4', 3.50, 2.0),
        ('M5', 4.50, 2.5),
    ])
    def test_ridge_dia_from_inner_dia(self, size, inner, ridge_dia):
        assert ridge_geometry(size, inner).ridge_dia == pytest.approx(ridge_dia)

    @pytest.mark.parametrize('size, depth', [('M3', 12.0), ('M4', 16.0), ('M5', 20.0)])
    def test_default_depth_is_four_times_screw_dia(self, size, depth):
        assert ridge_geometry(size, 2.0).default_depth == pytest.approx(depth)

    @pytest.mark.parametrize('size, count', [('M3', 3), ('M4', 3), ('M5', 4)])
    def test_ridge_count(self, size, count):
        assert ridge_geometry(size, 2.0).count == count


class TestCentralProfileArea:
    """Area of the Bore profile: bore circle minus the Ridge lobes."""

    @pytest.mark.parametrize('size, inner', [('M3', 2.40), ('M4', 3.50), ('M5', 4.50)])
    def test_matches_grid_count(self, size, inner):
        g = ridge_geometry(size, inner)
        assert central_profile_area_mm2(g) == pytest.approx(_grid_area_mm2(g), rel=0.005)

    def test_smaller_than_bore_circle(self):
        g = ridge_geometry('M3', 2.40)
        assert central_profile_area_mm2(g) < math.pi * (g.bore_dia / 2.0) ** 2
