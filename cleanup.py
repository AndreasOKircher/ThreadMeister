#!/usr/bin/env python3
import os

files_to_remove = [
    'tm_state.py',
    'tm_config.py',
    'tm_helpers.py',
    'tm_geometry.py',
    'tm_execute.py',
    'tm_ui.py'
]

base_dir = os.path.dirname(os.path.abspath(__file__))

for f in files_to_remove:
    fpath = os.path.join(base_dir, f)
    if os.path.exists(fpath):
        os.remove(fpath)
        print(f"Deleted: {f}")
    else:
        print(f"Not found: {f}")

print("Cleanup complete")
