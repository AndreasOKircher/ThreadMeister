"""
tm_helpers.py – Utility functions: geometry comparisons, logging, diagnostics.

Also exports calc_blind_hole_depth() for use in tm_execute and tests.
"""
import adsk.core
import math
import tm_state


def isSamePoint(p1, p2, tol=None):
    """Return True if two Point3D objects are within tolerance."""
    if tol is None:
        tol = tm_state.TOL
    return (abs(p1.x - p2.x) < tol and
            abs(p1.y - p2.y) < tol and
            abs(p1.z - p2.z) < tol)


def isSameCircle(c1, c2, tol=None):
    """Return True if two SketchCircles have the same center and radius."""
    if tol is None:
        tol = tm_state.TOL
    c1_center = c1.centerSketchPoint.geometry
    c2_center = c2.centerSketchPoint.geometry
    if not isSamePoint(c1_center, c2_center, tol):
        return False
    return abs(c1.radius - c2.radius) < tol


def calc_blind_hole_depth(insert_len_mm, extra_depth_mm):
    """
    Calculate the extrusion depth for a blind hole in cm (Fusion's internal unit).

    Args:
        insert_len_mm: Insert length in mm (from INSERT_SPECS)
        extra_depth_mm: Extra safety depth in mm (from CONFIG['blind_hole_extra_depth'])

    Returns:
        Depth in cm as a float.
    """
    return (insert_len_mm + extra_depth_mm) / 10.0


def log(msg):
    """Write a message to Fusion's Text Commands palette (only if logging enabled)."""
    try:
        if not tm_state.CONFIG.get('enable_logging', False):
            return
        app = adsk.core.Application.get()
        ui = app.userInterface
        p = ui.palettes.itemById('TextCommands')
        if not p.isVisible:
            p.isVisible = True
        p.writeText(str(msg))
    except Exception:
        pass


def clear_log():
    """Clear the Text Commands palette (workaround: write 50 blank lines)."""
    try:
        if not tm_state.CONFIG.get('enable_logging', False):
            return
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


def diagnose_blind_hole(component, targetBody, sketch, circleCenter, holeDiameter):
    """
    Diagnostic helper: logs all circular edges on targetBody sorted by radius proximity.
    Call this if bottom radius consistently fails.
    """
    log("\n=== BLIND HOLE DIAGNOSTIC ===")

    sketchTransform = sketch.transform
    center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
    center3D = center3DSketch.copy()
    center3D.transformBy(sketchTransform)

    (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()
    expectedRadius = holeDiameter / 2.0

    log(f"Looking for edges with radius ~{expectedRadius:.4f}cm")
    log(f"Along axis from ({center3D.x:.4f}, {center3D.y:.4f}, {center3D.z:.4f})")

    allCircularEdges = []
    for edge in targetBody.edges:
        if edge.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
            edgeCircle = edge.geometry
            allCircularEdges.append({
                'edge': edge,
                'radius': edgeCircle.radius,
                'center': edgeCircle.center
            })

    log(f"\nFound {len(allCircularEdges)} circular edges total")
    log("\nClosest matches by radius:")

    sorted_by_radius = sorted(allCircularEdges, key=lambda x: abs(x['radius'] - expectedRadius))
    for i, info in enumerate(sorted_by_radius[:5]):
        diff = abs(info['radius'] - expectedRadius)
        log(f"  {i+1}. Radius: {info['radius']:.4f}cm (diff: {diff*10:.4f}mm)")

    log("=== END DIAGNOSTIC ===\n")
