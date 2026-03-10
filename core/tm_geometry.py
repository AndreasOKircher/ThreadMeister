"""
tm_geometry.py – All geometry functions: profile finding, extrusion direction,
chamfer, fillet, and through-body distance.
"""
import adsk.core, adsk.fusion, traceback
import math
from itertools import combinations
import tm_state
from tm_helpers import log


def _filter_by_area(sketch, target_area):
    """
    Coarse area filter: select profiles whose area <= target_area * 1.01.

    Returns:
        List of (profile, area) tuples passing the area filter.
    """
    candidates = []
    for idx, prof in enumerate(sketch.profiles):
        props = prof.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy)
        if props.area <= target_area * 1.01:
            log(f"Profile {idx}: area filter PASS - area={props.area:.6f}")
            candidates.append((prof, props.area))
        else:
            log(f"Profile {idx}: area filter REJECT - area {props.area:.6f} > {target_area * 1.01:.6f}")
    return candidates


def _filter_by_centroid(candidates, circle_center3d, circle_radius):
    """
    Coarse centroid filter: check if profile centroid is inside target circle.

    Args:
        candidates: List of (profile, area) tuples from area filter
        circle_center3d: 3D center point of target circle
        circle_radius: Radius of target circle

    Returns:
        List of (profile, area, centroid_distance) tuples passing centroid filter.
    """
    filtered = []
    idx = 0
    for prof, area in candidates:
        props = prof.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy)
        centroid3d = props.centroid
        distance = circle_center3d.distanceTo(centroid3d)

        if distance <= circle_radius:
            log(f"Profile {idx}: centroid filter PASS - dist={distance:.6f}")
            filtered.append((prof, area, distance))
        else:
            log(f"Profile {idx}: centroid filter REJECT - dist {distance:.6f} > radius {circle_radius:.6f}")
        idx += 1
    return filtered


def _filter_by_bounding_box(candidates, circle_center3d, circle_radius):
    """
    Coarse bounding box filter: check if profile bbox fits in generous circle area.

    Args:
        candidates: List of (profile, area, distance) tuples from centroid filter
        circle_center3d: 3D center point of target circle
        circle_radius: Radius of target circle

    Returns:
        List of (profile, area, distance) tuples passing bbox filter.
    """
    bbox_margin = circle_radius * 1.0
    circle_bbox_min_x = circle_center3d.x - circle_radius - bbox_margin
    circle_bbox_max_x = circle_center3d.x + circle_radius + bbox_margin
    circle_bbox_min_y = circle_center3d.y - circle_radius - bbox_margin
    circle_bbox_max_y = circle_center3d.y + circle_radius + bbox_margin

    log(f"BBox margins: x=[{circle_bbox_min_x:.4f}, {circle_bbox_max_x:.4f}], y=[{circle_bbox_min_y:.4f}, {circle_bbox_max_y:.4f}]")

    filtered = []
    idx = 0
    for prof, area, distance in candidates:
        prof_bbox = prof.boundingBox
        is_contained = (
            prof_bbox.minPoint.x >= circle_bbox_min_x and
            prof_bbox.maxPoint.x <= circle_bbox_max_x and
            prof_bbox.minPoint.y >= circle_bbox_min_y and
            prof_bbox.maxPoint.y <= circle_bbox_max_y
        )

        if is_contained:
            log(f"Profile {idx}: bbox filter PASS")
            filtered.append((prof, area, distance))
        else:
            log(f"Profile {idx}: bbox filter REJECT - bbox outside margins")
            log(f"  Profile bbox: ({prof_bbox.minPoint.x:.4f}, {prof_bbox.minPoint.y:.4f}) to ({prof_bbox.maxPoint.x:.4f}, {prof_bbox.maxPoint.y:.4f})")
        idx += 1
    return filtered


