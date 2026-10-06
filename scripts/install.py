#!/usr/bin/env python3
"""Install the public local LIFE wiki into a fresh project, without sample records."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
EMPTY_WIKI = {"schema_version": 1, "revision": 0, "sources": [], "cards": [], "relations": [], "history": []}


def prepare_project(destination):
    """Reserve a new destination and copy the self-contained skill, never overwriting."""
    destination = Path(destination).expanduser().absolute()
    if not destination.parent.is_dir():
        raise ValueError("Destination parent folder must already exist.")
    # mkdir refuses existing directories, files, and symlinks, including empty ones.
    destination.mkdir(mode=0o700)
    skill = destination / ".agents" / "skills" / "life-wiki"
    shutil.copytree(ROOT / "skills" / "life-wiki", skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    viewer = skill / "assets" / "viewer"
    html = (viewer / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'<button id="demo"[^>]*>.*?</button>', '', html)
    html = html.replace('  <script defer src="demo-data.js"></script>\n', '')
    html = html.replace('가상 예제를 보거나, 내보낸 wiki.json을 선택하세요.', '자료를 정리하면 이 화면에 기록과 연결이 표시됩니다.')
    (viewer / "index.html").write_text(html, encoding="utf-8")
    (viewer / "demo-data.js").unlink()
    data = destination / "data"
    data.mkdir(mode=0o700)
    wiki = data / "wiki.json"
    wiki.write_text(json.dumps(EMPTY_WIKI, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    wiki.chmod(0o600)
    (destination / ".gitignore").write_text(".venv/\ndata/\nviewer*/\n*.lock\n.env*\n", encoding="utf-8")
    return destination, skill, wiki


def install(destination):
    destination, skill, wiki = prepare_project(destination)
    try:
        env = destination / ".venv"
        venv.EnvBuilder(with_pip=True).create(env)
        python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", "--no-cache-dir", "-r", str(skill / "requirements.txt")], check=True)
        helper = skill / "scripts" / "wiki.py"
        subprocess.run([str(python), str(helper), "validate", str(wiki)], check=True)
        subprocess.run([str(python), str(helper), "render", str(wiki), "--out", str(destination / "viewer")], check=True)
    except (OSError, subprocess.CalledProcessError):
        (destination / "INSTALL-INCOMPLETE.txt").write_text("Installation stopped. No sample or personal emails were imported. Review this incomplete folder before removing it; use a fresh destination for another installation.\n", encoding="utf-8")
        raise
    (destination / "OPEN-ME.txt").write_text("LIFE wiki local installation\n\n1. Continue in the same Codex conversation and ask it to read this project's .agents/skills/life-wiki/SKILL.md.\n2. Supply your own authorized material. Ask Codex to update data/wiki.json, validate it, and render to a fresh viewer directory.\n3. Open the resulting index.html. Its exported records load automatically; no JSON file selection is required.\n\nThe initial viewer has zero records. No email connection, hosting, automatic updates, or example records were installed.\n", encoding="utf-8")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True, help="New project folder; existing paths are never overwritten")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error("Python 3.10 or newer is required.")
    try:
        destination = install(args.dest)
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("Installation stopped. Check Python, internet access, destination permissions, and whether the destination already exists. Any incomplete folder is preserved; no existing project was overwritten.", file=sys.stderr)
        return 2
    print(f"Installed: {destination}\nContinue in the same Codex conversation; installed instructions: {destination / '.agents' / 'skills' / 'life-wiki' / 'SKILL.md'}\nViewer: {destination / 'viewer' / 'index.html'}\nRecords source (handled by Codex): {destination / 'data' / 'wiki.json'}\nNo sample records were installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
