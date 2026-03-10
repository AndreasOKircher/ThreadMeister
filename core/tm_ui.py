"""
tm_ui.py – UI event handlers and dialog helper.

Handles CommandCreated, InputChanged, ValidateInputs events and
the updateInfoText helper that refreshes the info text box.
"""
import adsk.core, adsk.fusion, traceback
import tm_state
import tm_config
from tm_execute import CommandExecuteHandler


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

            # Insert size dropdown
            insertDropdown = inputs.addDropDownCommandInput('insertSize', 'Insert Size',
                                                           adsk.core.DropDownStyles.TextListDropDownStyle)
            insertList = insertDropdown.listItems

            lastSelected = tm_state.CONFIG.get('last_selected_insert', 'M3 x 5.7mm (standard)')
            foundLastSelected = False
            for name in tm_state.INSERT_SPECS.keys():
                isSelected = (name == lastSelected)
                if isSelected:
                    foundLastSelected = True
                insertList.add(name, isSelected)

            if not foundLastSelected and insertList.count > 0:
                insertList.item(0).isSelected = True

            # Hole type
            holeTypeGroup = inputs.addRadioButtonGroupCommandInput('holeType', 'Hole Type')
            saved_is_blind = tm_state.CONFIG.get('hole_type_blind', True)
            holeTypeGroup.listItems.add('Blind Hole', saved_is_blind)
            holeTypeGroup.listItems.add('Through Hole', not saved_is_blind)

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

            # Info text
            inputs.addTextBoxCommandInput('infoText', '', '', 4, True)
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

            if changedInput.id == 'insertSize' or changedInput.id == 'holeType':
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
            else:
                args.areInputsValid = True

        except Exception:
            tm_state._ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def updateInfoText(inputs):
    """Refresh the info text box with specs for the currently selected insert."""
    try:
        insertSize = inputs.itemById('insertSize')
        holeType = inputs.itemById('holeType')
        infoText = inputs.itemById('infoText')

        insertName = insertSize.selectedItem.name
        isBlindHole = holeType.selectedItem.name == 'Blind Hole'

        holeDia, insertLen, minWall = tm_state.INSERT_SPECS[insertName]

        if isBlindHole:
            holeDepth = insertLen + tm_state.CONFIG['blind_hole_extra_depth']
            holeTypeStr = 'Blind hole'
        else:
            holeDepth = 'Through body'
            holeTypeStr = 'Through hole'

        info = (f'<b>Specifications:</b><br/>' +
                f'Hole diameter: {holeDia} mm<br/>' +
                f'Insert length: {insertLen} mm<br/>' +
                f'Hole depth: {holeDepth}<br/>' +
                f'Min wall thickness: {minWall} mm')

        infoText.formattedText = info

    except Exception:
        pass