def _accumulate_profiles(candidates, target_area):
    """
    Precise area matching: find profile combination with area closest to target.
    Uses combinatorial search with 15-profile cap.

    Args:
        candidates: List of (profile, area, distance) tuples from bbox filter
        target_area: Target circle area

    Returns:
        (best_profiles, best_difference) tuple, or (None, inf) if no match.
    """
    candidates.sort(key=lambda x: x[1], reverse=True)

    best_profiles = None
    best_difference = float('inf')
    max_profiles = min(len(candidates), 15)

    log(f"Starting combination search (max {max_profiles} profiles)...")

    for r in range(1, max_profiles + 1):
        combinations_tried = 0
        for combo in combinations(candidates, r):
            combo_area = sum(item[1] for item in combo)
            difference = abs(combo_area - target_area)
            combinations_tried += 1

            if difference < best_difference:
                best_difference = difference
                best_profiles = [item[0] for item in combo]
                log(f"  New best: {r} profiles, area={combo_area:.6f}, diff={difference:.6f}")

            # Early exit for near-perfect match
            if best_difference <= target_area * 0.00003:
                log(f"  Found near-perfect match! Stopping early.")
                break

        log(f"  Tried {combinations_tried} combinations of size {r}")

        if best_difference <= target_area * 0.00003:
            break

    return best_profiles, best_difference


def findProfileForCircle(sketch, target_circle):
    """
    Find all profiles that make up the area inside the target circle.

    Strategy:
    1. Coarse filters to reduce candidates (fast, permissive)
       - Area: not larger than circle
       - Centroid: inside circle
       - BBox: roughly within circle area (generous margin)
    2. Precise area-matching to find exact combination (slow, accurate)

    Returns:
        Profile, ObjectCollection of profiles, or None if validation fails.
    """
    if target_circle.parentSketch != sketch:
        log("findProfileForCircle: target_circle is not in given sketch")
        return None

    circle_center3d = target_circle.centerSketchPoint.geometry
    circle_radius = target_circle.radius
    target_area = target_circle.area

    log("=== findProfileForCircle START ===")
    log(f"Circle: center ({circle_center3d.x:.4f}, {circle_center3d.y:.4f}), radius={circle_radius:.6f}, area={target_area:.6f}")
    log(f"Total profiles in sketch: {sketch.profiles.count}")

    # Apply filters in sequence
    candidates_after_area = _filter_by_area(sketch, target_area)
    if not candidates_after_area:
        log("No candidates after area filter")
        log("=== findProfileForCircle END (no candidates) ===")
        return None

    candidates_after_centroid = _filter_by_centroid(candidates_after_area, circle_center3d, circle_radius)
    if not candidates_after_centroid:
        log("No candidates after centroid filter")
        log("=== findProfileForCircle END (no candidates) ===")
        return None

    candidates_after_bbox = _filter_by_bounding_box(candidates_after_centroid, circle_center3d, circle_radius)
    if not candidates_after_bbox:
        log("No candidates after bbox filter")
        log("=== findProfileForCircle END (no candidates) ===")
        return None

    log(f"Total candidates after all filters: {len(candidates_after_bbox)}")

    # Precise area matching
    best_profiles, best_difference = _accumulate_profiles(candidates_after_bbox, target_area)

    tolerance = target_area * 0.03
    log(f"Best match: {len(best_profiles)} profiles, area diff={best_difference:.6f}, tolerance={tolerance:.6f}")

    if best_difference > tolerance:
        log("No valid combination found within tolerance")
        log("=== findProfileForCircle END (no valid combination) ===")
        return None

    log(f"SUCCESS: Returning {len(best_profiles)} profile(s)")
    log("=== findProfileForCircle END (success) ===")

    if len(best_profiles) == 1:
        return best_profiles[0]

    coll = adsk.core.ObjectCollection.create()
    for prof in best_profiles:
        coll.add(prof)
    return coll


