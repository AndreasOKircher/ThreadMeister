"""
Fixture-based integration tests for profile selection algorithm.

Tests load JSON fixture files from fixtures/ directory and verify
that findProfileForCircle() produces expected results.

These tests use reconstructed mock Fusion objects based on exported
real sketch data.
"""

import pytest
import json
import os
import math
import glob
from unittest.mock import MagicMock
from types import SimpleNamespace

import tm_geometry


# ===== Helper Functions =====

def make_point(x, y, z=0.0):
    """Create a mock 3D point with x, y, z and distanceTo method."""
    point = SimpleNamespace(x=x, y=y, z=z)

    def distance_to(other):
        return math.sqrt(
            (point.x - other.x)**2 +
            (point.y - other.y)**2 +
            (point.z - other.z)**2
        )

    point.distanceTo = distance_to
    return point


def make_profile_from_fixture_data(profile_data):
    """
    Reconstruct a mock profile from fixture JSON data.

    Args:
        profile_data: dict with area_low_accuracy, centroid_low_xy, bbox, etc.

    Returns:
        Mock profile object compatible with tm_geometry functions
    """
    profile = MagicMock()

    # Area properties (use low accuracy as default)
    area_props = MagicMock()
    area_props.area = profile_data['area_low_accuracy']
    area_props.centroid = make_point(
        profile_data['centroid_low_xy'][0],
        profile_data['centroid_low_xy'][1]
    )
    profile.areaProperties.return_value = area_props

    # Bounding box
    bbox_min = make_point(
        profile_data['bbox']['min_xy'][0],
        profile_data['bbox']['min_xy'][1]
    )
    bbox_max = make_point(
        profile_data['bbox']['max_xy'][0],
        profile_data['bbox']['max_xy'][1]
    )

    profile.boundingBox = MagicMock()
    profile.boundingBox.minPoint = bbox_min
    profile.boundingBox.maxPoint = bbox_max

    return profile


def load_fixture_file(filepath):
    """Load and parse a fixture JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_fixture_files():
    """Collect all fixture JSON files from fixtures/ directory."""
    base_dir = os.path.dirname(os.path.dirname(__file__))  # project root
    fixtures_dir = os.path.join(base_dir, 'fixtures')

    if not os.path.exists(fixtures_dir):
        return []

    return sorted(glob.glob(os.path.join(fixtures_dir, '*.json')))


# ===== Fixtures =====

@pytest.fixture(params=get_fixture_files(), ids=lambda p: os.path.basename(p))
def fixture_data(request):
    """Parametrized fixture that loads each JSON file from fixtures/."""
    return load_fixture_file(request.param)


# ===== Tests =====

class TestProfileSelection:
    """Test profile selection against fixture data."""

    def test_simple_fixture_loads(self, fixture_data):
        """Verify fixture JSON structure is valid."""
        assert 'target_circle' in fixture_data
        assert 'profiles' in fixture_data
        assert 'expected_result' in fixture_data
        assert isinstance(fixture_data['profiles'], list)
        assert isinstance(fixture_data['expected_result'], list)

    @pytest.mark.xfail(reason="Stub fixtures - awaiting real data from Fusion 360 export")
    def test_profile_selection_matches_expected(self, fixture_data):
        """
        Test that findProfileForCircle matches the expected result.

        Reconstructs mock Fusion objects from fixture data and compares
        the algorithm output to the ground truth captured during export.

        NOTE: Fails on stub fixtures. Will pass once real fixtures are created
        in Fusion 360 using tm_debug_export.py.
        """
        # Reconstruct mock sketch and target circle from fixture
        circle_data = fixture_data['target_circle']
        profiles_data = fixture_data['profiles']

        # Create mock target circle
        target_circle = MagicMock()
        target_circle.centerSketchPoint = MagicMock()
        target_circle.centerSketchPoint.geometry = make_point(
            circle_data['center_xy'][0],
            circle_data['center_xy'][1]
        )
        target_circle.radius = circle_data['radius_cm']
        target_circle.area = circle_data['area_low']
        target_circle.parentSketch = MagicMock()

        # Create mock profiles
        mock_profiles = [
            make_profile_from_fixture_data(pd)
            for pd in profiles_data
        ]

        # Create mock sketch
        sketch = MagicMock()
        sketch.profiles = mock_profiles
        target_circle.parentSketch = sketch

        # Run the algorithm
        result = tm_geometry.findProfileForCircle(sketch, target_circle)

        # Extract result indices
        result_indices = _extract_result_indices(result, mock_profiles)

        # Compare to expected
        expected_indices = fixture_data['expected_result']
        assert sorted(result_indices) == sorted(expected_indices), \
            f"Expected {expected_indices}, got {result_indices}"

    def test_profile_areas_exported(self, fixture_data):
        """Verify that profile areas are exported at both accuracy levels."""
        for profile in fixture_data['profiles']:
            assert 'area_low_accuracy' in profile
            assert 'area_high_accuracy' in profile
            assert profile['area_low_accuracy'] > 0
            assert profile['area_high_accuracy'] > 0

    def test_centroids_exported(self, fixture_data):
        """Verify that centroids are exported for all profiles."""
        for profile in fixture_data['profiles']:
            assert 'centroid_low_xy' in profile
            assert 'centroid_high_xy' in profile
            assert len(profile['centroid_low_xy']) == 2
            assert len(profile['centroid_high_xy']) == 2

    def test_bounding_boxes_exported(self, fixture_data):
        """Verify that bounding boxes are exported."""
        for profile in fixture_data['profiles']:
            assert 'bbox' in profile
            assert 'min_xy' in profile['bbox']
            assert 'max_xy' in profile['bbox']


class TestSpecialCases:
    """Test special and edge cases."""

    def test_empty_profile_list(self):
        """Test with no profiles."""
        sketch = MagicMock()
        sketch.profiles = []

        target_circle = MagicMock()
        target_circle.centerSketchPoint = MagicMock()
        target_circle.centerSketchPoint.geometry = make_point(0, 0)
        target_circle.radius = 0.5
        target_circle.area = math.pi * (0.5 ** 2)
        target_circle.parentSketch = sketch

        result = tm_geometry.findProfileForCircle(sketch, target_circle)

        # Should handle gracefully (return None or empty collection)
        assert result is None or (hasattr(result, '__len__') and len(result) == 0)


# ===== Helper Functions =====

def _extract_result_indices(result, profiles):
    """
    Extract profile indices from algorithm result.

    Result can be:
    - None → []
    - Single profile object → [index]
    - ObjectCollection → [indices...]
    """
    if result is None:
        return []

    # Check if it's an ObjectCollection
    if hasattr(result, '__iter__') and not isinstance(result, str):
        indices = []
        for item in result:
            try:
                idx = profiles.index(item)
                indices.append(idx)
            except ValueError:
                pass
        return indices
    else:
        # Single profile
        try:
            idx = profiles.index(result)
            return [idx]
        except ValueError:
            return []
