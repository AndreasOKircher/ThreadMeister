"""
tm_execute.py – CommandExecuteHandler: orchestrates the hole creation loop.
"""
import adsk.core, adsk.fusion, traceback, os
import tm_state
import tm_config
from tm_helpers import calc_blind_hole_depth
from tm_geometry import (
    findProfileForCircle,
    findExtrudeDirectionFromSketch,
    findChamferEdge,
    addChamferToEdge,
    findDistanceThroughBody,
    addBottomRadiusToBlindHole,
)


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            bodySelect = inputs.itemById('bodySelect')
            pointSelect = inputs.itemById('pointSelect')
            insertSize = inputs.itemById('insertSize')
            holeType = inputs.itemById('holeType')
            addChamfer = inputs.itemById('addChamfer')
            addBottomRadius = inputs.itemById('addBottomRadius')
            showSuccessMessage = inputs.itemById('showSuccessMessage')
            exportDebugInput = inputs.itemById('exportDebug')
            shouldExport = exportDebugInput is not None and exportDebugInput.value

            targetBody = bodySelect.selection(0).entity
            selectedPoints = [pointSelect.selection(i).entity for i in range(pointSelect.selectionCount)]

            insertName = insertSize.selectedItem.name
            tm_config.save_last_selected_insert(insertName)

            isBlindHole = holeType.selectedItem.name == 'Blind Hole'
            includeChamfer = addChamfer.value
            includeBottomRadius = addBottomRadius.value and isBlindHole
            showMessage = showSuccessMessage.value

            tm_config.save_checkbox_states(includeChamfer, includeBottomRadius, showMessage, isBlindHole)

            holeDia, insertLen, minWall = tm_state.INSERT_SPECS[insertName]
            radius = holeDia / 2.0 / 10.0   # mm -> cm
            diameter = radius * 2.0

            successCount = 0
            failedCount = 0

            component = targetBody.parentComponent
            design = component.parentDesign
            timeline = None
            startIndex = -1

            if design and hasattr(design, 'timeline'):
                timeline = design.timeline
                if timeline and timeline.count > 0:
                    startIndex = timeline.markerPosition

            for point_idx, point in enumerate(selectedPoints):
                parentSketch = point.parentSketch
                center2d = point.geometry

                # Create clean sketch without auto-projected body edges
                face = parentSketch.referencePlane
                tempSketch = component.sketches.addWithoutEdges(face)
                tempSketch.name = f"TM_{insertName}_P{point_idx+1}"

                # Project original point to maintain parametric association
                projectedEntities = tempSketch.project(point)
                projectedPoint = projectedEntities.item(0)

                # Create bore circle in clean sketch
                circle = tempSketch.sketchCurves.sketchCircles.addByCenterRadius(
                    projectedPoint.geometry, radius)
                tempConstraints = tempSketch.geometricConstraints
                tempConstraints.addCoincident(circle.centerSketchPoint, projectedPoint)

                profile_or_collection = findProfileForCircle(tempSketch, circle)

                if profile_or_collection is None:
                    failedCount += 1
                    tempSketch.deleteMe()
                    continue

                # Export debug JSON if enabled
                if shouldExport:
                    try:
                        from tm_debug_export import export_sketch_data
                        export_dir = os.path.join(
                            os.path.dirname(os.path.dirname(__file__)), 'debug_exports')
                        os.makedirs(export_dir, exist_ok=True)
                        export_sketch_data(
                            tempSketch, circle, export_dir,
                            description=f"Point {point_idx+1} - {insertName}"
                        )
                    except Exception:
                        pass

                direction = findExtrudeDirectionFromSketch(parentSketch, center2d, targetBody)

                if direction is None:
                    failedCount += 1
                    tempSketch.deleteMe()
                    continue

                extrudes = component.features.extrudeFeatures
                extInput = extrudes.createInput(profile_or_collection, adsk.fusion.FeatureOperations.CutFeatureOperation)

                if isBlindHole:
                    holeDepth = calc_blind_hole_depth(insertLen, tm_state.CONFIG['blind_hole_extra_depth'])
                    dist = adsk.core.ValueInput.createByReal(holeDepth)
                    extent = adsk.fusion.DistanceExtentDefinition.create(dist)
                    extInput.setOneSideExtent(extent, direction)
                else:
                    throughDistance = findDistanceThroughBody(parentSketch, center2d, targetBody, direction)
                    dist = adsk.core.ValueInput.createByReal(throughDistance)
                    extent = adsk.fusion.DistanceExtentDefinition.create(dist)
                    extInput.setOneSideExtent(extent, direction)

                extInput.participantBodies = [targetBody]
                extrude = extrudes.add(extInput)

                if includeChamfer:
                    chamferEdge = findChamferEdge(extrude, targetBody, parentSketch, center2d, diameter)
                    if chamferEdge:
                        addChamferToEdge(component, chamferEdge, tm_state.CONFIG['chamfer_size'])

                if includeBottomRadius:
                    addBottomRadiusToBlindHole(
                        component, extrude, targetBody, parentSketch, center2d,
                        diameter, tm_state.CONFIG['bottom_radius_size']
                    )

                successCount += 1

            if successCount > 0 and timeline is not None and startIndex >= 0:
                try:
                    endIndex = timeline.markerPosition - 1
                    if endIndex >= startIndex:
                        timelineGroup = timeline.timelineGroups.add(startIndex, endIndex)
                        timelineGroup.name = f'({successCount}x {insertName})'
                except Exception:
                    pass

            if failedCount > 0:
                tm_state._ui.messageBox(
                    f'Created {successCount} insert hole(s).\n{failedCount} failed (no intersection with target body).'
                )
            elif showMessage:
                tm_state._ui.messageBox(f'Successfully created {successCount} insert hole(s).')

        except Exception:
            tm_state._ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
