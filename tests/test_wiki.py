import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/life-wiki/scripts"))
import wiki


class WikiTests(unittest.TestCase):
    def setUp(self):
        self.w = wiki.read_json(ROOT / "examples/expected/wiki.json")
        self.inbox = wiki.read_json(ROOT / "examples/inbox.json")

    def operation(self, action="revise", **payload):
        return {"operation_id": "op-test", "expected_revision": self.w["revision"],
                "recorded_at": "2026-02-10T12:00:00Z", "reason": "User-directed fictional test.",
                "action": action, **payload}

    def revised(self):
        state = wiki.state_of(self.w)
        state["cards"][0]["summary"] += " Evidence reviewed."
        return self.operation(state=state)

    def merged(self):
        selected = [c for c in self.w["cards"] if c["id"] in {"work-lantern", "work-maple"}]
        replacement = copy.deepcopy(selected[0])
        replacement["id"] = "work-demonstration-kit"
        replacement["title"] = "Fictional demonstration kit"
        replacement["timeline"] = sorted(wiki.all_events(selected).values(), key=lambda e: (wiki.instant(e["source_timestamp"]), e["id"]))
        replacement["unknowns"] = list(dict.fromkeys(u for c in selected for u in c["unknowns"]))
        return self.operation("merge", card_ids=[c["id"] for c in selected], replacement=replacement)

    def split(self):
        original = self.w["cards"][0]
        a, b = copy.deepcopy(original), copy.deepcopy(original)
        a.update(id="work-pilot-decision", timeline=original["timeline"][:2], unknowns=[])
        b.update(id="work-launch-followup", status="unknown", timeline=original["timeline"][2:])
        return self.operation("split", card_id=original["id"], replacements=[a, b])

    def test_expected_snapshot_valid_without_network(self):
        with patch("socket.socket", side_effect=AssertionError("Network is forbidden in tests")):
            wiki.validate(self.w)

    def test_grouping_cross_thread_shared_subject_and_mixed_message(self):
        cards = wiki.index_unique(self.w["cards"], "card")
        self.assertEqual(len(cards), 4)
        by_identity = {wiki.normalized_key(m["message_key"]): m for m in self.inbox["messages"]}
        sources = wiki.index_unique(self.w["sources"], "source")
        threads = {by_identity[sources[e["source_id"]]["message_key"]]["thread_key"] for e in cards["work-lantern"]["timeline"]}
        self.assertGreaterEqual(len(threads), 2)
        same_subject = [m for m in self.inbox["messages"] if m["subject"] == "Weekly update"]
        self.assertEqual(len(same_subject), 2)
        maple_sources = {e["source_id"] for e in cards["work-maple"]["timeline"]}
        quartz_sources = {e["source_id"] for e in cards["work-quartz"]["timeline"]}
        self.assertFalse(maple_sources & quartz_sources)
        self.assertTrue(maple_sources & {e["source_id"] for e in cards["work-lantern"]["timeline"]})

    def test_approval_is_not_implementation_and_report_is_not_verification(self):
        cards = wiki.index_unique(self.w["cards"], "card")
        self.assertEqual(cards["work-lantern"]["status"], "approved")
        self.assertEqual(cards["work-lantern"]["outcome"]["state"], "unknown")
        self.assertEqual(cards["work-quartz"]["outcome"]["state"], "reported_implemented")
        self.w["cards"][2]["outcome"]["state"] = "verified_implemented"
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_uncertain_relationship_cannot_be_silently_confirmed(self):
        self.w["relations"][1]["certainty"] = "confirmed"
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_absent_implementation_evidence_rejected(self):
        self.w["cards"][0]["status"] = "implemented"
        self.w["cards"][0]["outcome"] = {"state": "reported_implemented", "evidence_ids": ["ev-lantern-approval"]}
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_inferred_completion_and_verification_rejected(self):
        self.w["cards"][2]["timeline"][0]["basis"] = "inferred"
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_provenance_missing_source_and_changed_quote_rejected(self):
        for field, value in [("source_id", "src-missing"), ("quote", "Invented completion evidence"), ("source_timestamp", "2026-01-01T00:00:00Z")]:
            candidate = copy.deepcopy(self.w)
            candidate["cards"][0]["timeline"][0][field] = value
            with self.subTest(field=field), self.assertRaises(wiki.WikiError): wiki.validate(candidate)

    def test_timezone_order_uses_instants(self):
        c = self.w["cards"][0]
        a, b = c["timeline"][:2]
        a["source_timestamp"] = "2026-02-04T10:00:00+09:00"
        b["source_timestamp"] = "2026-02-04T08:00:00Z"
        source_by_id = wiki.index_unique(self.w["sources"], "source")
        source_by_id[a["source_id"]]["sent_at"] = a["source_timestamp"]
        source_by_id[b["source_id"]]["sent_at"] = b["source_timestamp"]
        wiki.validate(self.w)
        c["timeline"][:2] = [b, a]
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_dedup_and_digest(self):
        sources = wiki.normalize_inbox(self.inbox)
        self.assertEqual(len(sources), 8)
        first = self.inbox["messages"][0]
        self.assertEqual(sources[0]["content_sha256"], hashlib.sha256(first["body"].encode()).hexdigest())
        self.assertNotEqual(sources[0]["sent_at"], sources[0]["captured_at"])

    def test_repeat_import_retains_original_minimized_metadata(self):
        self.inbox["captured_at"] = "2026-02-20T12:00:00Z"
        self.assertEqual(wiki.normalize_inbox(self.inbox, self.w), self.w["sources"])
        self.inbox["messages"][0]["body"] += " Conflicting correction."
        with self.assertRaises(wiki.WikiError): wiki.normalize_inbox(self.inbox, self.w)

    def test_mailbox_scoped_identity_and_forward_not_content_dedup(self):
        other = copy.deepcopy(self.inbox)
        other["account_scope"] = "fictional-inbox-b"
        self.assertNotEqual(wiki.normalize_inbox(other)[0]["id"], wiki.normalize_inbox(self.inbox)[0]["id"])
        forward = dict(other["messages"][0]); forward["message_key"] = "forwarded-copy@fiction.example"
        other["messages"].append(forward)
        self.assertEqual(len(wiki.normalize_inbox(other)), 9)

    def test_conflicting_duplicates_and_empty_id_rejected(self):
        self.inbox["messages"][-1]["body"] += " conflicting content"
        with self.assertRaises(wiki.WikiError): wiki.normalize_inbox(self.inbox)
        self.inbox["messages"][0]["message_key"] = "<>"
        with self.assertRaises(wiki.WikiError): wiki.normalize_inbox(self.inbox)

    def test_missing_timezone_and_unknown_properties_rejected(self):
        self.w["sources"][0]["sent_at"] = "2026-02-03T09:00:00"
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)
        self.w = wiki.read_json(ROOT / "examples/expected/wiki.json")
        self.w["cards"][0]["send_email"] = True
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_protected_update_card_revisions_and_exact_replay(self):
        op = self.revised()
        updated, changed = wiki.prepare(self.w, op)
        self.assertTrue(changed)
        self.assertEqual(updated["revision"], 1)
        self.assertEqual([c["revision"] for c in updated["cards"]], [1, 0, 0, 0])
        again, changed = wiki.prepare(updated, op)
        self.assertFalse(changed); self.assertEqual(updated, again)

    def test_stale_update_and_conflicting_operation_id_rejected(self):
        op = self.revised(); updated, _ = wiki.prepare(self.w, op)
        conflict = copy.deepcopy(op); conflict["reason"] = "Different request."
        with self.assertRaises(wiki.WikiError): wiki.prepare(updated, conflict)
        conflict["operation_id"] = "op-another"
        with self.assertRaises(wiki.WikiError): wiki.prepare(updated, conflict)

    def test_user_edit_detected_and_history_checksums_enforced(self):
        updated, _ = wiki.prepare(self.w, self.revised())
        updated["cards"][0]["summary"] = "Outside helper edit"
        with self.assertRaises(wiki.WikiError): wiki.validate(updated)
        updated, _ = wiki.prepare(self.w, self.revised())
        ref = updated["history"][0]["before"]["cards"][0]
        updated["history_objects"][ref]["summary"] += " corruption"
        with self.assertRaises(wiki.WikiError): wiki.validate(updated)

    def test_revise_cannot_remove_rewrite_or_retire_original_evidence(self):
        for mutate in [lambda s: s["sources"].pop(), lambda s: s["cards"][0]["timeline"].pop(), lambda s: s["cards"][0].update(lifecycle="retired", replaced_by=["work-maple"]), lambda s: s["cards"][0].update(revision=5), lambda s: s["cards"].pop()]:
            state = wiki.state_of(self.w); mutate(state)
            with self.assertRaises(wiki.WikiError): wiki.prepare(self.w, self.operation(state=state))

    def test_merge_preserves_evidence_questions_and_retired_lineage(self):
        updated, _ = wiki.prepare(self.w, self.merged())
        cards = wiki.index_unique(updated["cards"], "card")
        self.assertEqual(cards["work-lantern"]["lifecycle"], "retired")
        self.assertEqual(cards["work-maple"]["replaced_by"], ["work-demonstration-kit"])
        self.assertEqual(len(cards["work-demonstration-kit"]["timeline"]), 6)
        self.assertEqual(updated["relations"], self.w["relations"])
        self.assertEqual(wiki.snapshot_state(updated, updated["history"][0]["before"]), wiki.state_of(self.w))

    def test_merge_drops_and_existing_target_rejected(self):
        op = self.merged(); op["replacement"]["timeline"].pop()
        with self.assertRaises(wiki.WikiError): wiki.prepare(self.w, op)
        op = self.merged(); op["replacement"]["unknowns"] = []
        with self.assertRaises(wiki.WikiError): wiki.prepare(self.w, op)
        op = self.merged(); op["replacement"]["id"] = "work-quartz"
        with self.assertRaises(wiki.WikiError): wiki.prepare(self.w, op)

    def test_split_partition_and_duplicate_partition_rejected(self):
        op = self.split(); updated, _ = wiki.prepare(self.w, op)
        self.assertEqual(len(updated["cards"]), 6)
        self.assertEqual(updated["cards"][0]["replaced_by"], ["work-pilot-decision", "work-launch-followup"])
        op["replacements"][1]["timeline"].insert(0, op["replacements"][0]["timeline"][0])
        with self.assertRaises(wiki.WikiError): wiki.prepare(self.w, op)

    def test_undo_restores_content_and_appends_history_with_monotone_revision(self):
        updated, _ = wiki.prepare(self.w, self.merged())
        undo = self.operation("undo", target_operation_id="op-test"); undo.update(operation_id="op-undo", expected_revision=1)
        restored, _ = wiki.prepare(updated, undo)
        self.assertEqual(restored["revision"], 2); self.assertEqual(len(restored["history"]), 2)
        content = wiki.state_of(restored); content["revision"] = 0
        for c in content["cards"]: c["revision"] = 0
        self.assertEqual(content, wiki.state_of(self.w))
        self.assertGreater(restored["cards"][0]["revision"], updated["cards"][0]["revision"])
        undo["operation_id"] = "op-old-undo"; undo["expected_revision"] = 2
        with self.assertRaises(wiki.WikiError): wiki.prepare(restored, undo)

    def test_historical_card_source_and_event_ids_stay_protected_after_undo(self):
        state = wiki.state_of(self.w)
        source = copy.deepcopy(state["sources"][0]); source["message_key"] = "extra-message@fiction.example"
        source["id"] = wiki.source_id(source["account_scope"], source["message_key"])
        card = copy.deepcopy(state["cards"][0]); card["id"] = "work-extra"
        card["timeline"] = [copy.deepcopy(card["timeline"][0])]; card["status"] = "proposed"
        card["timeline"][0].update(id="ev-extra", source_id=source["id"])
        state["sources"].append(source); state["cards"].append(card)
        updated, _ = wiki.prepare(self.w, self.operation(state=state))
        op = self.operation("undo", target_operation_id="op-test"); op.update(operation_id="op-restore", expected_revision=1)
        restored, _ = wiki.prepare(updated, op)
        # Reintroduction cannot reset the original card's revision to zero.
        proposed = wiki.state_of(restored); proposed["cards"].append(card); proposed["sources"].append(source)
        op = self.operation(state=proposed); op.update(operation_id="op-reintroduce", expected_revision=2)
        with self.assertRaises(wiki.WikiError): wiki.prepare(restored, op)
        # Even with a fresh work ID, source/evidence identities cannot change contents.
        proposed["cards"][-1]["id"] = "work-extra-fresh"
        proposed["sources"][-1]["content_sha256"] = "0"*64
        with self.assertRaises(wiki.WikiError): wiki.prepare(restored, op)
        proposed["sources"][-1]["content_sha256"] = source["content_sha256"]
        proposed["cards"][-1]["timeline"][0]["summary"] += " Rewritten history."
        with self.assertRaises(wiki.WikiError): wiki.prepare(restored, op)

    def test_rejoining_replacement_graph_validation_remains_linear(self):
        import time
        base = copy.deepcopy(self.w["cards"][0]); base["id"] = "work-root"
        nodes = [base]; parent = base
        for i in range(22):
            left, right, merged = copy.deepcopy(base), copy.deepcopy(base), copy.deepcopy(base)
            left["id"], right["id"], merged["id"] = f"work-left-{i}", f"work-right-{i}", f"work-merged-{i}"
            parent.update(lifecycle="retired", replaced_by=[left["id"], right["id"]])
            left.update(lifecycle="retired", replaced_by=[merged["id"]])
            right.update(lifecycle="retired", replaced_by=[merged["id"]])
            merged.update(lifecycle="active", replaced_by=[])
            nodes.extend([left, right, merged]); parent = merged
        state = wiki.state_of(self.w); state.update(cards=nodes, relations=[])
        started = time.monotonic(); wiki.validate_state(state)
        self.assertLess(time.monotonic()-started, 2.0)

    def test_id_cannot_contain_final_newline(self):
        self.w["cards"][0]["id"] += "\n"; self.w["relations"][0]["from"] += "\n"
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_atomic_file_replay_lock_permissions_and_failed_update_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"wiki.json"; wiki.write_new_json(path, self.w)
            initial = path.read_bytes()
            path.with_name("wiki.json.lock").write_text("owner")
            with self.assertRaises(wiki.WikiError): wiki.apply_file(path, self.revised())
            self.assertEqual(path.read_bytes(), initial)
            path.with_name("wiki.json.lock").unlink()
            op = self.revised(); op["expected_revision"] = 100
            with self.assertRaises(wiki.WikiError): wiki.apply_file(path, op)
            self.assertEqual(path.read_bytes(), initial)
            op["expected_revision"] = 0; wiki.apply_file(path, op)
            self.assertFalse(path.with_name("wiki.json.lock").exists())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            current = path.read_bytes(); wiki.apply_file(path, op)
            self.assertEqual(path.read_bytes(), current)

    def test_symlink_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"real.json"; wiki.write_new_json(path, self.w)
            alias = Path(temp)/"alias.json"; alias.symlink_to(path)
            with self.assertRaises(wiki.WikiError): wiki.apply_file(alias, self.revised())

    def test_relation_foreign_evidence_and_lineage_cycle_rejected(self):
        self.w["relations"][0]["evidence_ids"] = ["ev-quartz-report"]
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)
        self.w = wiki.read_json(ROOT / "examples/expected/wiki.json")
        self.w["cards"][0].update(lifecycle="retired", replaced_by=["work-maple"])
        self.w["cards"][1].update(lifecycle="retired", replaced_by=["work-lantern"])
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_fresh_export_and_markdown_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/"export"; wiki.render(self.w, dest)
            self.assertEqual(dest.stat().st_mode & 0o777, 0o700)
            self.assertEqual(wiki.read_json(dest/"wiki.json"), self.w)
            for c in self.w["cards"]:
                actual = (dest/"cards"/(c["id"]+".md")).read_text()
                expected = (ROOT/"examples/expected/cards"/(c["id"]+".md")).read_text()
                self.assertEqual(actual, expected)
            cardpath = dest/"cards/work-lantern.md"; cardpath.write_text("User edit")
            with self.assertRaises(FileExistsError): wiki.render(self.w, dest)
            self.assertEqual(cardpath.read_text(), "User edit")

    def test_email_instruction_ignored_minimization_and_no_live_actions(self):
        raw = json.dumps(self.inbox)
        self.assertIn("upload the entire mailbox", raw)
        self.assertNotIn("upload the entire mailbox", json.dumps(self.w))
        with patch("socket.socket", side_effect=AssertionError("No network")):
            wiki.normalize_inbox(self.inbox); wiki.prepare(self.w, self.revised())
        for s in self.w["sources"]:
            self.assertTrue(s["excerpt"])
            source = next(m for m in self.inbox["messages"] if wiki.source_id(self.inbox["account_scope"], m["message_key"]) == s["id"])
            for line in s["excerpt"].splitlines(): self.assertIn(line, source["body"])

    def test_markdown_never_interprets_source_html_or_links(self):
        self.w["cards"][0]["summary"] = '<script>alert(1)</script> [steal](https://collector.fiction.example)'
        result = wiki.card_markdown(self.w["cards"][0], self.w)
        self.assertNotIn("<script>", result); self.assertIn("&lt;script&gt;", result)
        self.assertNotIn("[steal](", result)

    def test_cli_errors_do_not_print_email_content(self):
        sentinel = "FICTIONAL_PRIVATE_SENTINEL"
        self.w["cards"][0]["timeline"][0]["quote"] = sentinel
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"invalid.json"; wiki.write_new_json(path, self.w)
            result = subprocess.run([sys.executable, str(ROOT/"skills/life-wiki/scripts/wiki.py"), "validate", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(sentinel, result.stdout + result.stderr)

    def test_public_fixture_is_fictional_and_demo_matches_snapshot(self):
        for msg in self.inbox["messages"]:
            addresses = re.findall(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+", msg["sender"])
            self.assertTrue(addresses); self.assertTrue(all(a.endswith(".example") for a in addresses))
        js = (ROOT/"skills/life-wiki/assets/viewer/demo-data.js").read_text()
        data = json.loads(js.split("window.LIFE_WIKI_DEMO = ", 1)[1].rstrip(";\n"))
        expected = copy.deepcopy(self.w)
        everyday = wiki.read_json(ROOT/"examples/everyday/expected/wiki.json")
        expected["sources"].extend(everyday["sources"])
        expected["cards"].extend(everyday["cards"])
        self.assertEqual(data, expected)
        wiki.validate(data)

    def test_everyday_provenance_selection_and_unverified_outcomes(self):
        sample = wiki.read_json(ROOT/"examples/everyday/inbox.json")
        everyday = wiki.read_json(ROOT/"examples/everyday/expected/wiki.json")
        with patch("socket.socket", side_effect=AssertionError("No network")):
            normalized = wiki.normalize_inbox(sample)
            wiki.validate(everyday)
        self.assertEqual(len(normalized), 8)
        self.assertEqual(len(everyday["sources"]), 5)
        by_id = wiki.index_unique(normalized, "source")
        for source in everyday["sources"]:
            self.assertEqual(source, by_id[source["id"]])
        selected = {s["message_key"] for s in everyday["sources"]}
        self.assertTrue(all(key.endswith(".example") for key in selected))
        self.assertTrue(all(f"{key}@everyday.example" not in selected for key in ("receipt", "advert", "alert")))
        cards = wiki.index_unique(everyday["cards"], "card")
        self.assertEqual(cards["work-islet"]["status"], "requested")
        self.assertEqual(cards["work-islet"]["outcome"]["state"], "unknown")
        self.assertEqual(cards["work-pine"]["outcome"]["state"], "reported_implemented")
        self.assertFalse(any(e["verification"] for c in cards.values() for e in c["timeline"]))
        self.assertEqual(everyday["relations"], [])

    def test_everyday_export_matches_reviewed_cards(self):
        everyday = wiki.read_json(ROOT/"examples/everyday/expected/wiki.json")
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)/"everyday-export"
            wiki.render(everyday, destination)
            self.assertEqual(wiki.read_json(destination/"wiki.json"), everyday)
            for card in everyday["cards"]:
                name = card["id"] + ".md"
                self.assertEqual((destination/"cards"/name).read_text(),
                                 (ROOT/"examples/everyday/expected/cards"/name).read_text())

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"duplicate.json"; path.write_text('{"revision":0,"revision":1}')
            with self.assertRaises(wiki.WikiError): wiki.read_json(path)

    def test_copied_skill_is_self_contained(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            installed = Path(temp)/".agents/skills/life-wiki"
            shutil.copytree(ROOT/"skills/life-wiki", installed, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            self.assertTrue((installed/"requirements.txt").is_file())
            fixture = Path(temp)/"wiki.json"; wiki.write_new_json(fixture, self.w)
            result = subprocess.run([sys.executable, str(installed/"scripts/wiki.py"), "validate", str(fixture)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("4 cards", result.stdout)

    @unittest.skipUnless(__import__("shutil").which("node"), "Node unavailable for viewer checks")
    def test_viewer_search_safety_and_interactions(self):
        result = subprocess.run(["node", str(ROOT/"tests/viewer.test.js")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__": unittest.main()
