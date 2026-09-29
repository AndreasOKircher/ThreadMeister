"""
Unit tests for tm_install.py: detecting other ThreadMeister installations.
"""

import os

from tm_install import (
    get_install_search_dirs,
    find_other_installs,
    duplicate_install_message,
)


def make_install(root, *parts):
    path = os.path.join(root, *parts)
    os.makedirs(path)
    return path


class TestGetInstallSearchDirs:

    def test_windows_uses_appdata(self):
        dirs = get_install_search_dirs('win32', {'APPDATA': 'C:\\Users\\A\\AppData\\Roaming'}, 'unused')
        assert dirs == [
            os.path.join('C:\\Users\\A\\AppData\\Roaming', 'Autodesk', 'ApplicationPlugins'),
            os.path.join('C:\\Users\\A\\AppData\\Roaming', 'Autodesk', 'Autodesk Fusion 360', 'API', 'AddIns'),
        ]

    def test_windows_without_appdata_returns_nothing(self):
        assert get_install_search_dirs('win32', {}, 'unused') == []

    def test_macos_uses_library(self):
        dirs = get_install_search_dirs('darwin', {}, '/Users/a')
        base = os.path.join('/Users/a', 'Library', 'Application Support', 'Autodesk')
        assert dirs == [
            os.path.join(base, 'ApplicationPlugins'),
            os.path.join(base, 'Autodesk Fusion 360', 'API', 'AddIns'),
        ]

    def test_other_platform_returns_nothing(self):
        assert get_install_search_dirs('linux', {}, '/home/a') == []


class TestFindOtherInstalls:

    def setup_dirs(self, tmp_path):
        plugins = make_install(str(tmp_path), 'ApplicationPlugins')
        addins = make_install(str(tmp_path), 'Autodesk Fusion 360', 'API', 'AddIns')
        return plugins, addins

    def test_only_own_install_finds_nothing(self, tmp_path):
        plugins, addins = self.setup_dirs(tmp_path)
        own = make_install(addins, 'ThreadMeister')
        assert find_other_installs(own, [plugins, addins]) == []

    def test_app_store_bundle_found_from_manual_install(self, tmp_path):
        """The reporter's case: manual 1.2.4 next to the App Store bundle."""
        plugins, addins = self.setup_dirs(tmp_path)
        bundle = make_install(plugins, 'ThreadMeister.bundle')
        own = make_install(addins, 'ThreadMeister')
        assert find_other_installs(own, [plugins, addins]) == [bundle]

    def test_manual_install_found_from_inside_app_store_bundle(self, tmp_path):
        """The running copy lives somewhere inside the bundle, not at its root."""
        plugins, addins = self.setup_dirs(tmp_path)
        own = make_install(plugins, 'ThreadMeister.bundle', 'Contents', 'ThreadMeister')
        manual = make_install(addins, 'ThreadMeister')
        assert find_other_installs(own, [plugins, addins]) == [manual]

    def test_unrelated_add_ins_ignored(self, tmp_path):
        plugins, addins = self.setup_dirs(tmp_path)
        make_install(plugins, 'SpurGear.bundle')
        make_install(addins, 'TinkercadToFusion')
        own = make_install(addins, 'ThreadMeister')
        assert find_other_installs(own, [plugins, addins]) == []

    def test_files_named_like_the_add_in_ignored(self, tmp_path):
        plugins, addins = self.setup_dirs(tmp_path)
        open(os.path.join(addins, 'ThreadMeister.zip'), 'w').close()
        own = make_install(addins, 'ThreadMeister')
        assert find_other_installs(own, [plugins, addins]) == []

    def test_missing_search_dir_ignored(self, tmp_path):
        own = make_install(str(tmp_path), 'ThreadMeister')
        missing = os.path.join(str(tmp_path), 'does-not-exist')
        assert find_other_installs(own, [missing]) == []

    def test_similar_prefix_is_not_own_install(self, tmp_path):
        """'ThreadMeister' must not count as inside 'ThreadMeister-old'."""
        plugins, addins = self.setup_dirs(tmp_path)
        old = make_install(addins, 'ThreadMeister-old')
        own = make_install(addins, 'ThreadMeister')
        assert find_other_installs(own, [addins]) == [old]


def test_message_lists_every_path_and_the_fix():
    msg = duplicate_install_message(['C:\\a\\ThreadMeister.bundle', 'C:\\b\\ThreadMeister'])
    assert 'C:\\a\\ThreadMeister.bundle' in msg
    assert 'C:\\b\\ThreadMeister' in msg
    assert 'Run on Startup' in msg
