"""
tm_state.py – Shared state, constants, and globals for ThreadMeister.

All other tm_* modules import from here. This module has no dependencies
on other tm_* modules.
"""
import adsk.core

# Tolerance for geometric comparisons
TOL = 1e-6

# Insert specifications: name -> (hole_diameter_mm, insert_length_mm, min_wall_mm)
# Populated at startup by tm_config.load_config(); defaults are set here as fallback.
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

# Runtime configuration (overwritten by tm_config.load_config())
CONFIG = {
    'chamfer_size': 0.5,
    'blind_hole_extra_depth': 1.0,
    'chamfer_enabled_default': True,
    'bottom_radius_size': 0.5,
    'bottom_radius_enabled_default': False,
    'show_success_message': True,
    'enable_logging': False,
    'enable_debug_export': False,
    'hole_type_blind': True,
    'last_selected_insert': 'M3 x 5.7mm (standard)',
}

# Event handler references (kept in scope to prevent garbage collection)
_handlers = []

# Fusion 360 application and UI handles
_app = adsk.core.Application.get()
_ui = _app.userInterface

# Command identity
CMD_ID = 'ThreadMeisterCmd'
CMD_NAME = 'ThreadMeister'
CMD_Description = 'Create heat-set insert holes with CNC Kitchen specifications'

# Toolbar panel
PANEL_ID = 'SolidModifyPanel'  # MODIFY panel in SOLID workspace
