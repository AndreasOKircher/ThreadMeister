"""
ThreadMeister – Heat-set Insert Creator for Fusion 360
Copyright (C) 2026  Andreas Kircher

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: GPL-3.0-or-later

Melt Insert Creator - Add-in for Fusion 360

This add-in automates the creation of heat-set insert holes for 3D printing,
using the dimensional specifications from CNC Kitchen.

Author: [Andreas Kircher, Andreas.O.Kircher@gmail.com]

Created with assistance from: Claude (Anthropic) / Perplexity
Insert specifications from: CNC Kitchen (cnckitchen.com)
Version: 1.0
Date: February 2026

Features:
- Creates heat-set insert holes at sketch points (including constrain to the sketch point for easy updates)
- Hole creation with CNC Kitchen specifications (M2-M10, 1/4"-20) - can be customized via config.ini
- Blind holes and through holes
- Automatic chamfer for easier insert installation (can be toggled on/off)
- Automatic bottom radius option for blind holes (can be toggled on/off)
- Timeline grouping for easy management
- Direct subtraction from target body


Usage:
1. Create a sketch with points where you want insert holes
2. Click "Melt Insert Creator" button in SOLID > MODIFY menu
3. Select target body and sketch points
4. Choose insert size and options
5. Done!


Known Issues:
-  Not tested with Apple macOS 
-  If insert holes are created too close and overlapping bore will be created, incomplete bores created - (no chamfer no radius)
-  Placing into complex geomerties sketches with many sketch elements might cause wrong profile selection or failed extrusions (more than 15 profiles with in circle of insert bore)

"""
import adsk.core, adsk.fusion, traceback
import os
import configparser
import math 

# Global configuration
TOL = 1e-6
INSERT_SPECS = {}
CONFIG = {
    'chamfer_size': 0.5,
    'blind_hole_extra_depth': 1.0,
    'chamfer_enabled_default': True,
    'bottom_radius_size': 0.5,
    'bottom_radius_enabled_default': False,
    'show_success_message': True,
    'enable_logging': False  # Neu hinzugefügt
}

def load_config():
    """Load configuration from INI file with error checking"""
    global INSERT_SPECS, CONFIG
    
    # Get the add-in directory
    addon_path = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(addon_path, 'config.ini')
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_file):
        create_default_config()
    
    errors = []
    warnings = []
    
    # Load config
    try:
        config = configparser.RawConfigParser()
        # Preserve case in option names
        config.optionxform = str
        config.read(config_file, encoding='utf-8')
        
        # Load settings with validation
        if config.has_section('Settings'):
            try:
                chamfer = config.getfloat('Settings', 'chamfer_size', fallback=0.5)
                if chamfer <= 0 or chamfer > 5.0:
                    warnings.append(f'Chamfer size {chamfer}mm is unusual (expected 0-5mm). Using default 0.5mm.')
                    chamfer = 0.5
                CONFIG['chamfer_size'] = chamfer
            except ValueError:
                warnings.append('Invalid chamfer_size value. Using default 0.5mm.')
                CONFIG['chamfer_size'] = 0.5
            
            try:
                extra_depth = config.getfloat('Settings', 'blind_hole_extra_depth', fallback=1.0)
                if extra_depth < 0 or extra_depth > 10.0:
                    warnings.append(f'Extra depth {extra_depth}mm is unusual (expected 0-10mm). Using default 1.0mm.')
                    extra_depth = 1.0
                CONFIG['blind_hole_extra_depth'] = extra_depth
            except ValueError:
                warnings.append('Invalid blind_hole_extra_depth value. Using default 1.0mm.')
                CONFIG['blind_hole_extra_depth'] = 1.0
            
            try:
                CONFIG['chamfer_enabled_default'] = config.getboolean('Settings', 'chamfer_enabled_default', fallback=True)
            except ValueError:
                warnings.append('Invalid chamfer_enabled_default value. Using default True.')
                CONFIG['chamfer_enabled_default'] = True
            
            try:
                bottom_radius = config.getfloat('Settings', 'bottom_radius_size', fallback=0.5)
                if bottom_radius < 0 or bottom_radius > 5.0:
                    warnings.append(f'Bottom radius {bottom_radius}mm is unusual (expected 0-5mm). Using default 0.5mm.')
                    bottom_radius = 0.5
                CONFIG['bottom_radius_size'] = bottom_radius
            except ValueError:
                warnings.append('Invalid bottom_radius_size value. Using default 0.5mm.')
                CONFIG['bottom_radius_size'] = 0.5
            
            try:
                CONFIG['bottom_radius_enabled_default'] = config.getboolean('Settings', 'bottom_radius_enabled_default', fallback=False)
            except ValueError:
                warnings.append('Invalid bottom_radius_enabled_default value. Using default False.')
                CONFIG['bottom_radius_enabled_default'] = False
             
            try:
                CONFIG['show_success_message'] = config.getboolean('Settings', 'show_success_message', fallback=True)
            except ValueError:
                warnings.append('Invalid show_success_message value. Using default True.')
                CONFIG['show_success_message'] = True
            
            try:
                CONFIG['hole_type_blind'] = config.getboolean('Settings', 'hole_type_blind', fallback=True)
            except ValueError:
                CONFIG['hole_type_blind'] = True
            
            try:
                CONFIG['enable_logging'] = config.getboolean('Settings', 'enable_logging', fallback=False)
            except ValueError:
                CONFIG['enable_logging'] = False
            
            # Load last selected insert
            try:
                CONFIG['last_selected_insert'] = config.get('Settings', 'last_selected_insert', fallback='M3 x 5.7mm (standard)')
            except:
                CONFIG['last_selected_insert'] = 'M3 x 5.7mm (standard)'
        
        # Load inserts with validation
        INSERT_SPECS.clear()
        if config.has_section('Inserts'):
            for name in config.options('Inserts'):
                # Skip comments
                if name.startswith('#'):
                    continue
                    
                try:
                    values = config.get('Inserts', name)
                    
                    # Skip empty or comment lines
                    if not values.strip() or values.strip().startswith('#'):
                        continue
                    
                    parts = [x.strip() for x in values.split(',')]
                    
                    if len(parts) != 3:
                        warnings.append(f'Insert "{name}" has {len(parts)} values (expected 3). Skipped.')
                        continue
                    
                    # Convert to floats and validate
                    try:
                        hole_dia = float(parts[0])
                        insert_len = float(parts[1])
                        min_wall = float(parts[2])
                        
                        # Validate ranges
                        if hole_dia <= 0 or hole_dia > 50:
                            warnings.append(f'Insert "{name}": hole diameter {hole_dia}mm is invalid. Skipped.')
                            continue
                        
                        if insert_len <= 0 or insert_len > 100:
                            warnings.append(f'Insert "{name}": insert length {insert_len}mm is invalid. Skipped.')
                            continue
                        
                        if min_wall < 0 or min_wall > 20:
                            warnings.append(f'Insert "{name}": min wall {min_wall}mm is invalid. Skipped.')
                            continue
                        
                        # Add valid insert
                        INSERT_SPECS[name] = (hole_dia, insert_len, min_wall)
                        
                    except ValueError as e:
                        warnings.append(f'Insert "{name}": Invalid number format. Skipped.')
                        continue
                        
                except Exception as e:
                    warnings.append(f'Insert "{name}": Error reading values. Skipped.')
                    continue
        
        # If no valid inserts loaded, use defaults
        if not INSERT_SPECS:
            errors.append('No valid inserts found in config.ini!')
            INSERT_SPECS = get_default_inserts()
            warnings.append('Using default CNC Kitchen specifications.')
        
        # Show warnings/errors if any
        if errors or warnings:
            msg = ''
            if errors:
                msg += 'ERRORS:\n' + '\n'.join(errors) + '\n\n'
            if warnings:
                msg += 'WARNINGS:\n' + '\n'.join(warnings)
            
            if _ui:
                _ui.messageBox(f'Config.ini issues:\n\n{msg}')
                        
    except Exception as e:
        if _ui:
            _ui.messageBox(f'Error loading config.ini: {str(e)}\nUsing default specifications.')
        INSERT_SPECS = get_default_inserts()
    
    return INSERT_SPECS, CONFIG


