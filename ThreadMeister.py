"""
ThreadMeister – Heat-set Insert Creator for Fusion 360
Copyright (c) 2026 Andreas Kircher

SPDX-License-Identifier: MIT

This add-in automates the creation of heat-set insert holes for 3D printing,
using the dimensional specifications from CNC Kitchen.

Author: Andreas Kircher (Andreas.O.Kircher@gmail.com)
Created with assistance from: Claude (Anthropic) / Perplexity
Insert specifications from: CNC Kitchen (cnckitchen.com)
Version: 1.1.0b

Features:
- Creates heat-set insert holes at sketch points
- Hole creation with CNC Kitchen specifications (M2-M10, 1/4"-20) – customizable via config.ini
- Blind holes and through holes
- Automatic chamfer for easier insert installation
- Automatic bottom radius for blind holes
- Timeline grouping for easy management
- Direct subtraction from target body

Usage:
1. Create a sketch with points where you want insert holes
2. Click "ThreadMeister" button in SOLID > MODIFY menu
3. Select target body and sketch points
4. Choose insert size and options
5. Done!

Known Issues:
- Not tested with Apple macOS
- Overlapping bores may cause incomplete extrusions (no chamfer/radius)
- Complex sketches with many elements near the bore may cause wrong profile selection
  (more than 15 profiles within the bore circle)
"""
import traceback
import os
import sys

# Add the add-in directory to sys.path so local modules are importable
_addin_path = os.path.dirname(os.path.realpath(__file__))
if _addin_path not in sys.path:
    sys.path.insert(0, _addin_path)

# Add the core subdirectory to sys.path for module imports
_core_path = os.path.join(_addin_path, 'core')
if _core_path not in sys.path:
    sys.path.insert(0, _core_path)

import tm_state
import tm_config
from tm_ui import CommandCreatedHandler


def run(context):
    """Called when the add-in is loaded."""
    try:
        tm_config.load_config()

        cmdDefs = tm_state._ui.commandDefinitions
        addon_path = os.path.dirname(os.path.realpath(__file__))
        resources_path = os.path.join(addon_path, 'resources', 'icons')

        buttonDef = cmdDefs.addButtonDefinition(
            tm_state.CMD_ID,
            tm_state.CMD_NAME,
            tm_state.CMD_Description,
            resources_path
        )

        onCommandCreated = CommandCreatedHandler()
        buttonDef.commandCreated.add(onCommandCreated)
        tm_state._handlers.append(onCommandCreated)

        panel = tm_state._ui.allToolbarPanels.itemById(tm_state.PANEL_ID)
        if panel:
            buttonControl = panel.controls.addCommand(buttonDef)
            buttonControl.isPromoted = True
            buttonControl.isPromotedByDefault = True
        else:
            tm_state._ui.messageBox(f'Could not find panel: {tm_state.PANEL_ID}')

    except Exception:
        tm_state._ui.messageBox('Failed to load add-in:\n{}'.format(traceback.format_exc()))


def stop(context):
    """Called when the add-in is unloaded."""
    try:
        cmdDef = tm_state._ui.commandDefinitions.itemById(tm_state.CMD_ID)
        if cmdDef:
            cmdDef.deleteMe()

        panel = tm_state._ui.allToolbarPanels.itemById(tm_state.PANEL_ID)
        if panel:
            control = panel.controls.itemById(tm_state.CMD_ID)
            if control:
                control.deleteMe()
    except Exception:
        tm_state._ui.messageBox('Failed to stop add-in:\n{}'.format(traceback.format_exc()))
