"""
Debug export utility for ThreadMeister.

Exports sketch and circle data to JSON for fixture-based testing.
Run from Fusion 360 to capture real profile data at both accuracy levels.

Dual output mode: logs progress to Fusion console AND writes JSON file.
"""

import json
import os
import time
import math
import adsk.core
import adsk.fusion
from tm_geometry import findProfileForCircle
from tm_helpers import log, clear_log


def export_sketch_data(sketch, target_circle, output_dir, description=""):
    """
    Export sketch profiles and target circle to JSON fixture.

    Dual output mode:
    - Console: [EXPORT] progress messages to Fusion TextCommands
    - File: JSON fixture to debug_exports/

    Args:
        sketch: Fusion Sketch object
        target_circle: Fusion SketchCircle object (the target bore)
        output_dir: Directory path for output JSON file
        description: Optional description for the fixture

    Returns:
        str: Path to created JSON file
    """
    try:
        clear_log()
        log(f"[EXPORT] Starting: {description}")

        # Compute accuracies for dual-level export
        low_accuracy = adsk.fusion.CalculationAccuracy.LowCalculationAccuracy
        high_accuracy = adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy

        # Export target circle data
        circle_center = target_circle.centerSketchPoint.geometry
        circle_data = {
            "center_xy": [circle_center.x, circle_center.y],
            "radius_cm": target_circle.radius,
            "area_low": _compute_circle_area(target_circle.radius),
            "area_high": _compute_circle_area(target_circle.radius),
        }

        log(f"[EXPORT] Target circle: center=({circle_center.x:.4f}, {circle_center.y:.4f}), radius={target_circle.radius:.4f}")

        # Export profile data
        profiles_data = []
        profiles_list = list(sketch.profiles)
        log(f"[EXPORT] Profiles found: {len(profiles_list)}")

        for i, profile in enumerate(profiles_list):
            try:
                # Get area properties at both accuracies
                props_low = profile.areaProperties(low_accuracy)
                props_high = profile.areaProperties(high_accuracy)

                # Extract centroid coordinates
                centroid_low = props_low.centroid
                centroid_high = props_high.centroid

                profile_entry = {
                    "index": i,
                    "area_low_accuracy": props_low.area,
                    "area_high_accuracy": props_high.area,
                    "centroid_low_xy": [centroid_low.x, centroid_low.y],
                    "centroid_high_xy": [centroid_high.x, centroid_high.y],
                    "bbox": {
                        "min_xy": [
                            profile.boundingBox.minPoint.x,
                            profile.boundingBox.minPoint.y
                        ],
                        "max_xy": [
                            profile.boundingBox.maxPoint.x,
                            profile.boundingBox.maxPoint.y
                        ]
                    }
                }
                profiles_data.append(profile_entry)
                log(f"[EXPORT] Profile {i}: area_low={props_low.area:.6f}, area_high={props_high.area:.6f}")

            except Exception as e:
                log(f"[EXPORT] Profile {i}: Error reading properties: {e}")

        # Run findProfileForCircle to get ground truth
        log(f"[EXPORT] Running profile selection algorithm...")
        result = findProfileForCircle(sketch, target_circle)
        expected_indices = _extract_profile_indices(result, sketch)
        log(f"[EXPORT] Algorithm result: selected profiles {expected_indices}")

        # Build complete fixture JSON
        fixture_data = {
            "description": description,
            "target_circle": circle_data,
            "profiles": profiles_data,
            "expected_result": expected_indices
        }

        # Write to file with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(fixture_data, f, indent=2)

        log(f"[EXPORT] Saved: {filename}")
        log(f"[EXPORT] Done. Profiles: {len(profiles_data)}, Selected: {len(expected_indices)}")

        return filepath

    except Exception as e:
        log(f"[EXPORT] FAILED: {str(e)}")
        raise


def _compute_circle_area(radius_cm):
    """Compute circle area from radius in cm."""
    return math.pi * (radius_cm ** 2)


def _extract_profile_indices(result, sketch):
    """
    Extract profile indices from findProfileForCircle result.

    Result can be:
    - Single profile object → [index]
    - ObjectCollection → [indices...]
    - None → []
    """
    if result is None:
        return []

    profiles_list = list(sketch.profiles)

    if isinstance(result, adsk.core.ObjectCollection):
        indices = []
        for item in result:
            try:
                idx = profiles_list.index(item)
                indices.append(idx)
            except ValueError:
                pass
        return sorted(indices)
    else:
        # Single profile
        try:
            idx = profiles_list.index(result)
            return [idx]
        except ValueError:
            return []
