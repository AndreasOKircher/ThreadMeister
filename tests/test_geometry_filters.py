"""
Unit tests for tm_geometry.py filter functions.
"""

import pytest
import math
from types import SimpleNamespace
from unittest.mock import MagicMock
from tm_geometry import (
    _filter_by_area,
    _filter_by_centroid,
    _filter_by_bounding_box,
    _accumulate_profiles
)


# Helper functions to create mock objects

def make_point(x, y, z=0.0):
    """Create a point object with x, y, z and distanceTo method."""
    point = SimpleNamespace(x=x, y=y, z=z)

    def distance_to(other):
        return math.sqrt(
            (point.x - other.x)**2 +
            (point.y - other.y)**2 +
            (point.z - other.z)**2
        )

    point.distanceTo = distance_to
    return point


def make_profile(area, centroid_x=0.0, centroid_y=0.0, centroid_z=0.0,
                 bbox_min_x=0.0, bbox_min_y=0.0, bbox_max_x=1.0, bbox_max_y=1.0):
    """Create a mock profile with areaProperties and boundingBox."""
    profile = MagicMock()

    # Mock areaProperties method
    area_props = MagicMock()
    area_props.area = area
    area_props.centroid = make_point(centroid_x, centroid_y, centroid_z)
    profile.areaProperties.return_value = area_props

    # Mock boundingBox
    bbox_min_point = MagicMock()
    bbox_min_point.x = bbox_min_x
    bbox_min_point.y = bbox_min_y

    bbox_max_point = MagicMock()
    bbox_max_point.x = bbox_max_x
    bbox_max_point.y = bbox_max_y

    profile.boundingBox = MagicMock()
    profile.boundingBox.minPoint = bbox_min_point
    profile.boundingBox.maxPoint = bbox_max_point

    return profile


class TestFilterByArea:
    """Test _filter_by_area function."""

    def test_profile_with_exact_target_area(self):
        """Profile with exact target area should be included."""
        target_area = 10.0
        profile = make_profile(area=10.0)

        # Create a mock sketch
        sketch = MagicMock()
        sketch.profiles = [profile]

        result = _filter_by_area(sketch, target_area)

        assert len(result) == 1
        assert result[0][0] == profile
        assert result[0][1] == 10.0

    def test_profile_within_1_percent_threshold(self):
        """Profile with area within 1% of target should be included."""
        target_area = 10.0
        profile = make_profile(area=10.09)  # 1.009 * target

        sketch = MagicMock()
        sketch.profiles = [profile]

        result = _filter_by_area(sketch, target_area)

        assert len(result) == 1

    def test_profile_exceeds_1_percent_threshold(self):
        """Profile with area >1% above target should be excluded."""
        target_area = 10.0
        profile = make_profile(area=10.11)  # > 1.01 * target

        sketch = MagicMock()
        sketch.profiles = [profile]

        result = _filter_by_area(sketch, target_area)

        assert len(result) == 0

    def test_multiple_profiles_filtered(self):
        """Filter multiple profiles by area."""
        target_area = 10.0
        # Threshold: target_area * 1.01 = 10.1
        profile1 = make_profile(area=9.5)       # < 10.1: included
        profile2 = make_profile(area=10.0)      # <= 10.1: included
        profile3 = make_profile(area=10.05)     # <= 10.1: included
        profile4 = make_profile(area=15.0)      # > 10.1: excluded

        sketch = MagicMock()
        sketch.profiles = [profile1, profile2, profile3, profile4]

        result = _filter_by_area(sketch, target_area)

        # profile1, profile2, profile3 should be included; profile4 excluded
        assert len(result) == 3
        assert profile1 in [p for p, _ in result]
        assert profile2 in [p for p, _ in result]
        assert profile3 in [p for p, _ in result]
        assert profile4 not in [p for p, _ in result]

    def test_empty_profiles(self):
        """Empty profile list should return empty."""
        sketch = MagicMock()
        sketch.profiles = []

        result = _filter_by_area(sketch, 10.0)

        assert len(result) == 0