def findExtrudeDirectionFromSketch(sketch, circleCenter, targetBody):
    """
    Determine extrude direction by checking which side of the sketch plane
    enters the target body.

    Args:
        sketch: The sketch containing the profile
        circleCenter: Center of the circle in sketch space (Point2D)
        targetBody: The body to cut into

    Returns:
        adsk.fusion.ExtentDirections enum value, or None on failure
    """
    try:
        log("--- findExtrudeDirectionFromSketch START ---")

        sketchTransform = sketch.transform
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)

        log(f"Circle center (world): ({center3D.x:.4f}, {center3D.y:.4f}, {center3D.z:.4f})")

        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()
        log(f"Sketch normal: ({zAxis.x:.4f}, {zAxis.y:.4f}, {zAxis.z:.4f})")

        testDistances = [0.01, 0.05, 0.1, 0.2]  # cm: 0.1mm, 0.5mm, 1mm, 2mm

        positiveIsInside = False
        negativeIsInside = False

        log("Testing positive direction...")
        for testDistance in testDistances:
            positivePoint = adsk.core.Point3D.create(
                center3D.x + zAxis.x * testDistance,
                center3D.y + zAxis.y * testDistance,
                center3D.z + zAxis.z * testDistance
            )
            positiveContainment = targetBody.pointContainment(positivePoint)
            containment_str = "INSIDE" if positiveContainment == adsk.fusion.PointContainment.PointInsidePointContainment else \
                             "ON_SURFACE" if positiveContainment == adsk.fusion.PointContainment.PointOnPointContainment else "OUTSIDE"
            log(f"  Distance {testDistance:.3f}cm: {containment_str}")
            if (positiveContainment == adsk.fusion.PointContainment.PointInsidePointContainment or
                    positiveContainment == adsk.fusion.PointContainment.PointOnPointContainment):
                positiveIsInside = True
                log(f"  Positive direction enters body at {testDistance:.3f}cm")
                break

        log("Testing negative direction...")
        for testDistance in testDistances:
            negativePoint = adsk.core.Point3D.create(
                center3D.x - zAxis.x * testDistance,
                center3D.y - zAxis.y * testDistance,
                center3D.z - zAxis.z * testDistance
            )
            negativeContainment = targetBody.pointContainment(negativePoint)
            containment_str = "INSIDE" if negativeContainment == adsk.fusion.PointContainment.PointInsidePointContainment else \
                             "ON_SURFACE" if negativeContainment == adsk.fusion.PointContainment.PointOnPointContainment else "OUTSIDE"
            log(f"  Distance {testDistance:.3f}cm: {containment_str}")
            if (negativeContainment == adsk.fusion.PointContainment.PointInsidePointContainment or
                    negativeContainment == adsk.fusion.PointContainment.PointOnPointContainment):
                negativeIsInside = True
                log(f"  Negative direction enters body at {testDistance:.3f}cm")
                break

        if positiveIsInside and not negativeIsInside:
            log("Decision: POSITIVE direction (only positive is inside)")
            log("--- findExtrudeDirectionFromSketch END (success) ---")
            return adsk.fusion.ExtentDirections.PositiveExtentDirection
        elif negativeIsInside and not positiveIsInside:
            log("Decision: NEGATIVE direction (only negative is inside)")
            log("--- findExtrudeDirectionFromSketch END (success) ---")
            return adsk.fusion.ExtentDirections.NegativeExtentDirection
        elif positiveIsInside and negativeIsInside:
            log("Both directions inside body - sketch is embedded in material")
            log("Testing very close to sketch plane to determine surface side...")

            verySmallDistance = 0.001  # 0.01mm

            veryClosePositive = adsk.core.Point3D.create(
                center3D.x + zAxis.x * verySmallDistance,
                center3D.y + zAxis.y * verySmallDistance,
                center3D.z + zAxis.z * verySmallDistance
            )
            veryCloseNegative = adsk.core.Point3D.create(
                center3D.x - zAxis.x * verySmallDistance,
                center3D.y - zAxis.y * verySmallDistance,
                center3D.z - zAxis.z * verySmallDistance
            )

            posContain = targetBody.pointContainment(veryClosePositive)
            negContain = targetBody.pointContainment(veryCloseNegative)

            posOut = (posContain == adsk.fusion.PointContainment.PointOutsidePointContainment)
            negOut = (negContain == adsk.fusion.PointContainment.PointOutsidePointContainment)

            log(f"  Very close positive: {'OUTSIDE' if posOut else 'INSIDE/ON'}")
            log(f"  Very close negative: {'OUTSIDE' if negOut else 'INSIDE/ON'}")

            if posOut and not negOut:
                log("Decision: NEGATIVE direction (positive side is outside)")
                log("--- findExtrudeDirectionFromSketch END (success) ---")
                return adsk.fusion.ExtentDirections.NegativeExtentDirection
            elif negOut and not posOut:
                log("Decision: POSITIVE direction (negative side is outside)")
                log("--- findExtrudeDirectionFromSketch END (success) ---")
                return adsk.fusion.ExtentDirections.PositiveExtentDirection
            else:
                log("Decision: POSITIVE direction (default fallback)")
                log("--- findExtrudeDirectionFromSketch END (success) ---")
                return adsk.fusion.ExtentDirections.PositiveExtentDirection
        else:
            log("ERROR: Neither direction is inside body - sketch not on body surface")
            log("--- findExtrudeDirectionFromSketch END (failed) ---")
            return None

    except Exception:
        log(f"EXCEPTION in findExtrudeDirectionFromSketch: {traceback.format_exc()}")
        log("--- findExtrudeDirectionFromSketch END (exception) ---")
        if tm_state._ui:
            tm_state._ui.messageBox('Error in findExtrudeDirectionFromSketch:\n{}'.format(traceback.format_exc()))
        return None