def save_last_selected_insert(insert_name):
    """Save the last selected insert to config.ini"""
    try:
        addon_path = os.path.dirname(os.path.realpath(__file__))
        config_file = os.path.join(addon_path, 'config.ini')
        
        config = configparser.RawConfigParser()
        # Preserve case in option names
        config.optionxform = str
        config.read(config_file, encoding='utf-8')
        
        # Ensure Settings section exists
        if not config.has_section('Settings'):
            config.add_section('Settings')
        
        # Update last selected insert
        config.set('Settings', 'last_selected_insert', insert_name)
        
        # Write back to file
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
    except:
        pass  # Silently fail if we can't save

def save_checkbox_states(chamfer_state, radius_state, show_message_state, is_blind_hole):
    """Save checkbox states and hole type to config.ini"""
    try:
        addon_path = os.path.dirname(os.path.realpath(__file__))
        config_file = os.path.join(addon_path, 'config.ini')
        
        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(config_file, encoding='utf-8')
        
        if not config.has_section('Settings'):
            config.add_section('Settings')
        
        # Update checkbox states
        config.set('Settings', 'chamfer_enabled_default', str(chamfer_state))
        config.set('Settings', 'bottom_radius_enabled_default', str(radius_state))
        config.set('Settings', 'show_success_message', str(show_message_state))
        config.set('Settings', 'hole_type_blind', str(is_blind_hole))
        
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
    except:
        pass

def get_default_inserts():
    """Get default CNC Kitchen insert specifications"""
    return {
        'M2 x 3mm': (3.2, 3.0, 1.5),
        'M2.5 x 4mm': (4.0, 4.0, 1.5),
        'M3 x 3mm (short)': (4.4, 3.0, 1.6),
        'M3 x 4mm (short)': (4.4, 4.0, 1.6),
        'M3 x 5.7mm (standard)': (4.4, 5.7, 1.6),
        'M4 x 4mm (short)': (5.6, 4.0, 2.0),
        'M4 x 8.1mm (standard)': (5.6, 8.1, 2.0),
        'M5 x 5.8mm (short)': (6.4, 5.8, 2.5),
        'M5 x 9.5mm (standard)': (6.4, 9.5, 2.5),
        'M6 x 12.7mm': (8.0, 12.7, 3.0),
        'M8 x 12.7mm': (9.7, 12.7, 4.0),
        'M10 x 12.7mm': (12.0, 12.7, 5.0),
        '1/4"-20 x 12.7mm (camera)': (8.0, 12.7, 3.0)
    }

def create_default_config():
    """Create a default config.ini file"""
    addon_path = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(addon_path, 'config.ini')
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('[Settings]\n')
            f.write('# Default chamfer size in mm\n')
            f.write('chamfer_size = 0.5\n')
            f.write('\n')
            f.write('# Extra depth added to blind holes in mm (recommended: 1.0mm)\n')
            f.write('blind_hole_extra_depth = 1.0\n')
            f.write('\n')
            f.write('# Default chamfer checkbox state (True or False)\n')
            f.write('chamfer_enabled_default = True\n')
            f.write('\n')
            f.write('# Bottom radius size for blind holes in mm (for rounding the bottom edge)\n')
            f.write('bottom_radius_size = 0.5\n')
            f.write('\n')
            f.write('# Default bottom radius checkbox state (True or False)\n')
            f.write('bottom_radius_enabled_default = False\n')
            f.write('\n')
            f.write('# Show success message after operation (True or False)\n')
            f.write('show_success_message = True\n')
            f.write('\n')
            f.write('# Last selected insert (will be remembered between sessions)\n')
            f.write('last_selected_insert = M3 x 5.7mm (standard)\n')
            f.write('\n\n')
            f.write('[Inserts]\n')
            
            # Write all default inserts
            default_inserts = get_default_inserts()
            for name, (dia, length, wall) in default_inserts.items():
                f.write(f'{name} = {dia}, {length}, {wall}\n')
            
            f.write('\n')
            f.write('# Add your custom inserts below:\n')
            f.write('# My Custom M3 = 4.5, 6.0, 1.6\n')
            f.write('# My Custom M4 = 5.7, 9.0, 2.0\n')
            
    except Exception as e:
        if _ui:
            _ui.messageBox(f'Could not create config.ini: {str(e)}')

