"""
tm_helpers.py – Utility functions: geometry comparisons, logging.

Also exports calc_blind_hole_depth() for use in tm_execute and tests.
"""
import adsk.core
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