def findChamferEdge(extrudeFeature, targetBody, sketch, circleCenter, holeDiameter):
    """
    Find the circular edge at the hole entrance for chamfering.

    Args:
        extrudeFeature: The extrude feature that created the hole
        targetBody: The body that was cut
        sketch: The sketch containing the circle
        circleCenter: Center point of the circle (Point2D)
        holeDiameter: The diameter of the hole in cm

    Returns:
        The edge to chamfer, or None if not found
    """
    try:
        sketchTransform = sketch.transform
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)

        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()

        expectedRadius = holeDiameter / 2.0
        candidateEdges = []

        for edge in targetBody.edges:
            if edge.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
                edgeCircle = edge.geometry
                edgeCenter = edgeCircle.center
                edgeRadius = edgeCircle.radius
                edgeNormal = edgeCircle.normal

                if abs(edgeRadius - expectedRadius) > 0.001:
                    continue

                dotProduct = abs(edgeNormal.x * zAxis.x + edgeNormal.y * zAxis.y + edgeNormal.z * zAxis.z)
                if dotProduct < 0.99:
                    continue

                vecToEdge = adsk.core.Vector3D.create(
                    edgeCenter.x - center3D.x,
                    edgeCenter.y - center3D.y,
                    edgeCenter.z - center3D.z
                )
                projection = vecToEdge.x * zAxis.x + vecToEdge.y * zAxis.y + vecToEdge.z * zAxis.z
                perpDist = vecToEdge.length - abs(projection)
                if perpDist > 0.01:
                    continue

                candidateEdges.append((edge, abs(projection)))

        if len(candidateEdges) > 0:
            candidateEdges.sort(key=lambda x: x[1])
            return candidateEdges[0][0]

        return None

    except Exception:
        if tm_state._ui:
            tm_state._ui.messageBox('Error in findChamferEdge:\n{}'.format(traceback.format_exc()))
        return None


def addChamferToEdge(component, edge, chamferSize):
    """
    Add a chamfer to the specified edge.

    Args:
        component: The component containing the feature
        edge: The edge to chamfer
        chamferSize: Chamfer distance in mm

    Returns:
        The chamfer feature, or None if failed
    """
    try:
        chamfers = component.features.chamferFeatures
        edges = adsk.core.ObjectCollection.create()
        edges.add(edge)
        chamferInput = chamfers.createInput(edges, True)
        chamferDistance = adsk.core.ValueInput.createByReal(chamferSize / 10.0)
        chamferInput.setToEqualDistance(chamferDistance)
        chamfer = chamfers.add(chamferInput)
        return chamfer
    except Exception:
        if tm_state._ui:
            tm_state._ui.messageBox('Error in addChamferToEdge:\n{}'.format(traceback.format_exc()))
        return None


