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


def _debug_log(msg):
    """Write directly to Fusion console (for debug export, independent of enable_logging flag)."""
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        p = ui.palettes.itemById('TextCommands')
        if not p.isVisible:
            p.isVisible = True
        p.writeText(str(msg))
    except Exception:
        pass


def _clear_debug_log():
    """Clear console for debug export."""
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        p = ui.palettes.itemById('TextCommands')
        if p:
            for _ in range(50):
                p.writeText('')
            if not p.isVisible:
                p.isVisible = True
    except Exception:
        pass


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
        _clear_debug_log()
        _debug_log(f"[EXPORT] Starting: {description}")
        sketch_token_set = _build_sketch_token_set(sketch)
        _debug_log(f"[EXPORT] Sketch has {len(sketch_token_set)} real sketch curves")

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

        _debug_log(f"[EXPORT] Target circle: center=({circle_center.x:.4f}, {circle_center.y:.4f}), radius={target_circle.radius:.4f}")

        # Export profile data
        profiles_data = []
        profiles_list = list(sketch.profiles)
        _debug_log(f"[EXPORT] Profiles found: {len(profiles_list)}")

        for i, profile in enumerate(profiles_list):
            try:
                # Get area properties at both accuracies
                props_low = profile.areaProperties(low_accuracy)
                props_high = profile.areaProperties(high_accuracy)

                # Extract centroid coordinates
                centroid_low = props_low.centroid
                centroid_high = props_high.centroid

                # Export profile loops and curves
                loops_data = _serialize_profile_loops(profile, sketch_token_set)

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
                    },
                    "loops": loops_data
                }
                profiles_data.append(profile_entry)
                _debug_log(f"[EXPORT] Profile {i}: area_low={props_low.area:.6f}, area_high={props_high.area:.6f}, loops={len(loops_data)}")

            except Exception as e:
                _debug_log(f"[EXPORT] Profile {i}: Error reading properties: {e}")

        # Run findProfileForCircle to get ground truth
        _debug_log(f"[EXPORT] Running profile selection algorithm...")
        result = findProfileForCircle(sketch, target_circle)
        expected_indices = _extract_profile_indices(result, sketch)
        _debug_log(f"[EXPORT] Algorithm result: selected profiles {expected_indices}")

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

        _debug_log(f"[EXPORT] Saved: {filename}")
        _debug_log(f"[EXPORT] Done. Profiles: {len(profiles_data)}, Selected: {len(expected_indices)}")

        return filepath

    except Exception as e:
        _debug_log(f"[EXPORT] FAILED: {str(e)}")
        raise


def _extract_ellipse_params(sketch_entity, type_name):
    """Extract major/minor axis lengths and rotation from an ellipse or elliptical arc entity.

    Note: majorAxis/minorAxis are Vector3D (direction), not scalars.
          majorAxisRadius/minorAxisRadius are the scalar half-lengths.
    """
    major_len = None
    minor_len = None
    rotation = 0

    # Try scalar radius properties first (correct), then fallback candidates
    for attr in ('majorAxisRadius', 'majorAxisLength'):
        if hasattr(sketch_entity, attr):
            val = getattr(sketch_entity, attr)
            if isinstance(val, (int, float)):
                major_len = val
                _debug_log(f"[EXPORT] {type_name}: {attr} = {major_len}")
                break
            else:
                _debug_log(f"[EXPORT] {type_name}: {attr} returned non-scalar {type(val).__name__}, skipping")

    for attr in ('minorAxisRadius', 'minorAxisLength'):
        if hasattr(sketch_entity, attr):
            val = getattr(sketch_entity, attr)
            if isinstance(val, (int, float)):
                minor_len = val
                _debug_log(f"[EXPORT] {type_name}: {attr} = {minor_len}")
                break
            else:
                _debug_log(f"[EXPORT] {type_name}: {attr} returned non-scalar {type(val).__name__}, skipping")

    # Rotation is encoded in the majorAxis Vector3D direction, not a scalar property
    if hasattr(sketch_entity, 'majorAxis'):
        ma = sketch_entity.majorAxis
        if hasattr(ma, 'x') and hasattr(ma, 'y'):
            rotation = math.atan2(ma.y, ma.x)
            _debug_log(f"[EXPORT] {type_name}: majorAxis=({ma.x:.4f},{ma.y:.4f}), rotation={math.degrees(rotation):.1f}°")
        else:
            _debug_log(f"[EXPORT] {type_name}: majorAxis has no x/y, rotation stays 0")

    return major_len, minor_len, rotation