# Initialize (will be loaded in run())
INSERT_SPECS = {
    'M2 x 3mm': (3.2, 3.0, 1.5),
    'M2.5 x 4mm': (4.0, 4.0, 1.5),
    'M3 x 3mm (short)': (4.4, 3.0, 1.6),
    'M3 x 4mm (short)': (4.4, 4.0, 1.6),
    'M3 x 5.7mm (standard)': (4.4, 5.7, 1.6),
    'M4 x 4mm (short)': (5.6, 4.0, 2.0),
    'M4 x 8.1mm (standard)': (5.6, 8.1, 2.0),
    'M5 x 5.8mm (short)': (6.4, 5.8, 2.5),
    'M5 x 9.5mm (standard)': (6.4, 9.5, 2.5),
    'M6 x 12.7mm': (8.0, 12.7, 3.0),
    'M8 x 12.7mm': (9.7, 12.7, 4.0),
    'M10 x 12.7mm': (12.0, 12.7, 5.0),
    '1/4"-20 x 12.7mm (camera)': (8.0, 12.7, 3.0)
}

# Global list to keep all event handlers in scope
_handlers = []
_app = adsk.core.Application.get()
_ui = _app.userInterface

# Unique command ID
CMD_ID = 'ThreadMeisterCmd'
CMD_NAME = 'ThreadMeister'
CMD_Description = 'Create heat-set insert holes with CNC Kitchen specifications'

# Panel to add the button to
PANEL_ID = 'SolidModifyPanel'  # MODIFY panel in SOLID workspace

def run(context):
    """Called when the add-in is loaded"""
    try:
        # Load configuration from INI file (creates default if doesn't exist)
        load_config()
        
        # Get the command definitions collection
        cmdDefs = _ui.commandDefinitions

        # Get the path to the resources folder
        addon_path = os.path.dirname(os.path.realpath(__file__))
        resources_path = os.path.join(addon_path, 'resources', 'icons')  # Assuming icon.png is in resources/icon/
        
        # Create a button command definition with icon
        buttonDef = cmdDefs.addButtonDefinition(
            CMD_ID,
            CMD_NAME,
            CMD_Description,
            resources_path
        )

        # Connect to the commandCreated event
        onCommandCreated = CommandCreatedHandler()
        buttonDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)
        
        # Get the MODIFY panel in the SOLID workspace
        panel = _ui.allToolbarPanels.itemById(PANEL_ID)
        
        if panel:
            # Add the button to the panel
            buttonControl = panel.controls.addCommand(buttonDef)
            # Make the button visible in the panel
            buttonControl.isPromoted = True
            buttonControl.isPromotedByDefault = True
        else:
            _ui.messageBox(f'Could not find panel: {PANEL_ID}')
        
    except:
        _ui.messageBox('Failed to load add-in:\n{}'.format(traceback.format_exc()))

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            # Reload config to get the latest saved selection
            load_config()

            cmd = args.command
            
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)
            
            onInputChanged = InputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)
            
            onValidateInputs = ValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)
            
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
            
            # Get last selected insert from config
            lastSelected = CONFIG.get('last_selected_insert', 'M3 x 5.7mm (standard)')
            
            # Add all inserts and mark which one should be selected
            foundLastSelected = False
            for i, name in enumerate(INSERT_SPECS.keys()):
                # Select the item as we add it if it matches the last selected
                isSelected = (name == lastSelected)
                if isSelected:
                    foundLastSelected = True
                insertList.add(name, isSelected)
            
            # If last selected wasn't found, select the first item as fallback
            if not foundLastSelected and insertList.count > 0:
                insertList.item(0).isSelected = True
            
            # Hole type
            holeTypeGroup = inputs.addRadioButtonGroupCommandInput('holeType', 'Hole Type')
            saved_is_blind = CONFIG.get('hole_type_blind', True)
            holeTypeGroup.listItems.add('Blind Hole', saved_is_blind)
            holeTypeGroup.listItems.add('Through Hole', not saved_is_blind)
            
            # Chamfer option - use default from config
            chamferCheck = inputs.addBoolValueInput('addChamfer', 
                                                     f'Add Chamfer ({CONFIG["chamfer_size"]}mm)', 
                                                     True, '', 
                                                     CONFIG['chamfer_enabled_default'])
            
            # Bottom radius option for blind holes - use default from config
            bottomRadiusCheck = inputs.addBoolValueInput('addBottomRadius', 
                                                         f'Add Fillet Bottom ({CONFIG["bottom_radius_size"]}mm)', 
                                                         True, '', 
                                                         CONFIG['bottom_radius_enabled_default'])
            # Show success message option - use default from config
            showMessageCheck = inputs.addBoolValueInput('showSuccessMessage', 
                                                        'Show Success Message', 
                                                        True, '', 
                                                        CONFIG['show_success_message'])                       
            
            # Info text
            infoText = inputs.addTextBoxCommandInput('infoText', '', '', 4, True)
            updateInfoText(inputs)
            
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

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
                
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

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
                
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