def findDistanceThroughBody(sketch, circleCenter, targetBody, direction):
    """
    Find the distance to cut completely through the body in the given direction.

    Args:
        sketch: The sketch containing the circle
        circleCenter: Center point of the circle (Point2D)
        targetBody: The body to cut through
        direction: Extrusion direction enum value

    Returns:
        Distance in cm, or fallback of 10.0 cm
    """
    try:
        sketchTransform = sketch.transform
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)

        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()

        multiplier = 1.0 if direction == adsk.fusion.ExtentDirections.PositiveExtentDirection else -1.0

        maxDistance = 100.0  # 1000mm max
        stepSize = 0.1       # 1mm steps

        insideBody = False
        exitDistance = None

        for i in range(1, int(maxDistance / stepSize) + 1):
            distance = i * stepSize
            testPoint = adsk.core.Point3D.create(
                center3D.x + zAxis.x * distance * multiplier,
                center3D.y + zAxis.y * distance * multiplier,
                center3D.z + zAxis.z * distance * multiplier
            )
            containment = targetBody.pointContainment(testPoint)
            if containment == adsk.fusion.PointContainment.PointInsidePointContainment:
                insideBody = True
            if insideBody and containment == adsk.fusion.PointContainment.PointOutsidePointContainment:
                exitDistance = distance
                break

        if exitDistance is not None:
            return exitDistance + 0.2  # 2mm margin

        return 10.0  # 100mm default

    except Exception:
        if tm_state._ui:
            tm_state._ui.messageBox('Error in findDistanceThroughBody:\n{}'.format(traceback.format_exc()))
        return 10.0


