"""
Unit tests for sketch plane resolution (ADR-0002, GitHub issue #1):
resolveSketchPlane, findFaceForSketchPlane, alignExtrudeDirection.
"""

import math
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock

import adsk.core
import adsk.fusion
from core.tm_geometry import (
    resolveSketchPlane,
    findFaceForSketchPlane,
    alignExtrudeDirection,
)

POSITIVE = adsk.fusion.ExtentDirections.PositiveExtentDirection
NEGATIVE = adsk.fusion.ExtentDirections.NegativeExtentDirection


def vec(x, y, z):
    return SimpleNamespace(x=x, y=y, z=z, length=math.sqrt(x * x + y * y + z * z))


def make_sketch(origin=(0, 0, 0), normal=(0, 0, 1), reference_plane_error=True):
    """Sketch mock whose transform describes the plane through origin with normal."""
    sketch = MagicMock()
    sketch.transform.getAsCoordinateSystem.return_value = (
        vec(*origin), vec(1, 0, 0), vec(0, 1, 0), vec(*normal))
    if reference_plane_error:
        type(sketch).referencePlane = PropertyMock(side_effect=RuntimeError(
            '3 : referencePlane is a BRefFace - need to roll timeline back before sketch'))
    return sketch


def make_face(point, normal, planar=True, name='face'):
    face = MagicMock(name=name)
    if planar:
        face.geometry.surfaceType = adsk.core.SurfaceTypes.PlaneSurfaceType
    else:
        face.geometry.surfaceType = adsk.core.SurfaceTypes.CylinderSurfaceType
    face.pointOnFace = vec(*point)
    face.evaluator.getNormalAtPoint.return_value = (True, vec(*normal))
    return face


def make_body(faces, component=None):
    body = MagicMock()
    body.faces = faces
    if component is not None:
        body.parentComponent = component
    return body


def make_target(faces, other_bodies=()):
    """Target Body in a component that also holds other_bodies."""
    component = MagicMock()
    target = make_body(faces, component)
    component.bRepBodies = [target] + list(other_bodies)
    return target


class TestResolveSketchPlane:

    def test_reference_plane_returned_when_readable(self):
        """Construction plane sketches keep the old path untouched."""
        sketch = make_sketch(reference_plane_error=False)
        plane = MagicMock(name='constructionPlane')
        sketch.referencePlane = plane
        target = make_target([])
        assert resolveSketchPlane(sketch, target) is plane

    def test_falls_back_to_face_lookup_when_reference_plane_raises(self):
        sketch = make_sketch(origin=(0, 0, 2), normal=(0, 0, 1))
        top = make_face((1, 1, 2), (0, 0, 1), name='top')
        target = make_target([make_face((1, 1, 0), (0, 0, -1)), top])
        assert resolveSketchPlane(sketch, target) is top

    def test_returns_none_when_no_face_matches(self):
        sketch = make_sketch(origin=(0, 0, 5), normal=(0, 0, 1))
        target = make_target([make_face((0, 0, 2), (0, 0, 1))])
        assert resolveSketchPlane(sketch, target) is None


class TestFindFaceForSketchPlane:

    def test_coplanar_same_normal_found(self):
        sketch = make_sketch(origin=(0, 0, 2), normal=(0, 0, 1))
        face = make_face((3, -4, 2), (0, 0, 1))
        assert findFaceForSketchPlane(sketch, make_target([face])) is face

    def test_coplanar_opposite_normal_used_as_fallback(self):
        sketch = make_sketch(origin=(0, 0, 2), normal=(0, 0, 1))
        face = make_face((0, 0, 2), (0, 0, -1))
        assert findFaceForSketchPlane(sketch, make_target([face])) is face

    def test_same_normal_preferred_over_opposite(self):
        sketch = make_sketch(origin=(0, 0, 2), normal=(0, 0, 1))
        opposite = make_face((0, 0, 2), (0, 0, -1), name='opposite')
        same = make_face((5, 5, 2), (0, 0, 1), name='same')
        assert findFaceForSketchPlane(sketch, make_target([opposite, same])) is same

    def test_parallel_offset_plane_rejected(self):
        sketch = make_sketch(origin=(0, 0, 2), normal=(0, 0, 1))
        face = make_face((0, 0, 2.5), (0, 0, 1))
        assert findFaceForSketchPlane(sketch, make_target([face])) is None

    def test_tilted_face_through_origin_rejected(self):
        sketch = make_sketch(origin=(0, 0, 0), normal=(0, 0, 1))
        face = make_face((0, 0, 0), (0, 1, 1))
        assert findFaceForSketchPlane(sketch, make_target([face])) is None

    def test_non_planar_face_skipped(self):
        sketch = make_sketch(origin=(0, 0, 0), normal=(0, 0, 1))
        face = make_face((0, 0, 0), (0, 0, 1), planar=False)
        assert findFaceForSketchPlane(sketch, make_target([face])) is None

    def test_face_on_other_body_in_component_found(self):
        """Sketch on body A, Target Body B — worked in v1.2.0, must keep working."""
        sketch = make_sketch(origin=(0, 0, 10), normal=(0, 0, 1))
        face_a = make_face((0, 0, 10), (0, 0, 1), name='bodyA-top')
        body_a = make_body([face_a])
        target = make_target([make_face((0, 0, 3), (0, 0, 1))], other_bodies=[body_a])
        assert findFaceForSketchPlane(sketch, target) is face_a

    def test_target_body_searched_before_other_bodies(self):
        sketch = make_sketch(origin=(0, 0, 2), normal=(0, 0, 1))
        on_other = make_face((0, 0, 2), (0, 0, 1), name='other')
        on_target = make_face((0, 0, 2), (0, 0, 1), name='target')
        target = make_target([on_target], other_bodies=[make_body([on_other])])
        assert findFaceForSketchPlane(sketch, target) is on_target

    def test_non_unit_normals_handled(self):
        sketch = make_sketch(origin=(0, 0, 1), normal=(0, 0, 3))
        face = make_face((2, 2, 1), (0, 0, 0.5))
        assert findFaceForSketchPlane(sketch, make_target([face])) is face


class TestAlignExtrudeDirection:

    def test_same_normal_keeps_direction(self):
        parent = make_sketch(normal=(0, 0, 1))
        temp = make_sketch(normal=(0, 0, 1))
        assert alignExtrudeDirection(POSITIVE, parent, temp) is POSITIVE
        assert alignExtrudeDirection(NEGATIVE, parent, temp) is NEGATIVE

    def test_opposite_normal_flips_direction(self):
        parent = make_sketch(normal=(0, 0, 1))
        temp = make_sketch(normal=(0, 0, -1))
        assert alignExtrudeDirection(POSITIVE, parent, temp) is NEGATIVE
        assert alignExtrudeDirection(NEGATIVE, parent, temp) is POSITIVE