def findProfileForCircle(sketch, target_circle):
    """
    Find all profiles that make up the area inside the target circle.
    
    Strategy:
    1. Coarse filters to reduce candidates (fast, permissive)
       - Area: not larger than circle
       - Centroid: inside circle  
       - BBox: roughly within circle area (generous margin)
    2. Precise area-matching to find exact combination (slow, accurate)
    
    Returns:
        Profile, ObjectCollection of profiles, or None if validation fails.
    """

    if target_circle.parentSketch != sketch:
        log("findProfileForCircle: target_circle is not in given sketch")
        return None

    circle_center3d = target_circle.centerSketchPoint.geometry
    circle_radius = target_circle.radius
    target_area = target_circle.area

    log("=== findProfileForCircle START ===")
    log(f"Circle: center ({circle_center3d.x:.4f}, {circle_center3d.y:.4f}), radius={circle_radius:.6f}, area={target_area:.6f}")
    log(f"Total profiles in sketch: {sketch.profiles.count}")

    # Coarse bounding box with generous margin
    bbox_margin = circle_radius * 1.0
    circle_bbox_min_x = circle_center3d.x - circle_radius - bbox_margin
    circle_bbox_max_x = circle_center3d.x + circle_radius + bbox_margin
    circle_bbox_min_y = circle_center3d.y - circle_radius - bbox_margin
    circle_bbox_max_y = circle_center3d.y + circle_radius + bbox_margin
    
    log(f"Circle bbox (with {bbox_margin:.4f} margin): ({circle_bbox_min_x:.4f}, {circle_bbox_min_y:.4f}) to ({circle_bbox_max_x:.4f}, {circle_bbox_max_y:.4f})")

    candidates = []

    for idx, prof in enumerate(sketch.profiles):
        props = prof.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy)
        
        # COARSE FILTER 1: Area
        if props.area > target_area * 1.01:
            log(f"Profile {idx}: REJECTED - area {props.area:.6f} > circle area {target_area:.6f}")
            continue
        
        # COARSE FILTER 2: Centroid
        centroid3d = props.centroid
        distance = circle_center3d.distanceTo(centroid3d)
        
        if distance > circle_radius:
            log(f"Profile {idx}: REJECTED - centroid outside (dist={distance:.6f} > radius={circle_radius:.6f})")
            continue
        
        # COARSE FILTER 3: BBox
        prof_bbox = prof.boundingBox
        is_contained = (
            prof_bbox.minPoint.x >= circle_bbox_min_x and
            prof_bbox.maxPoint.x <= circle_bbox_max_x and
            prof_bbox.minPoint.y >= circle_bbox_min_y and
            prof_bbox.maxPoint.y <= circle_bbox_max_y
        )
        
        if not is_contained:
            log(f"Profile {idx}: REJECTED - bbox way outside")
            log(f"  Profile bbox: ({prof_bbox.minPoint.x:.4f}, {prof_bbox.minPoint.y:.4f}) to ({prof_bbox.maxPoint.x:.4f}, {prof_bbox.maxPoint.y:.4f})")
            continue

        log(f"Profile {idx}: CANDIDATE - area={props.area:.6f}, centroid dist={distance:.6f}")
        candidates.append((prof, props.area, distance))

    if not candidates:
        log("No candidates found after filtering")
        log("=== findProfileForCircle END (no candidates) ===")
        return None

    log(f"Total candidates after filtering: {len(candidates)}")

    # PRECISE AREA MATCHING
    from itertools import combinations
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    best_profiles = None
    best_difference = float('inf')
    max_profiles = min(len(candidates), 15)
    
    log(f"Starting combination search (max {max_profiles} profiles)...")
    
    for r in range(1, max_profiles + 1):
        combinations_tried = 0
        for combo in combinations(candidates, r):
            combo_area = sum(item[1] for item in combo)
            difference = abs(combo_area - target_area)
            combinations_tried += 1
            
            if difference < best_difference:
                best_difference = difference
                best_profiles = [item[0] for item in combo]
                log(f"  New best: {r} profiles, area={combo_area:.6f}, diff={difference:.6f}")
            
            # Early exit for near-perfect match
            if best_difference <= target_area * 0.00003:
                log(f"  Found near-perfect match! Stopping early.")
                break
        
        log(f"  Tried {combinations_tried} combinations of size {r}")
        
        if best_difference <= target_area * 0.00003:
            break
    
    tolerance = target_area * 0.03
    log(f"Best match: {len(best_profiles)} profiles, area diff={best_difference:.6f}, tolerance={tolerance:.6f}")
    
    if best_difference > tolerance:
        log("No valid combination found within tolerance")
        log("=== findProfileForCircle END (no valid combination) ===")
        return None

    log(f"SUCCESS: Returning {len(best_profiles)} profile(s)")
    log("=== findProfileForCircle END (success) ===")
    
    if len(best_profiles) == 1:
        return best_profiles[0]
    
    coll = adsk.core.ObjectCollection.create()
    for prof in best_profiles:
        coll.add(prof)
    return coll

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            # Clear log at the very start
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

            targetBody = bodySelect.selection(0).entity
            selectedPoints = []
            for i in range(pointSelect.selectionCount):
                selectedPoints.append(pointSelect.selection(i).entity)

            insertName = insertSize.selectedItem.name
            save_last_selected_insert(insertName)
            
            isBlindHole = holeType.selectedItem.name == 'Blind Hole'
            includeChamfer = addChamfer.value
            includeBottomRadius = addBottomRadius.value and isBlindHole
            showMessage = showSuccessMessage.value

            save_checkbox_states(includeChamfer, includeBottomRadius, showMessage, isBlindHole)

            holeDia, insertLen, minWall = INSERT_SPECS[insertName]
            radius = holeDia / 2.0
            radius /= 10.0
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
                    holeDepth = (insertLen + CONFIG['blind_hole_extra_depth']) / 10.0
                    log(f"Blind hole depth: {holeDepth:.4f}cm")
                    distance = adsk.core.ValueInput.createByReal(holeDepth)
                    extent = adsk.fusion.DistanceExtentDefinition.create(distance)
                    extInput.setOneSideExtent(extent, direction)
                else:
                    throughDistance = findDistanceThroughBody(parentSketch, center2d, targetBody, direction)
                    log(f"Through hole distance: {throughDistance:.4f}cm")
                    distance = adsk.core.ValueInput.createByReal(throughDistance)
                    extent = adsk.fusion.DistanceExtentDefinition.create(distance)
                    extInput.setOneSideExtent(extent, direction)
                
                extInput.participantBodies = [targetBody]
                extrude = extrudes.add(extInput)
                
                log("Extrude created successfully")
                
                if includeChamfer:
                    chamferEdge = findChamferEdge(extrude, targetBody, parentSketch, center2d, diameter)
                    if chamferEdge:
                        addChamferToEdge(component, chamferEdge, CONFIG['chamfer_size'])
                        log(f"Chamfer added ({CONFIG['chamfer_size']}mm)")
                    else:
                        log("Chamfer edge not found, skipping chamfer")

                if includeBottomRadius:
                    result = addBottomRadiusToBlindHole(component, extrude, targetBody, parentSketch, center2d, diameter, CONFIG['bottom_radius_size'])
                    if result:
                        log(f"Bottom radius added ({CONFIG['bottom_radius_size']}mm)")
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
                except:
                    log("Timeline grouping failed (non-parametric mode?)")
                    pass

            log(f"\n=== COMMAND EXECUTE END ===")
            log(f"Results: {successCount} successful, {failedCount} failed")

            if failedCount > 0:
                _ui.messageBox(f'Created {successCount} insert hole(s).\n{failedCount} failed (no intersection with target body).')
            elif showMessage:
                _ui.messageBox(f'Successfully created {successCount} insert hole(s).')
                
        except:
            log(f"FATAL ERROR: {traceback.format_exc()}")
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def updateInfoText(inputs):
    try:
        insertSize = inputs.itemById('insertSize')
        holeType = inputs.itemById('holeType')
        infoText = inputs.itemById('infoText')
        
        insertName = insertSize.selectedItem.name
        isBlindHole = holeType.selectedItem.name == 'Blind Hole'
        
        holeDia, insertLen, minWall = INSERT_SPECS[insertName]
        
        if isBlindHole:
            holeDepth = insertLen + CONFIG['blind_hole_extra_depth']
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
        
    except:
        pass

