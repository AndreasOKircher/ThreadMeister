"""
tm_ridge.py – Ridge Thread geometry (pure maths, no Fusion calls).

A Ridge Thread is a Bore a little larger than the screw, with N arc-shaped Ridges that
stick into it. The screw forms its own thread in the Ridges. All lengths in mm.

Built-in per size (ThreadMeisterExtended values): bore diameter, arc distance (hole axis
to Ridge-circle centre), Ridge count, lead-in chamfer. Only the inner diameter at the
Ridges is user-tunable (config.ini [Ridge Threads]); the Ridge-circle diameter follows
from it with the arc distance unchanged.
"""
import math
from collections import namedtuple

RidgeGeometry = namedtuple(
    'RidgeGeometry',
    'bore_dia arc_distance count ridge_dia chamfer default_depth')

# size: (screw_dia, bore_dia, arc_distance, count, chamfer)
_BUILT_IN = {
    'M3': (3.0, 3.2, 2.05, 3, 0.28),
    'M4': (4.0, 4.2, 2.75, 3, 0.33),
    'M5': (5.0, 5.3, 3.50, 4, 0.37),
}

# Bore Type names (dialog dropdown, config.ini [UI State] last_bore_type)
BORE_TYPE_INSERT = 'Heat-Set Insert'
BORE_TYPE_RIDGE = 'Ridge Thread'

# Default inner diameter at the Ridges (user print tests, PRD): config.ini [Ridge Threads]
DEFAULT_INNER_DIA = {'M3': 2.40, 'M4': 3.50, 'M5': 4.50}

CHAMFER_ANGLE_DEG = 78.0  # lead-in chamfer angle from the face plane

DEFAULT_DEPTH_FACTOR = 4.0  # default blind depth = 4 x screw diameter


def ridge_geometry(size, inner_dia_mm):
    """Return the RidgeGeometry for a size and an inner diameter at the Ridges."""
    screw_dia, bore_dia, arc_distance, count, chamfer = _BUILT_IN[size]
    ridge_dia = 2.0 * arc_distance - inner_dia_mm
    return RidgeGeometry(bore_dia, arc_distance, count, ridge_dia, chamfer,
                         DEFAULT_DEPTH_FACTOR * screw_dia)


def is_ridge_top_edge(g, radius_mm, axial_offset_mm, radial_offset_mm):
    """True if an arc edge is a Ridge top edge of THIS Bore (for the lead-in chamfer).

    radius_mm: arc radius. axial_offset_mm: distance of the arc centre from the sketch
    plane. radial_offset_mm: distance of the arc centre from this Bore's axis.
    """
    if abs(radius_mm - g.ridge_dia / 2.0) > 0.05:
        return False
    if abs(axial_offset_mm) > 0.05:
        return False
    return abs(radial_offset_mm - g.arc_distance) <= max(0.1, g.ridge_dia / 2.0 * 0.5)


def _lens_area(R, r, d):
    """Area where two circles (radii R, r, centre distance d) overlap."""
    if d >= R + r:
        return 0.0
    if d <= abs(R - r):
        return math.pi * min(R, r) ** 2
    a = R * R * math.acos((d * d + R * R - r * r) / (2 * d * R))
    b = r * r * math.acos((d * d + r * r - R * R) / (2 * d * r))
    c = 0.5 * math.sqrt((-d + R + r) * (d + R - r) * (d - R + r) * (d + R + r))
    return a + b - c


def central_profile_area_mm2(g):
    """Area of the Bore profile in mm2: bore circle minus the Ridge lobes inside it.

    Used to pick the right profile in the Temp Sketch. Assumes the Ridge lobes do not
    overlap each other (true for all built-in sizes).
    """
    R = g.bore_dia / 2.0
    return math.pi * R * R - g.count * _lens_area(R, g.ridge_dia / 2.0, g.arc_distance)
