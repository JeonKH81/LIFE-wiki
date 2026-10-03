"""Regression checks for the 2026-10-03 review, using fictional copies only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/life-wiki/scripts"))
import wiki


class ReviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.w = wiki.read_json(ROOT / "examples/expected/wiki.json")
        self.inbox = wiki.read_json(ROOT / "examples/inbox.json")

    def operation(self, current=None, **values):
        current = current or self.w
        return {"operation_id": "review-op", "expected_revision": current["revision"],
                "recorded_at": "2026-10-03T12:00:00Z", "reason": "Fictional review regression.", **values}

    def revise(self, current, op_id="review-revise"):
        state = wiki.state_of(current)
        state["cards"][0]["summary"] += " Reviewed."
        return wiki.prepare(current, self.operation(current, operation_id=op_id, action="revise", state=state))[0]

    def legacy(self, compact):
        return {**wiki.state_of(compact), "history": [
            {**h, "before": copy.deepcopy(wiki.snapshot_state(compact, h["before"])),
             "after": copy.deepcopy(wiki.snapshot_state(compact, h["after"]))} for h in compact["history"]]}

    def test_timestamp_checks_do_not_depend_on_optional_format_packages(self):
        with patch("jsonschema.FormatChecker.check", return_value=None):
            op = self.operation(action="revise", state=wiki.state_of(self.w), recorded_at="not-a-time")
            with self.assertRaises(wiki.WikiError): wiki.prepare(self.w, op)
            changed = self.revise(self.w)
            changed["history"][0]["recorded_at"] = "not-a-time"
            with self.assertRaises(wiki.WikiError): wiki.validate(changed)

    def test_portable_lowercase_timezone_and_arbitrary_fraction_lengths(self):
        for fraction in ["1", "12", "1234", "123456789"]:
            lower = "2026-10-03t12:00:00." + fraction + "z"
            self.assertEqual(wiki.instant(lower), wiki.instant(lower.upper()))
        for invalid in ["2026-02-30T12:00:00Z", "2026-10-03 12:00:00Z", "2026-10-03T12:00:00+24:00", "2026-10-03T12:00:00+00:99", "2026-10-03T12:00:00Z\n", "2026-10-03T12:00:60Z", "9999-12-31T23:59:59-23:59", "0001-01-01T00:00:00+23:59"]:
            with self.subTest(value=invalid), self.assertRaises(wiki.WikiError): wiki.instant(invalid)

    def test_all_timestamp_locations_accept_lowercase_and_reject_invalid_dates(self):
        self.w["sources"][0]["sent_at"] = self.w["sources"][0]["sent_at"].lower()
        for card in self.w["cards"]:
            for event in card["timeline"]:
                if event["source_id"] == self.w["sources"][0]["id"]:
                    event["source_timestamp"] = self.w["sources"][0]["sent_at"]
        wiki.validate(self.w)
        for key in ["captured_at", "sent_at"]:
            bad = copy.deepcopy(self.w)
            bad["sources"][0][key] = "not-a-time"
            with self.assertRaises(wiki.WikiError): wiki.validate(bad)

    def test_korean_composition_and_line_endings_share_digest(self):
        self.inbox["messages"] = [self.inbox["messages"][0]]
        self.inbox["messages"][0]["body"] = "승인했습니다.\r\n다음 단계"
        composed = wiki.normalize_inbox(self.inbox)
        self.inbox["messages"][0]["body"] = unicodedata.normalize("NFD", "승인했습니다.\n다음 단계")
        self.assertEqual(wiki.normalize_inbox(self.inbox), composed)
        self.assertEqual(composed[0]["excerpt"], "승인했습니다.\n다음 단계")

    def test_korean_quote_validation_accepts_only_canonical_equivalence(self):
        event = self.w["cards"][0]["timeline"][0]
        source = next(s for s in self.w["sources"] if s["id"] == event["source_id"])
        source["excerpt"] = "이 업무를\r\n승인했습니다."
        event["quote"] = unicodedata.normalize("NFD", "업무를\n승인했습니다.")
        wiki.validate(self.w)
        event["quote"] = "승인하지 않았습니다."
        with self.assertRaises(wiki.WikiError): wiki.validate(self.w)

    def test_legacy_nfd_source_digest_is_preserved_on_repeat_import(self):
        self.inbox["messages"] = [self.inbox["messages"][0]]
        body = unicodedata.normalize("NFD", "가상 검토 본문")
        self.inbox["messages"][0]["body"] = body
        source = wiki.normalize_inbox(self.inbox)[0]
        source.update(excerpt=body, content_sha256=hashlib.sha256(body.encode()).hexdigest())
        existing = {"schema_version": 1, "revision": 0, "sources": [source], "cards": [], "relations": [], "history": []}
        self.assertEqual(wiki.normalize_inbox(self.inbox, existing), [source])
        self.inbox["messages"][0]["body"] = unicodedata.normalize("NFC", body)
        self.assertEqual(wiki.normalize_inbox(self.inbox, existing), [source])

    def test_compact_history_preserves_legacy_state_hashes_and_migrates_on_change(self):
        first = self.revise(self.w)
        legacy = self.legacy(first)
        wiki.validate(legacy)
        self.assertEqual(wiki.pack_history(legacy), first)
        second = self.revise(legacy, "review-second")
        self.assertEqual(second["history"][0]["before_sha256"], legacy["history"][0]["before_sha256"])
        self.assertEqual(second["history_format"], "content-addressed-v1")
        undo = self.operation(second, operation_id="review-undo", action="undo", target_operation_id="review-second")
        restored, _ = wiki.prepare(second, undo)
        self.assertEqual(restored["cards"][0]["summary"], first["cards"][0]["summary"])
        self.assertGreater(restored["cards"][0]["revision"], second["cards"][0]["revision"])

    def test_compact_history_rejects_missing_changed_unused_objects_and_broken_chain(self):
        good = self.revise(self.revise(self.w), "review-second")
        for mutation in [
            lambda w: w["history_objects"].pop(next(iter(w["history_objects"]))),
            lambda w: w["history_objects"][next(iter(w["history_objects"]))].update(excerpt="Changed"),
            lambda w: w["history_objects"].update({wiki.digest({"unused": True}): {"unused": True}}),
            lambda w: w["history"][1].update(before=copy.deepcopy(w["history"][0]["before"])),
        ]:
            bad = copy.deepcopy(good); mutation(bad)
            with self.assertRaises(wiki.WikiError): wiki.validate(bad)

    def test_repeated_small_edits_store_shared_sources_once_and_reduce_size(self):
        current = self.w
        for number in range(12): current = self.revise(current, f"review-{number}")
        self.assertEqual(len(current["history_objects"]), len(self.w["sources"]) + len(self.w["cards"]) + len(self.w["relations"]) + 12)
        self.assertLess(len(json.dumps(current)), len(json.dumps(self.legacy(current))) // 3)

    def private_fixture(self):
        sentinel = "FICTIONAL_REDACTION_SENTINEL"
        source = self.w["sources"][0]
        key = source["message_key"]
        for message in self.inbox["messages"]:
            if wiki.normalized_key(message["message_key"]) == key:
                message["body"] += "\n" + sentinel
                source["content_sha256"] = hashlib.sha256(wiki.normalized_text(message["body"]).encode()).hexdigest()
        source["excerpt"] += "\n" + sentinel
        source["uri"] = "private://" + sentinel
        for card in self.w["cards"]:
            if any(e["source_id"] == source["id"] for e in card["timeline"]):
                card["title"] += sentinel; card["summary"] += sentinel; card["unknowns"].append(sentinel)
                for event in card["timeline"]:
                    if event["source_id"] == source["id"]:
                        event.update(quote=sentinel, summary=sentinel)
        for relation in self.w["relations"]: relation["rationale"] += sentinel
        state = wiki.state_of(self.w); state["cards"][0]["summary"] += " Changed."
        prior, _ = wiki.prepare(self.w, self.operation(action="revise", state=state, reason=sentinel))
        op = self.operation(prior, operation_id="review-redact", action="redact", source_ids=[source["id"]], actor="privacy-test", reason=sentinel)
        redacted, _ = wiki.prepare(prior, op)
        return sentinel, prior, redacted, op

    def test_redaction_scrubs_current_history_objects_metadata_and_derived_cards(self):
        sentinel, prior, redacted, op = self.private_fixture()
        self.assertNotIn(sentinel, wiki.canonical(redacted))
        audit = redacted["history"][-1]["redaction"]
        self.assertEqual(audit["previous_wiki_sha256"], wiki.digest(prior))
        self.assertEqual(audit["reason_sha256"], wiki.digest(sentinel))
        self.assertIn("work-lantern", audit["card_ids"])
        self.assertIn("work-maple", audit["card_ids"])
        for state in [redacted] + list(wiki.history_states(redacted)):
            for source in state["sources"]:
                if source["id"] in audit["source_ids"]:
                    self.assertTrue(source["redacted"])
                    self.assertFalse(set(source) & {"message_key", "account_scope", "uri"})
            for card in state["cards"]:
                if card["id"] in audit["card_ids"]:
                    self.assertEqual(card["status"], "unknown")
                    self.assertEqual(card["outcome"], {"state": "unknown", "evidence_ids": []})
        replay, changed = wiki.prepare(redacted, op)
        self.assertFalse(changed); self.assertEqual(replay, redacted)

    def test_redaction_cannot_be_undone_and_repeat_import_keeps_tombstone(self):
        sentinel, prior, redacted, op = self.private_fixture()
        undo = self.operation(redacted, action="undo", target_operation_id=op["operation_id"])
        with self.assertRaises(wiki.WikiError): wiki.prepare(redacted, undo)
        imported = wiki.normalize_inbox(self.inbox, redacted)
        self.assertNotIn(sentinel, wiki.canonical(imported))
        self.assertTrue(next(s for s in imported if s["id"] == op["source_ids"][0])["redacted"])
        changed = self.revise(redacted, "review-after-redact")
        undo = self.operation(changed, operation_id="review-undo-after-redact", action="undo", target_operation_id="review-after-redact")
        restored, _ = wiki.prepare(changed, undo)
        self.assertNotIn(sentinel, wiki.canonical(restored))
        state = wiki.state_of(redacted)
        state["sources"] = copy.deepcopy(prior["sources"])
        with self.assertRaises(wiki.WikiError): wiki.prepare(redacted, self.operation(redacted, action="revise", state=state))

    def test_redaction_of_historical_source_survives_removal_by_undo(self):
        state = wiki.state_of(self.w)
        source = copy.deepcopy(state["sources"][0])
        source["message_key"] = "fictional-extra@fiction.example"
        source["id"] = wiki.source_id(source["account_scope"], source["message_key"])
        state["sources"].append(source)
        added, _ = wiki.prepare(self.w, self.operation(action="revise", state=state))
        undone, _ = wiki.prepare(added, self.operation(added, operation_id="review-undo", action="undo", target_operation_id="review-op"))
        redacted, _ = wiki.prepare(undone, self.operation(undone, operation_id="review-redact", action="redact", source_ids=[source["id"]], actor="privacy-test"))
        self.assertIn(source["id"], redacted["history"][-1]["redaction"]["source_ids"])
        state = wiki.state_of(redacted); state["sources"].append(source)
        with self.assertRaises(wiki.WikiError): wiki.prepare(redacted, self.operation(redacted, action="revise", state=state))

    def test_redaction_failure_preserves_original_file_and_cleans_temporary_files(self):
        _, prior, _, operation = self.private_fixture()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "wiki.json"; wiki.write_new_json(path, prior)
            original = path.read_bytes()
            with patch.object(wiki.os, "replace", side_effect=OSError("Fictional write failure")):
                with self.assertRaises(OSError): wiki.apply_file(path, operation)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual([p.name for p in Path(temp).iterdir()], ["wiki.json"])

    def test_redaction_preview_is_read_only_and_contains_no_source_text(self):
        sentinel, prior, _, operation = self.private_fixture()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "wiki.json"; wiki.write_new_json(path, prior)
            original = path.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / "skills/life-wiki/scripts/wiki.py"), "redact-preview", str(path), "--source-id", operation["source_ids"][0]], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(sentinel, result.stdout + result.stderr)
            self.assertIn(operation["source_ids"][0], json.loads(result.stdout)["source_ids"])
            self.assertEqual(path.read_bytes(), original)

    def test_export_failure_leaves_no_partial_destination_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "export"
            with patch.object(wiki, "card_markdown", side_effect=OSError("Fictional render failure")):
                with self.assertRaises(OSError): wiki.render(self.w, dest)
            self.assertFalse(dest.exists()); self.assertEqual(list(Path(temp).iterdir()), [])
            wiki.render(self.w, dest)
            self.assertTrue((dest / "cards/work-lantern.md").is_file())

    def test_exclusive_export_rename_does_not_replace_empty_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            src, dest = Path(temp) / "src", Path(temp) / "dest"
            src.mkdir(); dest.mkdir()
            (src / "marker").write_text("Fictional export")
            with self.assertRaises(FileExistsError): wiki.rename_new_directory(src, dest)
            self.assertTrue((src / "marker").is_file()); self.assertEqual(list(dest.iterdir()), [])

    def test_render_and_viewer_accept_compact_redacted_snapshot(self):
        _, _, redacted, _ = self.private_fixture()
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "export"; wiki.render(redacted, dest)
            self.assertIn("redact", (dest / "cards/work-lantern.md").read_text())
            result = subprocess.run(["node", "-e", "require(process.argv[1]).checkWiki(JSON.parse(require('node:fs').readFileSync(process.argv[2], 'utf8')))", str(ROOT / "skills/life-wiki/assets/viewer/app.js"), str(dest / "wiki.json")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__": unittest.main()
