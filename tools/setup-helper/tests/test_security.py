import unittest
import tempfile
import shutil
import os
from pathlib import Path
from talos_setup_helper.jail import WorkspaceJail, JailError
from talos_setup_helper.manifest import ManifestManager, ManifestError

class TestWorkspaceJail(unittest.TestCase):
    def setUp(self):
        self.test_dir_raw = tempfile.mkdtemp()
        self.test_dir = str(Path(self.test_dir_raw).resolve())
        self.jail = WorkspaceJail(Path(self.test_dir))

    def tearDown(self):
        shutil.rmtree(self.test_dir_raw)

    def test_valid_access(self):
        """Test access to a valid path inside the jail"""
        path = self.jail._validate_path("foo/bar.txt")
        self.assertTrue(str(path).startswith(self.test_dir))

    def test_path_traversal(self):
        """Test rejection of .. traversal"""
        with self.assertRaises(JailError):
            self.jail._validate_path("../outside.txt")
            
        with self.assertRaises(JailError):
            self.jail._validate_path("foo/../../etc/passwd")

    def test_absolute_path(self):
        """Test rejection of absolute paths"""
        with self.assertRaises(JailError):
            self.jail._validate_path("/etc/passwd")

    def test_symlink_escape(self):
        """Test rejection of paths containing symlinks"""
        # Create a malicious symlink pointing outside
        target = Path(self.test_dir) / "link_to_root"
        os.symlink("/", target)
        
        with self.assertRaises(JailError):
            self.jail._validate_path("link_to_root/etc/passwd")

class TestManifestManager(unittest.TestCase):
    def test_load_bundled_manifest(self):
        """Test that the real bundled manifest loads correctly"""
        mgr = ManifestManager()
        self.assertIsNotNone(mgr._manifest)
        self.assertIn("recipes", mgr._manifest)

    def test_get_recipe(self):
        mgr = ManifestManager()
        recipe = mgr.get_recipe("talos-sdk-init")
        self.assertEqual(recipe["id"], "talos-sdk-init")

    def test_unknown_recipe(self):
        mgr = ManifestManager()
        with self.assertRaises(ManifestError):
            mgr.get_recipe("malicious-recipe")

if __name__ == '__main__':
    unittest.main()