def isSamePoint(p1, p2, tol=TOL):
    return (abs(p1.x - p2.x) < tol and
            abs(p1.y - p2.y) < tol and
            abs(p1.z - p2.z) < tol)

def isSameCircle(c1, c2, tol=TOL):
    # Compare center (in sketch space) and radius
    c1_center = c1.centerSketchPoint.geometry
    c2_center = c2.centerSketchPoint.geometry
    if not isSamePoint(c1_center, c2_center, tol):
        return False
    return abs(c1.radius - c2.radius) < tol



def log(msg):
    """Write debug text to Fusion's Text Commands palette (only if logging enabled)."""
    try:
        # Only log if enabled in config
        if not CONFIG.get('enable_logging', False):
            return
            
        app = adsk.core.Application.get()
        ui = app.userInterface
        p = ui.palettes.itemById('TextCommands')
        if not p.isVisible:
            p.isVisible = True
        p.writeText(str(msg))
    except:
        pass

def clear_log():
    """Clear the Text Commands palette."""
    try:
        if not CONFIG.get('enable_logging', False):
            return
            
        app = adsk.core.Application.get()
        ui = app.userInterface
        p = ui.palettes.itemById('TextCommands')
        if p:
            # Clear by writing many empty lines (workaround, no direct clear method)
            for _ in range(50):
                p.writeText('')
            if not p.isVisible:
                p.isVisible = True
    except:
        pass


def findExtrudeDirectionFromSketch(sketch, circleCenter, targetBody):
    """
    Determine extrude direction by checking which direction from the circle center
    points INTO the target body from the sketch surface.
    
    Args:
        sketch: The sketch containing the profile
        circleCenter: The sketch point at the center of the circle (Point2D)
        targetBody: The body to cut into
    
    Returns:
        adsk.fusion.ExtentDirections enum value
    """
    try:
        log("--- findExtrudeDirectionFromSketch START ---")
        
        # Get sketch transform to convert 2D sketch point to 3D world space
        sketchTransform = sketch.transform
        
        # Convert 2D circle center to 3D point in sketch space (z=0)
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        
        # Transform to world space
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)
        
        log(f"Circle center (world): ({center3D.x:.4f}, {center3D.y:.4f}, {center3D.z:.4f})")
        
        # Get the sketch normal (Z-axis) from the transform matrix
        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()
        
        log(f"Sketch normal: ({zAxis.x:.4f}, {zAxis.y:.4f}, {zAxis.z:.4f})")
        
        # Test points at different distances to find which direction enters the body
        testDistances = [0.01, 0.05, 0.1, 0.2]  # 0.1mm, 0.5mm, 1mm, 2mm
        
        positiveIsInside = False
        negativeIsInside = False
        
        log("Testing positive direction...")
        # Check positive direction
        for testDistance in testDistances:
            positivePoint = adsk.core.Point3D.create(
                center3D.x + zAxis.x * testDistance,
                center3D.y + zAxis.y * testDistance,
                center3D.z + zAxis.z * testDistance
            )
            
            positiveContainment = targetBody.pointContainment(positivePoint)
            containment_str = "INSIDE" if positiveContainment == adsk.fusion.PointContainment.PointInsidePointContainment else \
                             "ON_SURFACE" if positiveContainment == adsk.fusion.PointContainment.PointOnPointContainment else "OUTSIDE"
            log(f"  Distance {testDistance:.3f}cm: {containment_str}")
            
            if (positiveContainment == adsk.fusion.PointContainment.PointInsidePointContainment or
                positiveContainment == adsk.fusion.PointContainment.PointOnPointContainment):
                positiveIsInside = True
                log(f"  Positive direction enters body at {testDistance:.3f}cm")
                break
        
        log("Testing negative direction...")
        # Check negative direction
        for testDistance in testDistances:
            negativePoint = adsk.core.Point3D.create(
                center3D.x - zAxis.x * testDistance,
                center3D.y - zAxis.y * testDistance,
                center3D.z - zAxis.z * testDistance
            )
            
            negativeContainment = targetBody.pointContainment(negativePoint)
            containment_str = "INSIDE" if negativeContainment == adsk.fusion.PointContainment.PointInsidePointContainment else \
                             "ON_SURFACE" if negativeContainment == adsk.fusion.PointContainment.PointOnPointContainment else "OUTSIDE"
            log(f"  Distance {testDistance:.3f}cm: {containment_str}")
            
            if (negativeContainment == adsk.fusion.PointContainment.PointInsidePointContainment or
                negativeContainment == adsk.fusion.PointContainment.PointOnPointContainment):
                negativeIsInside = True
                log(f"  Negative direction enters body at {testDistance:.3f}cm")
                break
        
        # Determine direction based on results
        if positiveIsInside and not negativeIsInside:
            log("Decision: POSITIVE direction (only positive is inside)")
            log("--- findExtrudeDirectionFromSketch END (success) ---")
            return adsk.fusion.ExtentDirections.PositiveExtentDirection
        elif negativeIsInside and not positiveIsInside:
            log("Decision: NEGATIVE direction (only negative is inside)")
            log("--- findExtrudeDirectionFromSketch END (success) ---")
            return adsk.fusion.ExtentDirections.NegativeExtentDirection
        elif positiveIsInside and negativeIsInside:
            log("Both directions inside body - sketch is embedded in material")
            log("Testing very close to sketch plane to determine surface side...")
            
            # Both directions are inside the body (sketch is inside material)
            verySmallDistance = 0.001  # 0.01mm
            
            veryClosePositive = adsk.core.Point3D.create(
                center3D.x + zAxis.x * verySmallDistance,
                center3D.y + zAxis.y * verySmallDistance,
                center3D.z + zAxis.z * verySmallDistance
            )
            
            veryCloseNegative = adsk.core.Point3D.create(
                center3D.x - zAxis.x * verySmallDistance,
                center3D.y - zAxis.y * verySmallDistance,
                center3D.z - zAxis.z * verySmallDistance
            )
            
            posContain = targetBody.pointContainment(veryClosePositive)
            negContain = targetBody.pointContainment(veryCloseNegative)
            
            posOut = (posContain == adsk.fusion.PointContainment.PointOutsidePointContainment)
            negOut = (negContain == adsk.fusion.PointContainment.PointOutsidePointContainment)
            
            log(f"  Very close positive: {'OUTSIDE' if posOut else 'INSIDE/ON'}")
            log(f"  Very close negative: {'OUTSIDE' if negOut else 'INSIDE/ON'}")
            
            if posOut and not negOut:
                log("Decision: NEGATIVE direction (positive side is outside)")
                log("--- findExtrudeDirectionFromSketch END (success) ---")
                return adsk.fusion.ExtentDirections.NegativeExtentDirection
            elif negOut and not posOut:
                log("Decision: POSITIVE direction (negative side is outside)")
                log("--- findExtrudeDirectionFromSketch END (success) ---")
                return adsk.fusion.ExtentDirections.PositiveExtentDirection
            else:
                log("Decision: POSITIVE direction (default fallback)")
                log("--- findExtrudeDirectionFromSketch END (success) ---")
                return adsk.fusion.ExtentDirections.PositiveExtentDirection
        else:
            log("ERROR: Neither direction is inside body - sketch not on body surface")
            log("--- findExtrudeDirectionFromSketch END (failed) ---")
            return None
            
    except:
        log(f"EXCEPTION in findExtrudeDirectionFromSketch: {traceback.format_exc()}")
        log("--- findExtrudeDirectionFromSketch END (exception) ---")
        if _ui:
            _ui.messageBox('Error in findExtrudeDirectionFromSketch:\n{}'.format(traceback.format_exc()))
        return None




