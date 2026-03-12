"""
tm_execute.py – CommandExecuteHandler: orchestrates the hole creation loop.
"""
import adsk.core, adsk.fusion, traceback, os
import tm_state
import tm_config
from tm_helpers import log, clear_log, calc_blind_hole_depth
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
            clear_log()
            log("=== COMMAND EXECUTE START ===")

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

            log(f"Insert: {insertName}")
            log(f"Hole type: {'Blind' if isBlindHole else 'Through'}")
            log(f"Diameter: {holeDia}mm, Radius: {radius:.4f}cm")
            log(f"Processing {len(selectedPoints)} point(s)...")

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
                log(f"\n--- Processing point {point_idx + 1}/{len(selectedPoints)} ---")

                parentSketch = point.parentSketch
                center2d = point.geometry

                log(f"Point location: ({center2d.x:.4f}, {center2d.y:.4f})")
                log(f"Sketch: {parentSketch.name}")

                circle = parentSketch.sketchCurves.sketchCircles.addByCenterRadius(center2d, radius)
                constraints = parentSketch.geometricConstraints
                constraints.addCoincident(circle.centerSketchPoint, point)

                log("Circle created and constrained to point")

                profile_or_collection = findProfileForCircle(parentSketch, circle)

                if profile_or_collection is None:
                    log(f"FAILED: No profile found for point {point_idx + 1}")
                    failedCount += 1
                    circle.deleteMe()
                    continue

                log("Profile(s) found successfully")

                # Export debug JSON if enabled
                if shouldExport:
                    try:
                        from tm_debug_export import export_sketch_data
                        export_dir = os.path.join(
                            os.path.dirname(os.path.dirname(__file__)), 'debug_exports')
                        os.makedirs(export_dir, exist_ok=True)
                        export_sketch_data(
                            parentSketch, circle, export_dir,
                            description=f"Point {point_idx+1} - {insertName}"
                        )
                    except Exception as e:
                        log(f"[DEBUG EXPORT] Error: {e}")

                direction = findExtrudeDirectionFromSketch(parentSketch, center2d, targetBody)

                if direction is None:
                    log(f"FAILED: Could not determine extrude direction for point {point_idx + 1}")
                    failedCount += 1
                    circle.deleteMe()
                    continue

                direction_str = "Positive" if direction == adsk.fusion.ExtentDirections.PositiveExtentDirection else "Negative"
                log(f"Extrude direction: {direction_str}")

                extrudes = component.features.extrudeFeatures
                extInput = extrudes.createInput(profile_or_collection, adsk.fusion.FeatureOperations.CutFeatureOperation)

                if isBlindHole:
                    holeDepth = calc_blind_hole_depth(insertLen, tm_state.CONFIG['blind_hole_extra_depth'])
                    log(f"Blind hole depth: {holeDepth:.4f}cm")
                    dist = adsk.core.ValueInput.createByReal(holeDepth)
                    extent = adsk.fusion.DistanceExtentDefinition.create(dist)
                    extInput.setOneSideExtent(extent, direction)
                else:
                    throughDistance = findDistanceThroughBody(parentSketch, center2d, targetBody, direction)
                    log(f"Through hole distance: {throughDistance:.4f}cm")
                    dist = adsk.core.ValueInput.createByReal(throughDistance)
                    extent = adsk.fusion.DistanceExtentDefinition.create(dist)
                    extInput.setOneSideExtent(extent, direction)

                extInput.participantBodies = [targetBody]
                extrude = extrudes.add(extInput)

                log("Extrude created successfully")

                if includeChamfer:
                    chamferEdge = findChamferEdge(extrude, targetBody, parentSketch, center2d, diameter)
                    if chamferEdge:
                        addChamferToEdge(component, chamferEdge, tm_state.CONFIG['chamfer_size'])
                        log(f"Chamfer added ({tm_state.CONFIG['chamfer_size']}mm)")
                    else:
                        log("Chamfer edge not found, skipping chamfer")

                if includeBottomRadius:
                    result = addBottomRadiusToBlindHole(
                        component, extrude, targetBody, parentSketch, center2d,
                        diameter, tm_state.CONFIG['bottom_radius_size']
                    )
                    if result:
                        log(f"Bottom radius added ({tm_state.CONFIG['bottom_radius_size']}mm)")
                    else:
                        log("Bottom edge not found, skipping bottom radius")

                successCount += 1
                log(f"SUCCESS: Point {point_idx + 1} completed")

            if successCount > 0 and timeline is not None and startIndex >= 0:
                try:
                    endIndex = timeline.markerPosition - 1
                    if endIndex >= startIndex:
                        timelineGroup = timeline.timelineGroups.add(startIndex, endIndex)
                        timelineGroup.name = f'({successCount}x {insertName})'
                        log(f"Timeline group created: ({successCount}x {insertName})")
                except Exception:
                    log("Timeline grouping failed (non-parametric mode?)")

            log(f"\n=== COMMAND EXECUTE END ===")
            log(f"Results: {successCount} successful, {failedCount} failed")

            if failedCount > 0:
                tm_state._ui.messageBox(
                    f'Created {successCount} insert hole(s).\n{failedCount} failed (no intersection with target body).'
                )
            elif showMessage:
                tm_state._ui.messageBox(f'Successfully created {successCount} insert hole(s).')

        except Exception:
            log(f"FATAL ERROR: {traceback.format_exc()}")
            tm_state._ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
