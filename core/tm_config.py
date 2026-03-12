"""
tm_config.py – Configuration loading, validation, saving, and defaults.

Reads/writes config.ini. Mutates INSERT_SPECS and CONFIG in tm_state.
"""
import os
import configparser
import tm_state


def load_config():
    """Load configuration from config.ini with validation. Creates defaults if missing."""
    addon_path = os.path.dirname(os.path.realpath(__file__))
    addon_path = os.path.dirname(addon_path)  # Go up one level from core/
    config_file = os.path.join(addon_path, 'config.ini')

    if not os.path.exists(config_file):
        create_default_config()

    errors = []
    warnings = []

    try:
        config = configparser.RawConfigParser()
        config.optionxform = str  # Preserve case
        config.read(config_file, encoding='utf-8')

        if config.has_section('Settings'):
            try:
                chamfer = config.getfloat('Settings', 'chamfer_size', fallback=0.5)
                if chamfer <= 0 or chamfer > 5.0:
                    warnings.append(f'Chamfer size {chamfer}mm is unusual (expected 0-5mm). Using default 0.5mm.')
                    chamfer = 0.5
                tm_state.CONFIG['chamfer_size'] = chamfer
            except ValueError:
                warnings.append('Invalid chamfer_size value. Using default 0.5mm.')
                tm_state.CONFIG['chamfer_size'] = 0.5

            try:
                extra_depth = config.getfloat('Settings', 'blind_hole_extra_depth', fallback=1.0)
                if extra_depth < 0 or extra_depth > 10.0:
                    warnings.append(f'Extra depth {extra_depth}mm is unusual (expected 0-10mm). Using default 1.0mm.')
                    extra_depth = 1.0
                tm_state.CONFIG['blind_hole_extra_depth'] = extra_depth
            except ValueError:
                warnings.append('Invalid blind_hole_extra_depth value. Using default 1.0mm.')
                tm_state.CONFIG['blind_hole_extra_depth'] = 1.0

            try:
                tm_state.CONFIG['chamfer_enabled_default'] = config.getboolean('Settings', 'chamfer_enabled_default', fallback=True)
            except ValueError:
                warnings.append('Invalid chamfer_enabled_default value. Using default True.')
                tm_state.CONFIG['chamfer_enabled_default'] = True

            try:
                bottom_radius = config.getfloat('Settings', 'bottom_radius_size', fallback=0.5)
                if bottom_radius < 0 or bottom_radius > 5.0:
                    warnings.append(f'Bottom radius {bottom_radius}mm is unusual (expected 0-5mm). Using default 0.5mm.')
                    bottom_radius = 0.5
                tm_state.CONFIG['bottom_radius_size'] = bottom_radius
            except ValueError:
                warnings.append('Invalid bottom_radius_size value. Using default 0.5mm.')
                tm_state.CONFIG['bottom_radius_size'] = 0.5

            try:
                tm_state.CONFIG['bottom_radius_enabled_default'] = config.getboolean('Settings', 'bottom_radius_enabled_default', fallback=False)
            except ValueError:
                warnings.append('Invalid bottom_radius_enabled_default value. Using default False.')
                tm_state.CONFIG['bottom_radius_enabled_default'] = False

            try:
                tm_state.CONFIG['show_success_message'] = config.getboolean('Settings', 'show_success_message', fallback=True)
            except ValueError:
                warnings.append('Invalid show_success_message value. Using default True.')
                tm_state.CONFIG['show_success_message'] = True

            try:
                tm_state.CONFIG['hole_type_blind'] = config.getboolean('Settings', 'hole_type_blind', fallback=True)
            except ValueError:
                tm_state.CONFIG['hole_type_blind'] = True

            try:
                tm_state.CONFIG['enable_logging'] = config.getboolean('Settings', 'enable_logging', fallback=False)
            except ValueError:
                tm_state.CONFIG['enable_logging'] = False

            try:
                tm_state.CONFIG['enable_debug_export'] = config.getboolean('Settings', 'enable_debug_export', fallback=False)
            except ValueError:
                tm_state.CONFIG['enable_debug_export'] = False

            try:
                tm_state.CONFIG['last_selected_insert'] = config.get('Settings', 'last_selected_insert', fallback='M3 x 5.7mm (standard)')
            except Exception:
                tm_state.CONFIG['last_selected_insert'] = 'M3 x 5.7mm (standard)'

        # Load inserts
        tm_state.INSERT_SPECS.clear()
        if config.has_section('Inserts'):
            for name in config.options('Inserts'):
                if name.startswith('#'):
                    continue
                try:
                    values = config.get('Inserts', name)
                    if not values.strip() or values.strip().startswith('#'):
                        continue
                    parts = [x.strip() for x in values.split(',')]
                    if len(parts) != 3:
                        warnings.append(f'Insert "{name}" has {len(parts)} values (expected 3). Skipped.')
                        continue
                    try:
                        hole_dia = float(parts[0])
                        insert_len = float(parts[1])
                        min_wall = float(parts[2])
                        if hole_dia <= 0 or hole_dia > 50:
                            warnings.append(f'Insert "{name}": hole diameter {hole_dia}mm is invalid. Skipped.')
                            continue
                        if insert_len <= 0 or insert_len > 100:
                            warnings.append(f'Insert "{name}": insert length {insert_len}mm is invalid. Skipped.')
                            continue
                        if min_wall < 0 or min_wall > 20:
                            warnings.append(f'Insert "{name}": min wall {min_wall}mm is invalid. Skipped.')
                            continue
                        tm_state.INSERT_SPECS[name] = (hole_dia, insert_len, min_wall)
                    except ValueError:
                        warnings.append(f'Insert "{name}": Invalid number format. Skipped.')
                        continue
                except Exception:
                    warnings.append(f'Insert "{name}": Error reading values. Skipped.')
                    continue

        if not tm_state.INSERT_SPECS:
            errors.append('No valid inserts found in config.ini!')
            tm_state.INSERT_SPECS.update(get_default_inserts())
            warnings.append('Using default CNC Kitchen specifications.')

        if errors or warnings:
            msg = ''
            if errors:
                msg += 'ERRORS:\n' + '\n'.join(errors) + '\n\n'
            if warnings:
                msg += 'WARNINGS:\n' + '\n'.join(warnings)
            if tm_state._ui:
                tm_state._ui.messageBox(f'Config.ini issues:\n\n{msg}')

    except Exception as e:
        if tm_state._ui:
            tm_state._ui.messageBox(f'Error loading config.ini: {str(e)}\nUsing default specifications.')
        tm_state.INSERT_SPECS.update(get_default_inserts())

    return tm_state.INSERT_SPECS, tm_state.CONFIG