def findChamferEdge(extrudeFeature, targetBody, sketch, circleCenter, holeDiameter):
    """
    Find the circular edge at the hole entrance for chamfering.
    The edge is where the hole enters the body surface, not necessarily at the sketch plane.
    
    Args:
        extrudeFeature: The extrude feature that created the hole
        targetBody: The body that was cut
        sketch: The sketch containing the circle
        circleCenter: Center point of the circle (Point2D)
        holeDiameter: The diameter of the hole in cm
    
    Returns:
        The edge to chamfer, or None if not found
    """
    try:
        # Convert circle center to 3D world coordinates
        sketchTransform = sketch.transform
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)
        
        # Get the sketch normal
        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()
        
        # Calculate expected radius
        expectedRadius = holeDiameter / 2.0
        
        # Look through all edges on the target body
        # Find circular edges with matching radius that are aligned with sketch normal
        candidateEdges = []
        
        for edge in targetBody.edges:
            if edge.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
                edgeCircle = edge.geometry
                edgeCenter = edgeCircle.center
                edgeRadius = edgeCircle.radius
                edgeNormal = edgeCircle.normal
                
                # Check if radius matches (within tolerance)
                if abs(edgeRadius - expectedRadius) > 0.001:  # 0.01mm tolerance
                    continue
                
                # Check if edge is aligned along the sketch normal direction
                # The edge normal should be parallel (or anti-parallel) to sketch normal
                dotProduct = abs(edgeNormal.x * zAxis.x + edgeNormal.y * zAxis.y + edgeNormal.z * zAxis.z)
                if dotProduct < 0.99:  # Allow small angle deviation
                    continue
                
                # Check if edge center is on the line through circleCenter along sketch normal
                # Vector from sketch center to edge center
                vecToEdge = adsk.core.Vector3D.create(
                    edgeCenter.x - center3D.x,
                    edgeCenter.y - center3D.y,
                    edgeCenter.z - center3D.z
                )
                
                # Project this vector onto the sketch normal
                projection = vecToEdge.x * zAxis.x + vecToEdge.y * zAxis.y + vecToEdge.z * zAxis.z
                
                # Check if the edge is on the axis (perpendicular distance should be ~0)
                perpDist = vecToEdge.length - abs(projection)
                if perpDist > 0.01:  # 0.1mm tolerance
                    continue
                
                # This is a valid candidate - store with distance along normal
                candidateEdges.append((edge, abs(projection)))
        
        # Return the edge closest to the sketch plane
        # (this is the entry edge, not the exit edge for through holes)
        if len(candidateEdges) > 0:
            candidateEdges.sort(key=lambda x: x[1])  # Sort by distance from sketch plane
            return candidateEdges[0][0]
        
        return None
        
    except:
        if _ui:
            _ui.messageBox('Error in findChamferEdge:\n{}'.format(traceback.format_exc()))
        return None


def addChamferToEdge(component, edge, chamferSize):
    """
    Add a chamfer to the specified edge.
    
    Args:
        component: The component containing the feature
        edge: The edge to chamfer
        chamferSize: Chamfer distance in mm
    
    Returns:
        The chamfer feature, or None if failed
    """
    try:
        chamfers = component.features.chamferFeatures
        
        # Create edge collection
        edges = adsk.core.ObjectCollection.create()
        edges.add(edge)
        
        # Create chamfer input
        chamferInput = chamfers.createInput(edges, True)
        
        # Set the chamfer distance (convert mm to cm)
        chamferDistance = adsk.core.ValueInput.createByReal(chamferSize / 10.0)
        chamferInput.setToEqualDistance(chamferDistance)
        
        # Create the chamfer
        chamfer = chamfers.add(chamferInput)
        return chamfer
        
    except:
        if _ui:
            _ui.messageBox('Error in addChamferToEdge:\n{}'.format(traceback.format_exc()))
        return None

