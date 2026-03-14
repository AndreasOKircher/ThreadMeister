"""
Pytest configuration and shared fixtures.

CRITICAL: Must mock adsk module BEFORE any project imports,
since tm_state calls adsk.core.Application.get() at module import time.
"""

import sys
import os
from unittest.mock import MagicMock

# Stub adsk module before any project imports
adsk_mock = MagicMock()
adsk_mock.core.Application.get.return_value = MagicMock()
adsk_mock.fusion.CalculationAccuracy.MediumCalculationAccuracy = MagicMock()

# Mock ObjectCollection to be iterable
def create_object_collection():
    """Create a mock ObjectCollection that supports iteration."""
    coll = MagicMock()
    coll._items = []

    def add(item):
        coll._items.append(item)

    coll.add = add
    coll.__iter__ = lambda self: iter(coll._items)

    return coll

adsk_mock.core.ObjectCollection.create = create_object_collection

sys.modules['adsk'] = adsk_mock
sys.modules['adsk.core'] = adsk_mock.core
sys.modules['adsk.fusion'] = adsk_mock.fusion

# Add core/ to path so we can import tm_* modules
_core_path = os.path.join(os.path.dirname(__file__), '..', 'core')
if _core_path not in sys.path:
    sys.path.insert(0, _core_path)

# Now safe to import tm_state and suppress messageBox calls
import tm_state
tm_state._ui = None
# Logging disabled by default - set to True to see algorithm debug output
tm_state.CONFIG['enable_logging'] = False

# Override log function to print to stdout during tests (optional for debugging)
import tm_helpers
_original_log = tm_helpers.log
def debug_log(msg):
    """Log to stdout for debugging tests."""
    if tm_state.CONFIG.get('enable_logging', False):
        print(msg)
tm_helpers.log = debug_log