def save_last_selected_insert(insert_name):
    """Persist the last selected insert name to config.ini."""
    try:
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        config_file = os.path.join(addon_path, 'config.ini')
        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(config_file, encoding='utf-8')
        if not config.has_section('Settings'):
            config.add_section('Settings')
        config.set('Settings', 'last_selected_insert', insert_name)
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
    except Exception:
        pass


def save_checkbox_states(chamfer_state, radius_state, show_message_state, is_blind_hole):
    """Persist UI checkbox states and hole type to config.ini."""
    try:
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        config_file = os.path.join(addon_path, 'config.ini')
        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(config_file, encoding='utf-8')
        if not config.has_section('Settings'):
            config.add_section('Settings')
        config.set('Settings', 'chamfer_enabled_default', str(chamfer_state))
        config.set('Settings', 'bottom_radius_enabled_default', str(radius_state))
        config.set('Settings', 'show_success_message', str(show_message_state))
        config.set('Settings', 'hole_type_blind', str(is_blind_hole))
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
    except Exception:
        pass


def get_default_inserts():
    """Return the default CNC Kitchen insert specifications."""
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
    """Write a default config.ini file."""
    addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
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
            f.write('# Enable logging to Fusion TextCommands console (True or False)\n')
            f.write('enable_logging = False\n')
            f.write('\n')
            f.write('# Enable debug JSON export button in dialog (developer/support feature)\n')
            f.write('enable_debug_export = False\n')
            f.write('\n')
            f.write('# Last selected insert (will be remembered between sessions)\n')
            f.write('last_selected_insert = M3 x 5.7mm (standard)\n')
            f.write('\n\n')
            f.write('[Inserts]\n')
            for name, (dia, length, wall) in get_default_inserts().items():
                f.write(f'{name} = {dia}, {length}, {wall}\n')
            f.write('\n')
            f.write('# Add your custom inserts below:\n')
            f.write('# My Custom M3 = 4.5, 6.0, 1.6\n')
            f.write('# My Custom M4 = 5.7, 9.0, 2.0\n')
    except Exception as e:
        if tm_state._ui:
            tm_state._ui.messageBox(f'Could not create config.ini: {str(e)}')
