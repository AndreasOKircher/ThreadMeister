"""
tm_ui.py – UI event handlers and dialog helper.

Handles CommandCreated, InputChanged, ValidateInputs events and
the updateInfoText helper that refreshes the info text box.
"""
import adsk.core, adsk.fusion, traceback
from . import tm_state
from . import tm_config
from . import tm_ridge
from .tm_helpers import calc_blind_hole_depth_mm
from .tm_execute import CommandExecuteHandler


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            # Reload config to pick up any saved changes
            tm_config.load_config()

            cmd = args.command

            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            tm_state._handlers.append(onExecute)

            onInputChanged = InputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            tm_state._handlers.append(onInputChanged)

            onValidateInputs = ValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            tm_state._handlers.append(onValidateInputs)

            inputs = cmd.commandInputs

            # Target body selection
            bodySelect = inputs.addSelectionInput('bodySelect', 'Select Target Body',
                                                  'Select the body to add insert holes to')
            bodySelect.addSelectionFilter('SolidBodies')
            bodySelect.setSelectionLimits(1, 1)

            # Sketch point selection
            pointSelect = inputs.addSelectionInput('pointSelect', 'Select Sketch Point(s)',
                                                   'Select line endpoint')
            pointSelect.addSelectionFilter('SketchPoints')
            pointSelect.setSelectionLimits(1, 0)

            # Bore Type dropdown (Heat-Set Insert / Ridge Thread)
            isRidge = tm_state.CONFIG.get('last_bore_type') == tm_ridge.BORE_TYPE_RIDGE
            boreTypeDropdown = inputs.addDropDownCommandInput('boreType', 'Bore Type',
                                                             adsk.core.DropDownStyles.TextListDropDownStyle)
            boreTypeDropdown.listItems.add(tm_ridge.BORE_TYPE_INSERT, not isRidge)
            boreTypeDropdown.listItems.add(tm_ridge.BORE_TYPE_RIDGE, isRidge)

            # Insert size dropdown (Insert Specs, or Ridge Thread sizes)
            insertDropdown = inputs.addDropDownCommandInput('insertSize', 'Insert Size',
                                                           adsk.core.DropDownStyles.TextListDropDownStyle)
            fillSizeDropdown(insertDropdown, isRidge)

            # Hole type
            holeTypeGroup = inputs.addRadioButtonGroupCommandInput('holeType', 'Hole Type')
            saved_is_blind = tm_state.CONFIG.get('hole_type_blind', True)
            holeTypeGroup.listItems.add('Blind Hole', saved_is_blind)
            holeTypeGroup.listItems.add('Through Hole', not saved_is_blind)

            # Ridge Thread depth (blind only); value in cm, shown in mm
            inputs.addValueInput('ridgeDepth', 'Depth', 'mm',
                                 adsk.core.ValueInput.createByReal(0.0))
            resetRidgeDepth(inputs)

            # Chamfer option
            inputs.addBoolValueInput('addChamfer',
                                     f'Add Chamfer ({tm_state.CONFIG["chamfer_size"]}mm)',
                                     True, '',
                                     tm_state.CONFIG['chamfer_enabled_default'])

            # Bottom radius option
            inputs.addBoolValueInput('addBottomRadius',
                                     f'Add Fillet Bottom ({tm_state.CONFIG["bottom_radius_size"]}mm)',
                                     True, '',
                                     tm_state.CONFIG['bottom_radius_enabled_default'])

            # Show success message option
            inputs.addBoolValueInput('showSuccessMessage',
                                     'Show Success Message',
                                     True, '',
                                     tm_state.CONFIG['show_success_message'])

            # Debug export button — only visible when enabled in config.ini
            if tm_state.CONFIG.get('enable_debug_export', False):
                inputs.addBoolValueInput('exportDebug',
                                        'Export Debug JSON (saves fixture to debug_exports/)',
                                        True, '',
                                        False)

            # Info text
            inputs.addTextBoxCommandInput('infoText', '', '', 4, True)
            applyBoreTypeVisibility(inputs)
            updateInfoText(inputs)

        except Exception:
            tm_state._ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inputs = args.inputs
            changedInput = args.input

            # Auto-focus on point selection after body is selected
            if changedInput.id == 'bodySelect':
                bodySelect = inputs.itemById('bodySelect')
                if bodySelect.selectionCount > 0:
                    pointSelect = inputs.itemById('pointSelect')
                    pointSelect.isEnabled = True
                    pointSelect.hasFocus = True

            if changedInput.id == 'boreType':
                fillSizeDropdown(inputs.itemById('insertSize'), isRidgeSelected(inputs))
            if changedInput.id in ('boreType', 'insertSize'):
                resetRidgeDepth(inputs)
            if changedInput.id in ('boreType', 'holeType'):
                applyBoreTypeVisibility(inputs)

            if changedInput.id in ('boreType', 'insertSize', 'holeType', 'addChamfer', 'ridgeDepth'):
                updateInfoText(inputs)

        except Exception:
            tm_state._ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class ValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        try:
            inputs = args.inputs
            bodySelect = inputs.itemById('bodySelect')
            pointSelect = inputs.itemById('pointSelect')

            if bodySelect.selectionCount == 0 or pointSelect.selectionCount == 0:
                args.areInputsValid = False
            elif (isRidgeSelected(inputs)
                  and inputs.itemById('holeType').selectedItem.name == 'Blind Hole'
                  and inputs.itemById('ridgeDepth').value <= 0):
                args.areInputsValid = False
            else:
                args.areInputsValid = True

        except Exception:
            tm_state._ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def isRidgeSelected(inputs):
    """True when the Bore Type dropdown is on Ridge Thread."""
    boreType = inputs.itemById('boreType')
    return boreType.selectedItem.name == tm_ridge.BORE_TYPE_RIDGE


