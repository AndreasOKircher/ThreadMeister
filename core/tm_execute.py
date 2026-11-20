"""
tm_execute.py – CommandExecuteHandler: orchestrates the hole creation loop.

The per-point Bore loop (runBores) is shared with the Bore Preview (tm_preview.py).
"""
import adsk.core, adsk.fusion, traceback, os
from . import tm_state
from . import tm_config
from . import tm_ridge
from .tm_helpers import calc_blind_hole_depth_mm
from .tm_geometry import (
    findProfileForCircle,
    resolveSketchPlane,
    alignExtrudeDirection,
    findExtrudeDirectionFromSketch,
    findChamferEdge,
    addChamferToEdge,
    findDistanceThroughBody,
    addBottomRadiusToBlindHole,
    createRidgeThreadSketch,
    getRidgeChamferEdges,
    addAngleChamferToEdge,
)


class BoreParams:
    """What the dialog asks for, read once from the command inputs (no side effects)."""

    def __init__(self, inputs):
        insertSize = inputs.itemById('insertSize')
        exportDebugInput = inputs.itemById('exportDebug')
        self.shouldExport = exportDebugInput is not None and exportDebugInput.value
        self.insertName = insertSize.selectedItem.name
        self.isRidge = inputs.itemById('boreType').selectedItem.name == tm_ridge.BORE_TYPE_RIDGE
        self.isBlindHole = inputs.itemById('holeType').selectedItem.name == 'Blind Hole'
        self.showMessage = inputs.itemById('showSuccessMessage').value

        if self.isRidge:
            # Ridge Thread: no Chamfer / Bottom Radius options; depth from the dialog
            self.ridgeGeometry = tm_ridge.ridge_geometry(
                self.insertName, tm_state.RIDGE_THREAD_SPECS[self.insertName])
            self.ridgeDepth = inputs.itemById('ridgeDepth').value   # cm
            self.includeChamfer = False
            self.includeBottomRadius = False
            self.label = f'{self.insertName} Ridge Thread'
            self.noun = 'Ridge Thread(s)'
            self.radius = self.ridgeGeometry.bore_dia / 2.0 / 10.0   # mm -> cm
        else:
            self.includeChamfer = inputs.itemById('addChamfer').value
            self.includeBottomRadius = inputs.itemById('addBottomRadius').value and self.isBlindHole
            self.holeDia, self.insertLen, self.minWall = tm_state.INSERT_SPECS[self.insertName]
            self.label = self.insertName
            self.noun = 'insert hole(s)'
            self.radius = self.holeDia / 2.0 / 10.0   # mm -> cm
        self.diameter = self.radius * 2.0


class BoreResult:
    def __init__(self):
        self.successCount = 0
        self.failedCount = 0
        self.failMessages = []
        self.warnMessages = []


