"""Installation must never replace an existing destination or seed fake records."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("life_install", Path(__file__).resolve().parents[1] / "scripts" / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_new_project_has_empty_wiki_and_no_sample_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, skill, wiki = installer.prepare_project(Path(tmp) / "new-project")
            self.assertEqual(json.loads(wiki.read_text()), installer.EMPTY_WIKI)
            self.assertTrue((skill / "scripts" / "wiki.py").is_file())
            self.assertTrue((skill / "assets" / "viewer" / "graph.js").is_file())
            html = (skill / "assets" / "viewer" / "index.html").read_text()
            self.assertNotIn('id="demo"', html)
            self.assertNotIn("demo-data.js", html)
            self.assertFalse((skill / "assets" / "viewer" / "demo-data.js").exists())
            self.assertEqual(html.count('id="nav-'), 7)
            self.assertIn("data/", (root / ".gitignore").read_text())

    def test_existing_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "existing"
            dest.mkdir()
            sentinel = dest / "my-record.txt"
            sentinel.write_text("keep this unrelated record")
            with self.assertRaises(FileExistsError):
                installer.prepare_project(dest)
            self.assertEqual(sentinel.read_text(), "keep this unrelated record")
            self.assertFalse((dest / ".agents").exists())

    def test_existing_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "link"
            target = Path(tmp) / "existing"
            target.mkdir()
            dest.symlink_to(target, target_is_directory=True)
            with self.assertRaises(FileExistsError):
                installer.prepare_project(dest)
            self.assertEqual(list(target.iterdir()), [])

    def test_missing_parent_is_reported_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "missing" / "new-project"
            with self.assertRaises(ValueError):
                installer.prepare_project(dest)
            self.assertFalse(dest.exists())
