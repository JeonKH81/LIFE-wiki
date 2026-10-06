import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("auto_load_helper", ROOT / "skills/life-wiki/scripts/wiki.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class AutoLoadTests(unittest.TestCase):
    def test_exported_script_preserves_snapshot_and_escapes_text(self):
        wiki = json.loads((ROOT / "examples/expected/wiki.json").read_text())
        wiki["cards"][0]["summary"] = '</script><img src=x onerror="bad()"> 한국어 & \u2028'
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "viewer"
            helper.render(wiki, dest)
            script = (dest / "initial-data.js").read_text()
            self.assertNotIn("<", script)
            self.assertNotIn("&", script)
            decoded = json.loads(script.split("window.LIFE_WIKI_INITIAL = ", 1)[1].removesuffix(";\n"))
            self.assertEqual(decoded, wiki)
            self.assertIn('src="initial-data.js"', (dest / "index.html").read_text())

    def test_empty_snapshot_is_ready_without_file_selection(self):
        wiki = {"schema_version": 1, "revision": 0, "cards": [], "sources": [], "relations": [], "history": []}
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "viewer"
            helper.render(wiki, dest)
            script = (dest / "initial-data.js").read_text()
            self.assertEqual(json.loads(script.split(" = ", 1)[1].removesuffix(";\n")), wiki)