def runBores(targetBody, selectedPoints, params):
    """Cut one Bore per Sketch Point into targetBody. Silent: returns a BoreResult, shows nothing."""
    result = BoreResult()
    isRidge = params.isRidge
    isBlindHole = params.isBlindHole
    includeChamfer = params.includeChamfer
    includeBottomRadius = params.includeBottomRadius
    label = params.label
    radius = params.radius
    diameter = params.diameter
    component = targetBody.parentComponent

    for point_idx, point in enumerate(selectedPoints):
        parentSketch = point.parentSketch
        center2d = point.geometry

        # Create clean sketch without auto-projected body edges
        plane = resolveSketchPlane(parentSketch, targetBody)
        if plane is None:
            result.failedCount += 1
            result.failMessages.append(f"Point {point_idx+1}: Could not find the sketch's face. Try placing the sketch on a construction plane.")
            continue
        tempSketch = component.sketches.addWithoutEdges(plane)
        tempSketch.name = f"TM_{label}_P{point_idx+1}"

        # Project original point to maintain parametric association
        projectedEntities = tempSketch.project(point)
        projectedPoint = projectedEntities.item(0)

        if isRidge:
            # Ridge Thread: bore + Ridges, all constrained to the projected point
            circle = None
            profile_or_collection = createRidgeThreadSketch(
                tempSketch, projectedPoint, params.ridgeGeometry)
        else:
            # Create bore circle in clean sketch
            circle = tempSketch.sketchCurves.sketchCircles.addByCenterRadius(
                projectedPoint.geometry, radius)
            tempConstraints = tempSketch.geometricConstraints
            tempConstraints.addCoincident(circle.centerSketchPoint, projectedPoint)

            profile_or_collection = findProfileForCircle(tempSketch, circle)

        if profile_or_collection is None:
            result.failedCount += 1
            result.failMessages.append(f'Point {point_idx+1}: Could not create bore profile.')
            tempSketch.deleteMe()
            continue

        # Export debug JSON if enabled
        if params.shouldExport and circle is not None:
            try:
                from .tm_debug_export import export_sketch_data
                export_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), 'debug_exports')
                os.makedirs(export_dir, exist_ok=True)
                export_sketch_data(
                    tempSketch, circle, export_dir,
                    description=f"Point {point_idx+1} - {params.insertName}"
                )
            except Exception:
                pass

        direction = findExtrudeDirectionFromSketch(parentSketch, center2d, targetBody)

        if direction is None:
            result.failedCount += 1
            result.failMessages.append(f'Point {point_idx+1}: Could not determine extrusion direction. Ensure the sketch is on a planar face of the target body.')
            tempSketch.deleteMe()
            continue

        # direction is relative to the Parent Sketch; the cut is made from the Temp Sketch
        cutDirection = alignExtrudeDirection(direction, parentSketch, tempSketch)

        extrudes = component.features.extrudeFeatures
        extInput = extrudes.createInput(profile_or_collection, adsk.fusion.FeatureOperations.CutFeatureOperation)

        if isBlindHole:
            if isRidge:
                holeDepth = params.ridgeDepth
            else:
                chamfer = tm_state.CONFIG['chamfer_size'] if includeChamfer else 0.0
                depth_mm = calc_blind_hole_depth_mm(
                    params.insertLen, tm_state.CONFIG['blind_hole_extra_depth'], chamfer)
                holeDepth = depth_mm / 10.0  # mm -> cm
            dist = adsk.core.ValueInput.createByReal(holeDepth)
            extent = adsk.fusion.DistanceExtentDefinition.create(dist)
            extInput.setOneSideExtent(extent, cutDirection)
        else:
            throughDistance = findDistanceThroughBody(parentSketch, center2d, targetBody, direction)
            dist = adsk.core.ValueInput.createByReal(throughDistance)
            extent = adsk.fusion.DistanceExtentDefinition.create(dist)
            extInput.setOneSideExtent(extent, cutDirection)

        extInput.participantBodies = [targetBody]
        extrude = extrudes.add(extInput)

        if isRidge:
            # Lead-in chamfer on the Ridge top edges; failure keeps the bore
            ridgeEdges = getRidgeChamferEdges(
                targetBody, tempSketch, projectedPoint.geometry, params.ridgeGeometry)
            if ridgeEdges is None or addAngleChamferToEdge(
                    component, ridgeEdges, params.ridgeGeometry.chamfer,
                    tm_ridge.CHAMFER_ANGLE_DEG) is None:
                result.warnMessages.append(
                    f'Point {point_idx+1}: Ridge Thread created, but the lead-in chamfer could not be added.')

        if includeChamfer:
            chamferEdge = findChamferEdge(extrude, targetBody, parentSketch, center2d, diameter)
            if chamferEdge:
                addChamferToEdge(component, chamferEdge, tm_state.CONFIG['chamfer_size'])

        if includeBottomRadius:
            addBottomRadiusToBlindHole(
                component, extrude, targetBody, parentSketch, center2d,
                diameter, tm_state.CONFIG['bottom_radius_size']
            )

        result.successCount += 1

    return result


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            targetBody = inputs.itemById('bodySelect').selection(0).entity
            pointSelect = inputs.itemById('pointSelect')
            selectedPoints = [pointSelect.selection(i).entity for i in range(pointSelect.selectionCount)]

            params = BoreParams(inputs)

            if params.isRidge:
                tm_config.save_bore_type_state(tm_ridge.BORE_TYPE_RIDGE, params.insertName)
                # Keep Hole Type and the success-message checkbox; leave the insert-only checkboxes as they were
                tm_config.save_checkbox_states(
                    tm_state.CONFIG.get('chamfer_enabled_default', True),
                    tm_state.CONFIG.get('bottom_radius_enabled_default', False),
                    params.showMessage, params.isBlindHole)
            else:
                tm_config.save_bore_type_state(
                    tm_ridge.BORE_TYPE_INSERT, tm_state.CONFIG.get('last_ridge_thread', 'M3'))
                tm_config.save_last_selected_insert(params.insertName)
                tm_config.save_checkbox_states(
                    params.includeChamfer, params.includeBottomRadius,
                    params.showMessage, params.isBlindHole)
            showPreviewInput = inputs.itemById('showPreview')
            if showPreviewInput is not None:
                tm_config.save_show_preview(showPreviewInput.value)

            component = targetBody.parentComponent
            design = component.parentDesign
            timeline = None
            startIndex = -1

            if design and hasattr(design, 'timeline'):
                timeline = design.timeline
                if timeline and timeline.count > 0:
                    startIndex = timeline.markerPosition

            result = runBores(targetBody, selectedPoints, params)
            successCount = result.successCount
            failedCount = result.failedCount

            if successCount > 0 and timeline is not None and startIndex >= 0:
                try:
                    endIndex = timeline.markerPosition - 1
                    if endIndex >= startIndex:
                        timelineGroup = timeline.timelineGroups.add(startIndex, endIndex)
                        timelineGroup.name = f'({successCount}x {params.label})'
                except Exception:
                    pass

            warnMessages = result.warnMessages
            warnText = ('\n\nWarnings:\n' + '\n'.join(warnMessages)) if warnMessages else ''
            if failedCount > 0:
                details = '\n'.join(result.failMessages)
                tm_state._ui.messageBox(
                    f'Created {successCount} {params.noun}, {failedCount} failed.\n\n{details}{warnText}'
                )
            elif params.showMessage or warnMessages:
                tm_state._ui.messageBox(f'Successfully created {successCount} {params.noun}.{warnText}')

        except Exception:
            tm_state._ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