def findDistanceThroughBody(sketch, circleCenter, targetBody, direction):
    """
    Find the distance needed to cut completely through the body in the given direction.
    
    Args:
        sketch: The sketch containing the circle
        circleCenter: Center point of the circle (Point2D)
        targetBody: The body to cut through
        direction: Extrusion direction (PositiveExtentDirection or NegativeExtentDirection)
    
    Returns:
        Distance in cm to cut through the body, or None if not found
    """
    try:
        # Get sketch transform
        sketchTransform = sketch.transform
        
        # Convert circle center to 3D
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)
        
        # Get sketch normal
        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()
        
        # Determine direction multiplier
        if direction == adsk.fusion.ExtentDirections.PositiveExtentDirection:
            multiplier = 1.0
        else:
            multiplier = -1.0
        
        # Search along the direction to find where we exit the body
        maxDistance = 100.0  # 1000mm = 1 meter max
        stepSize = 0.1  # 1mm steps
        
        insideBody = False
        exitDistance = None
        
        for i in range(1, int(maxDistance / stepSize) + 1):
            distance = i * stepSize
            testPoint = adsk.core.Point3D.create(
                center3D.x + zAxis.x * distance * multiplier,
                center3D.y + zAxis.y * distance * multiplier,
                center3D.z + zAxis.z * distance * multiplier
            )
            
            containment = targetBody.pointContainment(testPoint)
            
            # Track when we're inside the body
            if containment == adsk.fusion.PointContainment.PointInsidePointContainment:
                insideBody = True
            
            # Detect when we exit the body (inside -> outside)
            if insideBody and containment == adsk.fusion.PointContainment.PointOutsidePointContainment:
                exitDistance = distance
                break
        
        # Add a small margin to ensure we go completely through
        if exitDistance is not None:
            return exitDistance + 0.2  # Add 2mm margin
        
        # Fallback to a large distance if we can't find the exit
        return 10.0  # 100mm default
        
    except:
        if _ui:
            _ui.messageBox('Error in findDistanceThroughBody:\n{}'.format(traceback.format_exc()))
        return 10.0  # 100mm fallback
    
"""
ThreadMeister - Improved version with detailed logging

This version includes extensive logging for the addBottomRadiusToBlindHole function
to diagnose why the bottom radius is not being created.

Key improvements:
1. Detailed logging in addBottomRadiusToBlindHole function
2. Better error reporting
3. Edge detection diagnostics
"""
import adsk.core, adsk.fusion, traceback
import os
import configparser
import math 

# Global configuration
TOL = 1e-6
INSERT_SPECS = {}
CONFIG = {
    'chamfer_size': 0.5,
    'blind_hole_extra_depth': 1.0,
    'chamfer_enabled_default': True,
    'bottom_radius_size': 0.5,
    'bottom_radius_enabled_default': False,
    'show_success_message': True,
    'enable_logging': True  # WICHTIG: Auf True setzen für Debugging!
}

# [Previous functions remain the same: load_config, save_last_selected_insert, etc.]
# ... (keep all the existing helper functions)