def addBottomRadiusToBlindHole(component, extrudeFeature, targetBody, sketch, circleCenter, holeDiameter, radiusSize):
    """
    Add a fillet to the bottom edge of a blind hole.

    Args:
        component: The component containing features
        extrudeFeature: The extrude feature that created the hole
        targetBody: The body that was cut
        sketch: The sketch containing the circle
        circleCenter: Center point of the circle (Point2D)
        holeDiameter: Diameter of the hole in cm
        radiusSize: Fillet radius in mm

    Returns:
        The fillet feature, or None if failed
    """
    try:
        log("=== addBottomRadiusToBlindHole START ===")
        log(f"Hole diameter: {holeDiameter:.4f}cm, Fillet radius size: {radiusSize}mm")

        sketchTransform = sketch.transform
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)

        log(f"Circle center (world): ({center3D.x:.4f}, {center3D.y:.4f}, {center3D.z:.4f})")

        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()
        log(f"Sketch normal: ({zAxis.x:.4f}, {zAxis.y:.4f}, {zAxis.z:.4f})")

        expectedRadius = holeDiameter / 2.0
        log(f"Expected edge radius: {expectedRadius:.4f}cm ({expectedRadius * 10:.2f}mm)")

        filletRadiusCm = radiusSize / 10.0
        log(f"Fillet radius: {filletRadiusCm:.4f}cm ({radiusSize}mm)")

        if filletRadiusCm >= expectedRadius:
            log(f"WARNING: Fillet radius ({radiusSize}mm) >= hole radius ({expectedRadius*10:.2f}mm)!")

        candidateEdges = []

        log(f"\nSearching through {targetBody.edges.count} edges on target body...")
        edgeCount = 0
        circleCount = 0
        rejectionReasons = {'not_circle': 0, 'radius_mismatch': 0, 'not_aligned': 0, 'not_on_axis': 0}

        for edge in targetBody.edges:
            edgeCount += 1

            if edge.geometry.curveType != adsk.core.Curve3DTypes.Circle3DCurveType:
                rejectionReasons['not_circle'] += 1
                continue

            circleCount += 1
            edgeCircle = edge.geometry
            edgeCenter = edgeCircle.center
            edgeRadius = edgeCircle.radius
            edgeNormal = edgeCircle.normal

            log(f"\n  Circle Edge #{circleCount} (Edge #{edgeCount}):")
            log(f"    Center: ({edgeCenter.x:.4f}, {edgeCenter.y:.4f}, {edgeCenter.z:.4f})")
            log(f"    Radius: {edgeRadius:.4f}cm ({edgeRadius*10:.2f}mm)")
            log(f"    Normal: ({edgeNormal.x:.4f}, {edgeNormal.y:.4f}, {edgeNormal.z:.4f})")

            radiusDiff = abs(edgeRadius - expectedRadius)
            log(f"    Radius difference: {radiusDiff:.6f}cm ({radiusDiff*10:.4f}mm)")

            if radiusDiff > 0.005:
                log(f"    REJECTED - Radius mismatch (diff={radiusDiff*10:.4f}mm > 0.05mm)")
                rejectionReasons['radius_mismatch'] += 1
                continue
            log(f"    Radius matches")

            dotProduct = abs(edgeNormal.x * zAxis.x + edgeNormal.y * zAxis.y + edgeNormal.z * zAxis.z)
            log(f"    Alignment dot product: {dotProduct:.6f}")

            if dotProduct < 0.95:
                log(f"    REJECTED - Not aligned with sketch normal (dot={dotProduct:.6f} < 0.95)")
                rejectionReasons['not_aligned'] += 1
                continue
            log(f"    Aligned with sketch normal")

            vecToEdge = adsk.core.Vector3D.create(
                edgeCenter.x - center3D.x,
                edgeCenter.y - center3D.y,
                edgeCenter.z - center3D.z
            )
            distanceAlongNormal = abs(vecToEdge.x * zAxis.x + vecToEdge.y * zAxis.y + vecToEdge.z * zAxis.z)
            perpDistanceSquared = (vecToEdge.length ** 2) - (distanceAlongNormal ** 2)
            perpDistance = math.sqrt(max(0, perpDistanceSquared))

            log(f"    Distance along normal: {distanceAlongNormal:.4f}cm ({distanceAlongNormal*10:.2f}mm)")
            log(f"    Perpendicular distance from axis: {perpDistance:.4f}cm ({perpDistance*10:.2f}mm)")

            if perpDistance > 0.05:
                log(f"    REJECTED - Not on hole axis (perpDist={perpDistance*10:.2f}mm > 0.5mm)")
                rejectionReasons['not_on_axis'] += 1
                continue
            log(f"    CANDIDATE ACCEPTED - Distance from sketch: {distanceAlongNormal:.4f}cm")
            candidateEdges.append((edge, distanceAlongNormal))

        log(f"\n=== SEARCH SUMMARY ===")
        log(f"Total edges examined: {edgeCount}")
        log(f"Circular edges found: {circleCount}")
        log(f"Candidates found: {len(candidateEdges)}")
        log(f"Rejection reasons: not_circle={rejectionReasons['not_circle']}, "
            f"radius_mismatch={rejectionReasons['radius_mismatch']}, "
            f"not_aligned={rejectionReasons['not_aligned']}, "
            f"not_on_axis={rejectionReasons['not_on_axis']}")

        if len(candidateEdges) == 0:
            log("ERROR: No candidate edges found!")
            log("=== addBottomRadiusToBlindHole END (no candidates) ===")
            return None

        # Sort by distance: furthest = bottom of blind hole
        candidateEdges.sort(key=lambda x: x[1], reverse=True)
        bottomEdge = candidateEdges[0][0]
        bottomDistance = candidateEdges[0][1]
        log(f"\nUsing edge at distance: {bottomDistance:.4f}cm ({bottomDistance*10:.2f}mm)")

        fillets = component.features.filletFeatures
        edgeCollection = adsk.core.ObjectCollection.create()
        edgeCollection.add(bottomEdge)

        filletInput = fillets.createInput()

        try:
            filletInput.addConstantRadiusEdgeSet(
                edgeCollection,
                adsk.core.ValueInput.createByReal(filletRadiusCm),
                True  # isTangentChain
            )
        except Exception as e:
            log(f"ERROR adding edge set: {str(e)}")
            log("=== addBottomRadiusToBlindHole END (edge set error) ===")
            return None

        try:
            fillet = fillets.add(filletInput)
            if fillet:
                log("SUCCESS: Fillet created successfully!")
                log("=== addBottomRadiusToBlindHole END (success) ===")
                return fillet
            else:
                log("ERROR: fillets.add() returned None")
                log("=== addBottomRadiusToBlindHole END (fillet creation failed) ===")
                return None
        except Exception as e:
            log(f"EXCEPTION during fillet.add(): {str(e)}")
            log(traceback.format_exc())
            log("=== addBottomRadiusToBlindHole END (exception) ===")
            return None

    except Exception as e:
        log(f"FATAL EXCEPTION in addBottomRadiusToBlindHole: {str(e)}")
        log(traceback.format_exc())
        log("=== addBottomRadiusToBlindHole END (fatal exception) ===")
        if tm_state._ui:
            tm_state._ui.messageBox('Error in addBottomRadiusToBlindHole:\n{}'.format(traceback.format_exc()))
        return None