def _serialize_curve(curve_index, sketch_curve, sketch_token_set=None):
    """
    Serialize a single SketchCurve (SketchLine, SketchArc, SketchCircle, etc).

    Args:
        curve_index: Integer index within the loop
        sketch_curve: The SketchCurve object
        sketch_token_set: set of entityTokens from real sketch curves.
            If provided, curves absent from this set are flagged as boundary-derived.

    Returns:
        dict with curve data, or None if curve type is unsupported (e.g., Spline)
    """
    try:
        sketch_entity = sketch_curve.sketchEntity

        # Sanity check: skip invalid entities
        if hasattr(sketch_entity, 'isValid') and not sketch_entity.isValid:
            _debug_log(f"[EXPORT] Curve {curve_index}: sketchEntity is INVALID, skipping")
            return None

        is_construction = sketch_entity.isConstruction
        is_reference = bool(getattr(sketch_entity, 'isReference', False))
        entity_type = type(sketch_entity).__name__

        # Capture entity token and check against real sketch curves
        entity_token = getattr(sketch_entity, 'entityToken', None)
        is_boundary_derived = (
            sketch_token_set is not None and
            entity_token is not None and
            entity_token not in sketch_token_set
        )
        if is_reference:
            _debug_log(f"[EXPORT] Curve {curve_index}: REFERENCE/PROJECTED curve (type={entity_type}), flagging")
        elif is_boundary_derived:
            _debug_log(f"[EXPORT] Curve {curve_index}: BOUNDARY-DERIVED (type={entity_type}, not in sketch.sketchCurves)")
        else:
            _debug_log(f"[EXPORT] Curve {curve_index}: type={entity_type}, token={entity_token or 'N/A'}")

        if isinstance(sketch_entity, adsk.fusion.SketchLine):
            start_pt = sketch_entity.startSketchPoint.geometry
            end_pt = sketch_entity.endSketchPoint.geometry
            return {
                "curve_index": curve_index,
                "type": "SketchLine",
                "is_construction": is_construction,
                "is_reference": is_reference,
                "is_boundary_derived": is_boundary_derived,
                "entity_token": entity_token,
                "start_xy": [start_pt.x, start_pt.y],
                "end_xy": [end_pt.x, end_pt.y]
            }

        elif isinstance(sketch_entity, adsk.fusion.SketchArc):
            center_pt = sketch_entity.centerSketchPoint.geometry
            start_pt = sketch_entity.startSketchPoint.geometry
            end_pt = sketch_entity.endSketchPoint.geometry
            return {
                "curve_index": curve_index,
                "type": "SketchArc",
                "is_construction": is_construction,
                "is_reference": is_reference,
                "is_boundary_derived": is_boundary_derived,
                "entity_token": entity_token,
                "center_xy": [center_pt.x, center_pt.y],
                "radius": sketch_entity.radius,
                "start_xy": [start_pt.x, start_pt.y],
                "end_xy": [end_pt.x, end_pt.y]
            }

        elif isinstance(sketch_entity, adsk.fusion.SketchCircle):
            center_pt = sketch_entity.centerSketchPoint.geometry
            return {
                "curve_index": curve_index,
                "type": "SketchCircle",
                "is_construction": is_construction,
                "is_reference": is_reference,
                "is_boundary_derived": is_boundary_derived,
                "entity_token": entity_token,
                "center_xy": [center_pt.x, center_pt.y],
                "radius": sketch_entity.radius
            }

        elif isinstance(sketch_entity, adsk.fusion.SketchEllipticalArc):
            center_pt = sketch_entity.centerSketchPoint.geometry
            start_pt = sketch_entity.startSketchPoint.geometry
            end_pt = sketch_entity.endSketchPoint.geometry

            major_len, minor_len, rotation = _extract_ellipse_params(sketch_entity, "SketchEllipticalArc")

            return {
                "curve_index": curve_index,
                "type": "SketchEllipticalArc",
                "is_construction": is_construction,
                "is_reference": is_reference,
                "is_boundary_derived": is_boundary_derived,
                "entity_token": entity_token,
                "center_xy": [center_pt.x, center_pt.y],
                "start_xy": [start_pt.x, start_pt.y],
                "end_xy": [end_pt.x, end_pt.y],
                "major_axis_length": major_len if major_len else 0,
                "minor_axis_length": minor_len if minor_len else 0,
                "rotation_angle": rotation
            }

        elif isinstance(sketch_entity, adsk.fusion.SketchEllipse):
            center_pt = sketch_entity.centerSketchPoint.geometry

            major_len, minor_len, rotation = _extract_ellipse_params(sketch_entity, "SketchEllipse")

            return {
                "curve_index": curve_index,
                "type": "SketchEllipse",
                "is_construction": is_construction,
                "is_reference": is_reference,
                "is_boundary_derived": is_boundary_derived,
                "entity_token": entity_token,
                "center_xy": [center_pt.x, center_pt.y],
                "major_axis_length": major_len if major_len else 0,
                "minor_axis_length": minor_len if minor_len else 0,
                "rotation_angle": rotation
            }

        else:
            # Unsupported type (Spline, etc.) — return None to skip
            _debug_log(f"[EXPORT] Skipped unsupported curve type: {entity_type} (construction={is_construction})")
            return None

    except Exception as e:
        # Skip curves that fail to serialize
        _debug_log(f"[EXPORT] Error serializing curve: {e}")
        return None