class TestFilterByCentroid:
    """Test _filter_by_centroid function."""

    def test_centroid_at_circle_center(self):
        """Centroid at circle center should be included."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 5.0

        profile = make_profile(area=10.0, centroid_x=0.0, centroid_y=0.0, centroid_z=0.0)
        candidates = [(profile, 10.0)]

        result = _filter_by_centroid(candidates, circle_center, circle_radius)

        assert len(result) == 1
        assert result[0][0] == profile

    def test_centroid_at_circle_edge(self):
        """Centroid at circle edge (distance == radius) should be included."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 5.0

        # Centroid at distance 5.0 from center
        profile = make_profile(area=10.0, centroid_x=5.0, centroid_y=0.0, centroid_z=0.0)
        candidates = [(profile, 10.0)]

        result = _filter_by_centroid(candidates, circle_center, circle_radius)

        assert len(result) == 1

    def test_centroid_outside_circle(self):
        """Centroid outside circle should be excluded."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 5.0

        # Centroid at distance 6.0 from center
        profile = make_profile(area=10.0, centroid_x=6.0, centroid_y=0.0, centroid_z=0.0)
        candidates = [(profile, 10.0)]

        result = _filter_by_centroid(candidates, circle_center, circle_radius)

        assert len(result) == 0

    def test_multiple_candidates_filtered(self):
        """Filter multiple candidates by centroid."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 5.0

        profile1 = make_profile(area=5.0, centroid_x=0.0, centroid_y=0.0)
        profile2 = make_profile(area=6.0, centroid_x=3.0, centroid_y=4.0)  # distance 5.0
        profile3 = make_profile(area=7.0, centroid_x=4.0, centroid_y=4.0)  # distance ~5.66 > 5.0

        candidates = [(profile1, 5.0), (profile2, 6.0), (profile3, 7.0)]

        result = _filter_by_centroid(candidates, circle_center, circle_radius)

        assert len(result) == 2
        assert profile1 in [p for p, _, _ in result]
        assert profile2 in [p for p, _, _ in result]
        assert profile3 not in [p for p, _, _ in result]


