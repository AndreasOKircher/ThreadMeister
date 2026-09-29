"""
tm_config.py – Configuration loading, validation, saving, and defaults.

Reads/writes config.ini. Mutates INSERT_SPECS and CONFIG in tm_state.

Config sections:
  [Settings]   - Design parameters (chamfer_size, blind_hole_extra_depth, bottom_radius_size)
  [Inserts]    - Insert specifications (name = diameter, length, min_wall)
  [UI State]   - Remembered menu state (chamfer_enabled_default, bottom_radius_enabled_default, etc.)
  [Developer]  - Debug flags (enable_logging, enable_debug_export)
"""
import os
import configparser
from . import tm_state


def _get_config_path():
    """Return the absolute path to config.ini."""
    addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    return os.path.join(addon_path, 'config.ini')


def _read_config_file(config_file=None):
    """Read and return a RawConfigParser from config.ini."""
    if config_file is None:
        config_file = _get_config_path()
    config = configparser.RawConfigParser()
    config.optionxform = str  # Preserve case
    config.read(config_file, encoding='utf-8')
    return config


def _is_old_format(config):
    """Check if config uses old single-section format (no [UI State] section)."""
    return not config.has_section('UI State')


def _get(config, key, section_new, fallback, getter='get'):
    """Read a key from the correct section, falling back to [Settings] for old format."""
    for section in (section_new, 'Settings'):
        if config.has_section(section) and config.has_option(section, key):
            try:
                if getter == 'float':
                    return config.getfloat(section, key)
                elif getter == 'boolean':
                    return config.getboolean(section, key)
                else:
                    return config.get(section, key)
            except (ValueError, configparser.Error):
                return fallback
    return fallback


def load_config():
    """Load configuration from config.ini with validation. Creates defaults if missing."""
    config_file = _get_config_path()

    if not os.path.exists(config_file):
        create_default_config()

    errors = []
    warnings = []

    try:
        config = _read_config_file(config_file)
        needs_migration = _is_old_format(config)

        # --- [Settings]: Design parameters ---
        chamfer = _get(config, 'chamfer_size', 'Settings', 0.5, 'float')
        if chamfer <= 0 or chamfer > 5.0:
            warnings.append(f'Chamfer size {chamfer}mm is unusual (expected 0-5mm). Using default 0.5mm.')
            chamfer = 0.5
        tm_state.CONFIG['chamfer_size'] = chamfer

        extra_depth = _get(config, 'blind_hole_extra_depth', 'Settings', 1.0, 'float')
        if extra_depth < 0 or extra_depth > 10.0:
            warnings.append(f'Extra depth {extra_depth}mm is unusual (expected 0-10mm). Using default 1.0mm.')
            extra_depth = 1.0
        tm_state.CONFIG['blind_hole_extra_depth'] = extra_depth

        bottom_radius = _get(config, 'bottom_radius_size', 'Settings', 0.5, 'float')
        if bottom_radius < 0 or bottom_radius > 5.0:
            warnings.append(f'Bottom radius {bottom_radius}mm is unusual (expected 0-5mm). Using default 0.5mm.')
            bottom_radius = 0.5
        tm_state.CONFIG['bottom_radius_size'] = bottom_radius

        # --- [UI State]: Remembered menu state ---
        tm_state.CONFIG['chamfer_enabled_default'] = _get(
            config, 'chamfer_enabled_default', 'UI State', True, 'boolean')
        tm_state.CONFIG['bottom_radius_enabled_default'] = _get(
            config, 'bottom_radius_enabled_default', 'UI State', False, 'boolean')
        tm_state.CONFIG['show_success_message'] = _get(
            config, 'show_success_message', 'UI State', True, 'boolean')
        tm_state.CONFIG['hole_type_blind'] = _get(
            config, 'hole_type_blind', 'UI State', True, 'boolean')
        tm_state.CONFIG['last_selected_insert'] = _get(
            config, 'last_selected_insert', 'UI State', 'M3 x 5.7mm (standard)')

        # --- [Developer]: Debug flags ---
        tm_state.CONFIG['enable_logging'] = _get(
            config, 'enable_logging', 'Developer', False, 'boolean')
        tm_state.CONFIG['enable_debug_export'] = _get(
            config, 'enable_debug_export', 'Developer', False, 'boolean')

        # --- [Inserts] ---
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

        # Auto-migrate old format to new sections
        if needs_migration:
            _migrate_config(config_file)

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