def _build_sketch_token_set(sketch):
    """
    Build a set of entityTokens for all curves actually drawn in the sketch.

    Fusion profiles can include boundary-derived curves from the underlying solid
    that are NOT real sketch entities. Comparing against this set lets us flag
    those phantom curves.
    """
    tokens = set()
    try:
        for sc in sketch.sketchCurves:
            token = getattr(sc, 'entityToken', None)
            if token:
                tokens.add(token)
    except Exception as e:
        _debug_log(f"[EXPORT] Warning: could not build sketch token set: {e}")
    return tokens


def _serialize_profile_loops(profile, sketch_token_set=None):
    """
    Serialize all loops and curves in a profile.

    Args:
        profile: Fusion Profile object
        sketch_token_set: set of entityTokens from real sketch curves (optional).
            If provided, curves whose token is absent are flagged as boundary-derived.

    Returns:
        list of loop dicts, each containing a list of curve dicts
    """
    loops_data = []
    try:
        for loop_idx, loop in enumerate(profile.profileLoops):
            curves_data = []
            curve_count = 0
            try:
                for curve_idx, profile_curve in enumerate(loop.profileCurves):
                    curve_count += 1
                    curve_dict = _serialize_curve(curve_idx, profile_curve, sketch_token_set)
                    if curve_dict is not None:  # Skip unsupported curve types
                        curves_data.append(curve_dict)
                    else:
                        _debug_log(f"[EXPORT] Loop {loop_idx}: Curve {curve_idx} skipped (unsupported type)")

                _debug_log(f"[EXPORT] Loop {loop_idx}: {curve_count} curves found, {len(curves_data)} serialized")

                # Detect shared entity tokens (Fusion splitting one sketch entity into multiple segments)
                has_weird_split = False
                token_groups = {}
                for cd in curves_data:
                    token = cd.get("entity_token")
                    if token is not None:
                        token_groups.setdefault(token, []).append(cd)

                shared = {t: cds for t, cds in token_groups.items() if len(cds) > 1}
                if shared:
                    has_weird_split = True
                    for token, cds in shared.items():
                        types_str = ", ".join(cd["type"] for cd in cds)
                        indices_str = ", ".join(str(cd["curve_index"]) for cd in cds)
                        _debug_log(
                            f"[EXPORT] Loop {loop_idx}: WEIRD SPLIT detected! "
                            f"Token ...{token[-20:]} shared by curves [{indices_str}] "
                            f"as types [{types_str}]"
                        )

            except Exception as e:
                has_weird_split = False
                _debug_log(f"[EXPORT] Loop {loop_idx}: Error iterating curves: {e}")

            if curves_data:  # Only add loop if it has valid curves
                loops_data.append({
                    "loop_index": loop_idx,
                    "has_weird_split": has_weird_split,
                    "curves": curves_data
                })
    except Exception as e:
        _debug_log(f"[EXPORT] Error reading profile loops: {e}")

    return loops_data


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