def fillSizeDropdown(dropdown, isRidge):
    """Fill the size dropdown with Insert Specs or Ridge Thread sizes; reselect the last one."""
    listItems = dropdown.listItems
    listItems.clear()
    if isRidge:
        names = list(tm_state.RIDGE_THREAD_SPECS.keys())
        lastSelected = tm_state.CONFIG.get('last_ridge_thread', 'M3')
    else:
        names = list(tm_state.INSERT_SPECS.keys())
        lastSelected = tm_state.CONFIG.get('last_selected_insert', 'M3 x 5.7mm (standard)')
    found = False
    for name in names:
        isSelected = (name == lastSelected)
        found = found or isSelected
        listItems.add(name, isSelected)
    if not found and listItems.count > 0:
        listItems.item(0).isSelected = True


def resetRidgeDepth(inputs):
    """Set the Ridge Thread depth to the size's default (4 x D). Not remembered."""
    if not isRidgeSelected(inputs):
        return
    size = inputs.itemById('insertSize').selectedItem.name
    g = tm_ridge.ridge_geometry(size, tm_state.RIDGE_THREAD_SPECS[size])
    inputs.itemById('ridgeDepth').value = g.default_depth / 10.0   # mm -> cm


def applyBoreTypeVisibility(inputs):
    """Ridge Thread: show Depth (blind only), hide Chamfer and Bottom Radius."""
    isRidge = isRidgeSelected(inputs)
    isBlind = inputs.itemById('holeType').selectedItem.name == 'Blind Hole'
    inputs.itemById('ridgeDepth').isVisible = isRidge and isBlind
    inputs.itemById('addChamfer').isVisible = not isRidge
    inputs.itemById('addBottomRadius').isVisible = not isRidge


def _ridgeInfoText(inputs, isBlindHole):
    size = inputs.itemById('insertSize').selectedItem.name
    inner = tm_state.RIDGE_THREAD_SPECS[size]
    g = tm_ridge.ridge_geometry(size, inner)
    if isBlindHole:
        depthStr = f'{inputs.itemById("ridgeDepth").value * 10.0:.1f} mm'
    else:
        depthStr = 'Through body'
    return (f'<b>Ridge Thread {size}:</b><br/>' +
            f'Bore diameter: {g.bore_dia} mm<br/>' +
            f'Inner diameter at ridges: {inner} mm ({g.count} ridges)<br/>' +
            f'Hole depth: {depthStr}')


def updateInfoText(inputs):
    """Refresh the info text box with specs for the currently selected insert."""
    try:
        insertSize = inputs.itemById('insertSize')
        holeType = inputs.itemById('holeType')
        infoText = inputs.itemById('infoText')

        insertName = insertSize.selectedItem.name
        isBlindHole = holeType.selectedItem.name == 'Blind Hole'

        if isRidgeSelected(inputs):
            infoText.formattedText = _ridgeInfoText(inputs, isBlindHole)
            return

        holeDia, insertLen, minWall = tm_state.INSERT_SPECS[insertName]

        addChamfer = inputs.itemById('addChamfer')
        chamferOn = addChamfer.value if addChamfer else False

        if isBlindHole:
            extra = tm_state.CONFIG['blind_hole_extra_depth']
            chamfer = tm_state.CONFIG['chamfer_size'] if chamferOn else 0.0
            holeDepth = calc_blind_hole_depth_mm(insertLen, extra, chamfer)
            if chamferOn:
                depthStr = f'{holeDepth:.1f} mm ({insertLen} + {extra} extra + {tm_state.CONFIG["chamfer_size"]} chamfer)'
            else:
                depthStr = f'{holeDepth:.1f} mm ({insertLen} + {extra} extra)'
        else:
            depthStr = 'Through body'

        info = (f'<b>Specifications:</b><br/>' +
                f'Hole diameter: {holeDia} mm<br/>' +
                f'Insert length: {insertLen} mm<br/>' +
                f'Hole depth: {depthStr}<br/>' +
                f'Min wall thickness: {minWall} mm')

        infoText.formattedText = info

    except Exception:
        pass