def _migrate_config(config_file):
    """Rewrite config.ini from old single-section format to new multi-section format."""
    try:
        _write_config_file(config_file)
    except Exception:
        pass  # Migration failure is non-critical; old format still works


def _write_config_file(config_file=None):
    """Write current CONFIG and INSERT_SPECS to config.ini in the new multi-section format."""
    if config_file is None:
        config_file = _get_config_path()

    config = configparser.RawConfigParser()
    config.optionxform = str

    # [Settings]
    config.add_section('Settings')
    config.set('Settings', 'chamfer_size', str(tm_state.CONFIG.get('chamfer_size', 0.5)))
    config.set('Settings', 'blind_hole_extra_depth', str(tm_state.CONFIG.get('blind_hole_extra_depth', 1.0)))
    config.set('Settings', 'bottom_radius_size', str(tm_state.CONFIG.get('bottom_radius_size', 0.5)))

    # [Inserts]
    config.add_section('Inserts')
    for name, (dia, length, wall) in tm_state.INSERT_SPECS.items():
        config.set('Inserts', name, f'{dia}, {length}, {wall}')

    # [UI State]
    config.add_section('UI State')
    config.set('UI State', 'chamfer_enabled_default', str(tm_state.CONFIG.get('chamfer_enabled_default', True)))
    config.set('UI State', 'bottom_radius_enabled_default', str(tm_state.CONFIG.get('bottom_radius_enabled_default', False)))
    config.set('UI State', 'show_success_message', str(tm_state.CONFIG.get('show_success_message', True)))
    config.set('UI State', 'hole_type_blind', str(tm_state.CONFIG.get('hole_type_blind', True)))
    config.set('UI State', 'last_selected_insert', tm_state.CONFIG.get('last_selected_insert', 'M3 x 5.7mm (standard)'))

    # [Developer]
    config.add_section('Developer')
    config.set('Developer', 'enable_logging', str(tm_state.CONFIG.get('enable_logging', False)))
    config.set('Developer', 'enable_debug_export', str(tm_state.CONFIG.get('enable_debug_export', False)))

    with open(config_file, 'w', encoding='utf-8') as f:
        config.write(f)


def save_last_selected_insert(insert_name):
    """Persist the last selected insert name to config.ini."""
    try:
        config_file = _get_config_path()
        config = _read_config_file(config_file)
        section = 'UI State' if config.has_section('UI State') else 'Settings'
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, 'last_selected_insert', insert_name)
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
    except Exception:
        pass


def save_checkbox_states(chamfer_state, radius_state, show_message_state, is_blind_hole):
    """Persist UI checkbox states and hole type to config.ini."""
    try:
        config_file = _get_config_path()
        config = _read_config_file(config_file)
        section = 'UI State' if config.has_section('UI State') else 'Settings'
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, 'chamfer_enabled_default', str(chamfer_state))
        config.set(section, 'bottom_radius_enabled_default', str(radius_state))
        config.set(section, 'show_success_message', str(show_message_state))
        config.set(section, 'hole_type_blind', str(is_blind_hole))
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
    """Write a default config.ini file in the new multi-section format."""
    config_file = _get_config_path()
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('[Settings]\n')
            f.write('chamfer_size = 0.5\n')
            f.write('blind_hole_extra_depth = 1.0\n')
            f.write('bottom_radius_size = 0.5\n')
            f.write('\n')
            f.write('[Inserts]\n')
            for name, (dia, length, wall) in get_default_inserts().items():
                f.write(f'{name} = {dia}, {length}, {wall}\n')
            f.write('\n')
            f.write('[UI State]\n')
            f.write('chamfer_enabled_default = True\n')
            f.write('bottom_radius_enabled_default = False\n')
            f.write('show_success_message = True\n')
            f.write('hole_type_blind = True\n')
            f.write('last_selected_insert = M3 x 5.7mm (standard)\n')
            f.write('\n')
            f.write('[Developer]\n')
            f.write('enable_logging = False\n')
            f.write('enable_debug_export = False\n')
    except Exception as e:
        if tm_state._ui:
            tm_state._ui.messageBox(f'Could not create config.ini: {str(e)}')