def addBottomRadiusToBlindHole(component, extrudeFeature, targetBody, sketch, circleCenter, holeDiameter, radiusSize):
    """
    Add a fillet to the bottom edge of a blind hole to round the corner.
    IMPROVED VERSION with extensive logging.
    
    Args:
        component: The component containing features
        extrudeFeature: The extrude feature that created the hole
        targetBody: The body that was cut
        sketch: The sketch containing the circle
        circleCenter: Center point of the circle (Point2D)
        holeDiameter: Diameter of the hole in cm
        radiusSize: Fillet radius in mm
    
    Returns:
        The fillet feature, or None if failed
    """
    try:
        log("=== addBottomRadiusToBlindHole START ===")
        log(f"Hole diameter: {holeDiameter:.4f}cm, Fillet radius size: {radiusSize}mm")
        
        # Convert circle center to 3D
        sketchTransform = sketch.transform
        center3DSketch = adsk.core.Point3D.create(circleCenter.x, circleCenter.y, 0)
        center3D = center3DSketch.copy()
        center3D.transformBy(sketchTransform)
        
        log(f"Circle center (world): ({center3D.x:.4f}, {center3D.y:.4f}, {center3D.z:.4f})")
        
        # Get sketch normal
        (origin, xAxis, yAxis, zAxis) = sketchTransform.getAsCoordinateSystem()
        log(f"Sketch normal: ({zAxis.x:.4f}, {zAxis.y:.4f}, {zAxis.z:.4f})")
        
        # Expected radius
        expectedRadius = holeDiameter / 2.0
        log(f"Expected edge radius: {expectedRadius:.4f}cm ({expectedRadius * 10:.2f}mm)")
        
        # Log fillet size relative to hole
        filletRadiusCm = radiusSize / 10.0
        log(f"Fillet radius: {filletRadiusCm:.4f}cm ({radiusSize}mm)")
        
        if filletRadiusCm >= expectedRadius:
            log(f"WARNING: Fillet radius ({radiusSize}mm) >= hole radius ({expectedRadius*10:.2f}mm)!")
            log("This may cause the fillet to fail. Consider reducing fillet size.")
        
        # Find the bottom edge of the blind hole
        candidateEdges = []
        
        log(f"\nSearching through {targetBody.edges.count} edges on target body...")
        edgeCount = 0
        circleCount = 0
        rejectionReasons = {
            'not_circle': 0,
            'radius_mismatch': 0,
            'not_aligned': 0,
            'not_on_axis': 0
        }
        
        for edge in targetBody.edges:
            edgeCount += 1
            
            # Only process circular edges
            if edge.geometry.curveType != adsk.core.Curve3DTypes.Circle3DCurveType:
                rejectionReasons['not_circle'] += 1
                continue
            
            circleCount += 1
            edgeCircle = edge.geometry
            edgeCenter = edgeCircle.center
            edgeRadius = edgeCircle.radius
            edgeNormal = edgeCircle.normal
            
            log(f"\n  Circle Edge #{circleCount} (Edge #{edgeCount}):")
            log(f"    Center: ({edgeCenter.x:.4f}, {edgeCenter.y:.4f}, {edgeCenter.z:.4f})")
            log(f"    Radius: {edgeRadius:.4f}cm ({edgeRadius*10:.2f}mm)")
            log(f"    Normal: ({edgeNormal.x:.4f}, {edgeNormal.y:.4f}, {edgeNormal.z:.4f})")
            
            # CHECK 1: Radius match
            radiusDiff = abs(edgeRadius - expectedRadius)
            log(f"    Radius difference: {radiusDiff:.6f}cm ({radiusDiff*10:.4f}mm)")
            
            if radiusDiff > 0.005:  # 0.05mm tolerance
                log(f"    ❌ REJECTED - Radius mismatch (diff={radiusDiff*10:.4f}mm > 0.01mm)")
                rejectionReasons['radius_mismatch'] += 1
                continue
            log(f"    ✓ Radius matches")
            
            # CHECK 2: Alignment with sketch normal
            dotProduct = abs(edgeNormal.x * zAxis.x + edgeNormal.y * zAxis.y + edgeNormal.z * zAxis.z)
            log(f"    Alignment dot product: {dotProduct:.6f}")
            
            if dotProduct < 0.95:
                log(f"    ❌ REJECTED - Not aligned with sketch normal (dot={dotProduct:.6f} < 0.99)")
                rejectionReasons['not_aligned'] += 1
                continue
            log(f"    ✓ Aligned with sketch normal")
            
            # CHECK 3: Position on hole axis
            vecToEdge = adsk.core.Vector3D.create(
                edgeCenter.x - center3D.x,
                edgeCenter.y - center3D.y,
                edgeCenter.z - center3D.z
            )
            
            # Distance along the normal (z-axis of sketch)
            distanceAlongNormal = abs(vecToEdge.x * zAxis.x + vecToEdge.y * zAxis.y + vecToEdge.z * zAxis.z)
            
            # Perpendicular distance from axis
            perpDistanceSquared = (vecToEdge.length ** 2) - (distanceAlongNormal ** 2)
            perpDistance = math.sqrt(max(0, perpDistanceSquared))
            
            log(f"    Distance along normal: {distanceAlongNormal:.4f}cm ({distanceAlongNormal*10:.2f}mm)")
            log(f"    Perpendicular distance from axis: {perpDistance:.4f}cm ({perpDistance*10:.2f}mm)")
            
            if perpDistance > 0.05:  # 0.5mm tolerance
                log(f"    ❌ REJECTED - Not on hole axis (perpDist={perpDistance*10:.2f}mm > 0.1mm)")
                rejectionReasons['not_on_axis'] += 1
                continue
            log(f"    ✓ On hole axis")
            
            log(f"    ✓✓✓ CANDIDATE ACCEPTED - Distance from sketch: {distanceAlongNormal:.4f}cm")
            candidateEdges.append((edge, distanceAlongNormal))
        
        # Summary
        log(f"\n=== SEARCH SUMMARY ===")
        log(f"Total edges examined: {edgeCount}")
        log(f"Circular edges found: {circleCount}")
        log(f"Candidates found: {len(candidateEdges)}")
        log(f"\nRejection reasons:")
        log(f"  Not circular: {rejectionReasons['not_circle']}")
        log(f"  Radius mismatch: {rejectionReasons['radius_mismatch']}")
        log(f"  Not aligned: {rejectionReasons['not_aligned']}")
        log(f"  Not on axis: {rejectionReasons['not_on_axis']}")
        
        # Process candidates
        if len(candidateEdges) == 0:
            log("\n❌ ERROR: No candidate edges found!")
            log("Possible reasons:")
            log("  1. Hole was not created successfully")
            log("  2. Tolerance too strict for edge detection")
            log("  3. Geometry issue with the blind hole")
            log("=== addBottomRadiusToBlindHole END (no candidates) ===")
            return None
        
        # Sort by distance (furthest = bottom of blind hole)
        candidateEdges.sort(key=lambda x: x[1], reverse=True)
        
        log(f"\n=== CANDIDATE EDGES (sorted by distance) ===")
        for i, (edge, dist) in enumerate(candidateEdges):
            marker = "← SELECTED (furthest)" if i == 0 else ""
            log(f"  {i+1}. Distance from sketch: {dist:.4f}cm ({dist*10:.2f}mm) {marker}")
        
        bottomEdge = candidateEdges[0][0]
        bottomDistance = candidateEdges[0][1]
        
        log(f"\nUsing edge at distance: {bottomDistance:.4f}cm ({bottomDistance*10:.2f}mm)")
        
        # Create fillet
        log(f"\n=== CREATING FILLET ===")
        fillets = component.features.filletFeatures
        edgeCollection = adsk.core.ObjectCollection.create()
        edgeCollection.add(bottomEdge)
        
        log(f"Edge collection created with 1 edge")
        log(f"Fillet radius: {filletRadiusCm:.4f}cm ({radiusSize}mm)")
        
        filletInput = fillets.createInput()
        log("Fillet input created")
        
        try:
            filletInput.addConstantRadiusEdgeSet(
                edgeCollection,
                adsk.core.ValueInput.createByReal(filletRadiusCm),
                True  # isTangentChain
            )
            log("Constant radius edge set added successfully")
        except Exception as e:
            log(f"❌ ERROR adding edge set: {str(e)}")
            log("=== addBottomRadiusToBlindHole END (edge set error) ===")
            return None
        
        log("Adding fillet feature to component...")
        try:
            fillet = fillets.add(filletInput)
            
            if fillet:
                log("✓✓✓ SUCCESS: Fillet created successfully!")
                log("=== addBottomRadiusToBlindHole END (success) ===")
                return fillet
            else:
                log("❌ ERROR: fillets.add() returned None")
                log("Possible reasons:")
                log("  1. Fillet radius too large for geometry")
                log("  2. Edge cannot be filleted (sharp corner issue)")
                log("  3. Fusion 360 internal error")
                log("=== addBottomRadiusToBlindHole END (fillet creation failed) ===")
                return None
                
        except Exception as e:
            log(f"❌ EXCEPTION during fillet.add(): {str(e)}")
            log(traceback.format_exc())
            log("=== addBottomRadiusToBlindHole END (exception) ===")
            return None
        
    except Exception as e:
        log(f"❌ FATAL EXCEPTION in addBottomRadiusToBlindHole: {str(e)}")
        log(traceback.format_exc())
        log("=== addBottomRadiusToBlindHole END (fatal exception) ===")
        if _ui:
            _ui.messageBox('Error in addBottomRadiusToBlindHole:\n{}'.format(traceback.format_exc()))
        return None


# Add debugging helper function
def diagnose_blind_hole(component, targetBody, sketch, circleCenter, holeDiameter):
    """
    Diagnostic function to analyze blind hole geometry.
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


def stop(context):
    """Called when the add-in is unloaded"""
    try:
        # Delete the command definition
        cmdDef = _ui.commandDefinitions.itemById(CMD_ID)
        if cmdDef:
            cmdDef.deleteMe()
            
        # Delete the button from the panel
        panel = _ui.allToolbarPanels.itemById(PANEL_ID)
        if panel:
            control = panel.controls.itemById(CMD_ID)
            if control:
                control.deleteMe()
    except:
        _ui.messageBox('Failed to stop add-in:\n{}'.format(traceback.format_exc()))
