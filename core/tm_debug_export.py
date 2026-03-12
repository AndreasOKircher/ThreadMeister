"""
Debug export utility for ThreadMeister.

Exports sketch and circle data to JSON for fixture-based testing.
Run from Fusion 360 to capture real profile data at both accuracy levels.
"""

import json
import os
import time
import adsk.core
import adsk.fusion
from tm_geometry import findProfileForCircle


def export_sketch_data(sketch, target_circle, output_dir, description=""):
    """
    Export sketch profiles and target circle to JSON fixture.

    Interactive workflow:
    1. Highlight each profile in Fusion UI (user verifies visually)
    2. Run findProfileForCircle to get ground truth result
    3. Write JSON with both profile data and expected result

    Args:
        sketch: Fusion Sketch object
        target_circle: Fusion SketchCircle object (the target bore)
        output_dir: Directory path for output JSON file
        description: Optional description for the fixture

    Returns:
        str: Path to created JSON file
    """
    try:
        ui = adsk.core.Application.get().userInterface

        # Compute accuracies for dual-level export
        low_accuracy = adsk.fusion.CalculationAccuracy.LowCalculationAccuracy
        high_accuracy = adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy

        # Export target circle data
        circle_center = target_circle.centerSketchPoint.geometry
        circle_data = {
            "center_xy": [circle_center.x, circle_center.y],
            "radius_cm": target_circle.radius,
            "area_low": _compute_circle_area(target_circle.radius, "low"),
            "area_high": _compute_circle_area(target_circle.radius, "high"),
        }

        # Export profile data
        profiles_data = []
        for i, profile in enumerate(sketch.profiles):
            # Get area properties at both accuracies
            props_low = profile.areaProperties(low_accuracy)
            props_high = profile.areaProperties(high_accuracy)

            # Highlight profile and pause
            ui.messageBox(
                f"Profile {i}: {props_low.area:.4f} cm²\n"
                f"High accuracy: {props_high.area:.6f} cm²\n\n"
                f"This profile is highlighted. Verify it's relevant.\n"
                f"Click OK to continue.",
                "ThreadMeister Export — Profile Review"
            )

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

        # Run findProfileForCircle to get ground truth
        result = findProfileForCircle(sketch, target_circle)
        expected_indices = _extract_profile_indices(result, sketch)

        # Build complete fixture JSON
        fixture_data = {
            "description": description,
            "target_circle": circle_data,
            "profiles": profiles_data,
            "expected_result": expected_indices
        }

        # Write to file with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"fixture_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(fixture_data, f, indent=2)

        ui.messageBox(
            f"Export complete!\n\nFile: {filename}\n\nProfiles: {len(profiles_data)}\n"
            f"Selected: {len(expected_indices)}",
            "ThreadMeister Export — Success"
        )

        return filepath

    except Exception as e:
        try:
            ui.messageBox(f"Export failed: {str(e)}", "ThreadMeister Export — Error")
        except:
            pass
        raise


def _compute_circle_area(radius_cm, accuracy="high"):
    """Compute circle area from radius. Placeholder for future accuracy variations."""
    import math
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