class TestFilterByBoundingBox:
    """Test _filter_by_bounding_box function."""

    def test_bbox_within_circle_bounds(self):
        """Bbox entirely within circle bounds should be included."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 10.0

        # Margin: circle_radius * 1.0 = 10.0
        # Bounds: [center ± 2*radius] = [-20, 20]
        profile = make_profile(
            area=10.0,
            bbox_min_x=-5.0, bbox_min_y=-5.0,
            bbox_max_x=5.0, bbox_max_y=5.0
        )
        candidates = [(profile, 10.0, 1.0)]

        result = _filter_by_bounding_box(candidates, circle_center, circle_radius)

        assert len(result) == 1

    def test_bbox_outside_left_boundary(self):
        """Bbox extending past left boundary should be excluded."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 10.0

        # Min bound: center.x - 2*radius = -20.0
        profile = make_profile(
            area=10.0,
            bbox_min_x=-21.0, bbox_min_y=-5.0,
            bbox_max_x=5.0, bbox_max_y=5.0
        )
        candidates = [(profile, 10.0, 1.0)]

        result = _filter_by_bounding_box(candidates, circle_center, circle_radius)

        assert len(result) == 0

    def test_bbox_outside_right_boundary(self):
        """Bbox extending past right boundary should be excluded."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 10.0

        # Max bound: center.x + 2*radius = 20.0
        profile = make_profile(
            area=10.0,
            bbox_min_x=-5.0, bbox_min_y=-5.0,
            bbox_max_x=21.0, bbox_max_y=5.0
        )
        candidates = [(profile, 10.0, 1.0)]

        result = _filter_by_bounding_box(candidates, circle_center, circle_radius)

        assert len(result) == 0

    def test_bbox_outside_top_boundary(self):
        """Bbox extending past top boundary should be excluded."""
        circle_center = make_point(0.0, 0.0, 0.0)
        circle_radius = 10.0

        profile = make_profile(
            area=10.0,
            bbox_min_x=-5.0, bbox_min_y=-5.0,
            bbox_max_x=5.0, bbox_max_y=21.0
        )
        candidates = [(profile, 10.0, 1.0)]

        result = _filter_by_bounding_box(candidates, circle_center, circle_radius)

        assert len(result) == 0


class TestAccumulateProfiles:
    """Test _accumulate_profiles function."""

    def test_single_profile_exact_match(self):
        """Single profile with exact area match should be selected."""
        target_area = 10.0
        profile = make_profile(area=10.0)
        candidates = [(profile, 10.0, 1.0)]

        profiles, difference = _accumulate_profiles(candidates, target_area)

        assert len(profiles) == 1
        assert profiles[0] == profile
        assert difference == pytest.approx(0.0, abs=1e-9)

    def test_two_profiles_sum_to_target(self):
        """Two profiles summing to target should be selected."""
        target_area = 10.0
        profile1 = make_profile(area=4.0)
        profile2 = make_profile(area=6.0)
        candidates = [
            (profile1, 4.0, 1.0),
            (profile2, 6.0, 1.0)
        ]

        profiles, difference = _accumulate_profiles(candidates, target_area)

        assert len(profiles) == 2
        assert difference == pytest.approx(0.0, abs=1e-9)

    def test_no_perfect_match(self):
        """Returns best combination even if not perfect match."""
        target_area = 10.0
        profile1 = make_profile(area=3.5)
        profile2 = make_profile(area=3.7)
        candidates = [
            (profile1, 3.5, 1.0),
            (profile2, 3.7, 1.0)
        ]

        profiles, difference = _accumulate_profiles(candidates, target_area)

        # Best combination is both: 3.5 + 3.7 = 7.2, diff = 2.8
        assert len(profiles) == 2
        assert difference == pytest.approx(2.8, abs=1e-9)

    def test_early_exit_on_very_close_match(self):
        """Should exit early if difference <= target * 0.00003."""
        target_area = 100.0
        # Threshold: 100.0 * 0.00003 = 0.003
        profile = make_profile(area=100.001)
        candidates = [(profile, 100.001, 1.0)]

        profiles, difference = _accumulate_profiles(candidates, target_area)

        assert len(profiles) == 1
        assert difference <= target_area * 0.00003

    def test_empty_candidates(self):
        """Empty candidates should return None and inf."""
        target_area = 10.0
        candidates = []

        profiles, difference = _accumulate_profiles(candidates, target_area)

        assert profiles is None
        assert difference == pytest.approx(float('inf'))

    def test_max_15_profiles_limit(self):
        """Should not exceed 15 profiles in a combination."""
        target_area = 15.0
        # Create 20 profiles with area 1.0 each
        candidates = [
            (make_profile(area=1.0), 1.0, float(i))
            for i in range(20)
        ]

        profiles, difference = _accumulate_profiles(candidates, target_area)

        # Should select at most 15 profiles
        assert len(profiles) <= 15

    def test_sorts_by_area_descending(self):
        """Should consider profiles in descending area order."""
        target_area = 10.0
        # Create profiles in increasing order
        profile1 = make_profile(area=2.0)
        profile2 = make_profile(area=4.0)
        profile3 = make_profile(area=6.0)

        candidates = [
            (profile1, 2.0, 1.0),
            (profile2, 4.0, 1.0),
            (profile3, 6.0, 1.0)
        ]

        profiles, difference = _accumulate_profiles(candidates, target_area)

        # Best match: 6.0 + 4.0 = 10.0 (exact)
        assert len(profiles) == 2
        assert profile2 in profiles
        assert profile3 in profiles
