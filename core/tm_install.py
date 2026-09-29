"""
tm_install.py – Detect other ThreadMeister installations.

Fusion loads every installed copy of the add-in (App Store bundle and manual installs).
All copies register the same command ID, so the one that loads first owns the toolbar
button. See .scratch/duplicate-install/.
"""
import glob
import os
import sys


def get_install_search_dirs(platform=None, environ=None, home=None):
    """
    Return the folders Fusion loads add-ins from, per platform.

    Windows: %APPDATA%\\Autodesk\\ApplicationPlugins (App Store) and
             %APPDATA%\\Autodesk\\Autodesk Fusion 360\\API\\AddIns (manual install)
    macOS:   the same two folders under ~/Library/Application Support/Autodesk
    """
    platform = sys.platform if platform is None else platform
    environ = os.environ if environ is None else environ
    home = os.path.expanduser('~') if home is None else home

    if platform.startswith('win'):
        appdata = environ.get('APPDATA')
        if not appdata:
            return []
        autodesk = os.path.join(appdata, 'Autodesk')
    elif platform == 'darwin':
        autodesk = os.path.join(home, 'Library', 'Application Support', 'Autodesk')
    else:
        return []

    return [
        os.path.join(autodesk, 'ApplicationPlugins'),
        os.path.join(autodesk, 'Autodesk Fusion 360', 'API', 'AddIns'),
    ]


def _norm(path):
    return os.path.normcase(os.path.realpath(path))


def find_other_installs(own_dir, search_dirs):
    """
    Return the ThreadMeister installation folders in search_dirs other than the one
    that contains own_dir (this running copy).

    Matches folders named ThreadMeister* (e.g. "ThreadMeister", "ThreadMeister.bundle").
    """
    own = _norm(own_dir)
    others = []
    for search_dir in search_dirs:
        for candidate in sorted(glob.glob(os.path.join(search_dir, 'ThreadMeister*'))):
            if not os.path.isdir(candidate):
                continue
            path = _norm(candidate)
            if own == path or own.startswith(path + os.sep):
                continue
            others.append(candidate)
    return others


def duplicate_install_message(others):
    """User message listing the other installations and how to disable them."""
    paths = '\n'.join(f'  {p}' for p in others)
    return (
        'Another ThreadMeister installation was found:\n'
        f'{paths}\n\n'
        'Only one copy can own the ThreadMeister button, so an old version may run '
        'instead of this one.\n\n'
        'Please disable the other copy in Utilities → Add-Ins: switch it off and '
        'uncheck "Run on Startup", then restart Fusion. You can ignore error messages '
        'from the old version until then.'
    )
