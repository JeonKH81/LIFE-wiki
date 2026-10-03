#!/usr/bin/env python3
"""Offline evidence validation, protected transactions, and portable export."""
import argparse
import copy
import ctypes
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata
from functools import lru_cache
from datetime import datetime, timezone

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SKILL_ROOT = Path(__file__).resolve().parents[1]


class WikiError(ValueError):
    """Actionable errors without echoing email contents."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def read_json(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise WikiError("Duplicate JSON object key; resolve the input conflict.")
            result[key] = value
        return result
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise WikiError("Invalid UTF-8 JSON; check the input locally.") from exc


@lru_cache(maxsize=None)
def schema_validator(name):
    schemas = [json.loads(p.read_text()) for p in (SKILL_ROOT / "schemas").glob("*.json")]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    schema = next(s for s in schemas if s["$id"].endswith("/" + name + ".schema.json"))
    checker = FormatChecker()
    # Never rely on an optional jsonschema format dependency for timestamps.
    @checker.checks("date-time", raises=WikiError)
    def date_time(value):
        if not isinstance(value, str):
            return True  # The schema's type check handles this.
        instant(value)
        return True
    return Draft202012Validator(schema, registry=registry, format_checker=checker)


def schema_validate(value, name):
    errors = list(schema_validator(name).iter_errors(value))
    if errors:
        # jsonschema messages can contain raw input: do not echo them.
        raise WikiError(f"{name} schema check failed ({len(errors)} issue(s)); inspect input against schemas.")


def instant(value):
    try:
        # Strict, portable RFC 3339 subset: reject impossible dates and leap
        # seconds (datetime cannot represent them); accept lowercase t/z.
        match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[Tt](\d{2}:\d{2}:\d{2})(?:\.(\d+))?([Zz]|[+-]\d{2}:\d{2})", value)
        if match is None:
            raise ValueError
        day, clock, fraction, zone = match.groups()
        if zone not in {"Z", "z"} and (int(zone[1:3]) > 23 or int(zone[4:]) > 59):
            raise ValueError
        normalized = day + "T" + clock
        if fraction:
            normalized += "." + (fraction + "000000")[:6]
        normalized += "+00:00" if zone in {"Z", "z"} else zone
        dt = datetime.fromisoformat(normalized)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError) as exc:
        raise WikiError("Timestamps need valid RFC 3339 dates and a representable UTC instant; leap seconds are unsupported.") from exc


def normalized_text(value):
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def normalized_key(value):
    return value.strip().strip("<>").strip()


def source_id(scope, key):
    return "src-" + digest([scope, normalized_key(key)])[:24]


def normalize_inbox(inbox, existing=None):
    if not isinstance(inbox, dict) or set(inbox) != {"account_scope", "captured_at", "messages"}:
        raise WikiError("Inbox needs account_scope, captured_at, and messages.")
    scope = inbox["account_scope"]
    if not isinstance(scope, str) or not scope.strip():
        raise WikiError("A stable nonempty mailbox alias is required.")
    instant(inbox["captured_at"])
    if not isinstance(inbox["messages"], list):
        raise WikiError("Inbox messages must be an array.")
    retained = {}
    if existing is not None:
        validate(existing)
        snapshots = [existing] + list(history_states(existing))
        for state in snapshots:
            for source in state["sources"]:
                retained[source["id"]] = source
    sources = {}
    for message in inbox["messages"]:
        required = {"message_key", "thread_key", "sent_at", "subject", "body"}
        if not isinstance(message, dict) or not required <= set(message) or set(message) - required - {"sender"}:
            raise WikiError("Each message needs stable identity, thread, sent_at, subject, and body.")
        if any(not isinstance(message[k], str) or not message[k].strip() for k in required):
            raise WikiError("Message fields must be nonempty strings.")
        key = normalized_key(message["message_key"])
        if not key:
            raise WikiError("Message identity is empty after normalization.")
        instant(message["sent_at"])
        body = normalized_text(message["body"])
        sid = source_id(scope, key)
        source = {"id": sid, "account_scope": scope, "message_key": key,
                  "sent_at": message["sent_at"], "captured_at": inbox["captured_at"],
                  "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(), "excerpt": body}
        prior = retained.get(sid)
        if prior is not None:
            keys = ["sent_at", "content_sha256"] if prior.get("redacted") else ["account_scope", "message_key", "sent_at", "content_sha256"]
            legacy_hash = hashlib.sha256(message["body"].replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")).hexdigest()
            legacy_nfd_hash = hashlib.sha256(unicodedata.normalize("NFD", body).encode("utf-8")).hexdigest()
            hashes = {source["content_sha256"], legacy_hash, legacy_nfd_hash}
            if any(prior[k] != source[k] for k in keys if k != "content_sha256") or prior["content_sha256"] not in hashes:
                raise WikiError("Conflicting existing message identity; no source was overwritten.")
            source = copy.deepcopy(prior)
        if sid in sources and sources[sid] != source:
            raise WikiError("Conflicting repeated message identity; no source was overwritten.")
        sources[sid] = source
    result = sorted(sources.values(), key=lambda s: (instant(s["sent_at"]), s["id"]))
    schema_validate(result, "provenance")
    return result


def state_of(wiki):
    return copy.deepcopy({k: wiki[k] for k in ["schema_version", "revision", "sources", "cards", "relations"]})


def snapshot_state(wiki, snapshot):
    if snapshot.get("encoding") != "sha256-refs":
        return snapshot
    objects = wiki.get("history_objects", {})
    try:
        return {"schema_version": snapshot["schema_version"], "revision": snapshot["revision"],
                **{key: [objects[ref] for ref in snapshot[key]] for key in ["sources", "cards", "relations"]}}
    except KeyError as exc:
        raise WikiError("History references a missing object.") from exc


def history_states(wiki):
    for entry in wiki["history"]:
        yield snapshot_state(wiki, entry["before"])
        yield snapshot_state(wiki, entry["after"])


def pack_history(wiki):
    """Store immutable sources/cards/relations once, with small state manifests."""
    objects, entries = {}, []
    for entry in wiki["history"]:
        packed = {k: copy.deepcopy(v) for k, v in entry.items() if k not in {"before", "after"}}
        for side in ["before", "after"]:
            state = snapshot_state(wiki, entry[side])
            manifest = {"encoding": "sha256-refs", "schema_version": 1, "revision": state["revision"]}
            for key in ["sources", "cards", "relations"]:
                manifest[key] = []
                for item in state[key]:
                    ref = digest(item)
                    if ref not in objects:
                        objects[ref] = copy.deepcopy(item)
                    manifest[key].append(ref)
            packed[side] = manifest
        entries.append(packed)
    return {**state_of(wiki), "history": entries, "history_format": "content-addressed-v1", "history_objects": objects}


def index_unique(items, label):
    result = {}
    for item in items:
        if item["id"] in result:
            raise WikiError(f"Duplicate {label} ID.")
        result[item["id"]] = item
    return result


def validate_state(state):
    # Called after structural schema validation, including for history snapshots.
    sources = index_unique(state["sources"], "source")
    identities = set()
    for s in sources.values():
        if s.get("redacted"):
            if s["excerpt"] != "[Redacted]" or any(k in s for k in ["uri", "account_scope", "message_key"]):
                raise WikiError("Redacted sources must contain only tombstone metadata.")
            instant(s["sent_at"])
            instant(s["captured_at"])
            continue
        key = normalized_key(s["message_key"])
        if key != s["message_key"] or not key or s["id"] != source_id(s["account_scope"], key):
            raise WikiError("Source ID/normalized identity mismatch.")
        identity = (s["account_scope"], key)
        if identity in identities:
            raise WikiError("Repeated mailbox/message identity.")
        identities.add(identity)
        instant(s["sent_at"])
        instant(s["captured_at"])
    cards = index_unique(state["cards"], "card")
    events = {}
    for c in cards.values():
        local = index_unique(c["timeline"], "timeline event")
        ordered = sorted(c["timeline"], key=lambda e: (instant(e["source_timestamp"]), e["id"]))
        if c["timeline"] != ordered:
            raise WikiError("Timeline must be ordered by timestamp instant, then event ID.")
        for e in local.values():
            source = sources.get(e["source_id"])
            if source is None or e["source_timestamp"] != source["sent_at"]:
                raise WikiError("Evidence references a missing source or a changed source timestamp.")
            if normalized_text(e["quote"]) not in normalized_text(source["excerpt"]):
                raise WikiError("Evidence quote must match the retained source excerpt exactly.")
            if source.get("redacted") and (e["quote"] != "[Redacted]" or e["summary"] != "[Redacted]" or e["kind"] != "unknown" or e["verification"] or e["basis"] != "inferred"):
                raise WikiError("Redacted evidence cannot retain text or support a conclusion.")
            if e["id"] in events and e != events[e["id"]]:
                raise WikiError("Evidence ID reused with different contents.")
            events[e["id"]] = e
            if e["verification"] and (e["kind"] != "implemented" or e["basis"] != "explicit"):
                raise WikiError("Verification must cite explicit implementation evidence.")
        if c["status"] != "unknown" and not any(e["kind"] == c["status"] for e in local.values()):
            raise WikiError("Card status has no corresponding evidence assertion.")
        if c["status"] == "implemented" and not any(e["kind"] == "implemented" and e["basis"] == "explicit" for e in local.values()):
            raise WikiError("Implemented status requires explicit evidence.")
        outcome = c["outcome"]
        if outcome["state"] == "unknown":
            if outcome["evidence_ids"] or c["status"] == "implemented":
                raise WikiError("Unknown outcome cannot claim implementation evidence or status.")
        else:
            if c["status"] != "implemented" or not outcome["evidence_ids"]:
                raise WikiError("Implementation outcome needs implemented status and evidence.")
            for eid in outcome["evidence_ids"]:
                e = local.get(eid)
                if e is None or e["kind"] != "implemented" or e["basis"] != "explicit":
                    raise WikiError("Implementation outcome cites invalid evidence.")
                if outcome["state"] == "verified_implemented" and not e["verification"]:
                    raise WikiError("Verified outcome needs independently checked evidence.")
        replacements = c["replaced_by"]
        if (c["lifecycle"] == "active" and replacements) or (c["lifecycle"] == "retired" and not replacements):
            raise WikiError("Lifecycle and replacement list disagree.")
        if any(cid not in cards or cid == c["id"] for cid in replacements):
            raise WikiError("Replacement refers to a missing card or itself.")
    # Retired lineage must stay traversable, with no cycles.
    completed = set()
    def walk(cid, ancestors):
        if cid in ancestors:
            raise WikiError("Replacement lineage contains a cycle.")
        if cid in completed:
            return
        for successor in cards[cid]["replaced_by"]:
            walk(successor, ancestors | {cid})
        completed.add(cid)
    for cid in cards:
        walk(cid, set())
    index_unique(state["relations"], "relation")
    for r in state["relations"]:
        if r["from"] not in cards or r["to"] not in cards or r["from"] == r["to"]:
            raise WikiError("Relation needs two distinct existing cards.")
        instant(r["recorded_at"])
        endpoint_evidence = {e["id"] for cid in [r["from"], r["to"]] for e in cards[cid]["timeline"]}
        if any(eid not in endpoint_evidence for eid in r["evidence_ids"]):
            raise WikiError("Relation evidence must belong to an endpoint.")
        if r["certainty"] == "confirmed" and not r["evidence_ids"]:
            raise WikiError("Confirmed relation requires supporting evidence.")
        if r["type"] == "possible_same_work" and r["certainty"] != "uncertain":
            raise WikiError("Possible same work must remain uncertain.")


def validate(wiki):
    schema_validate(wiki, "wiki")
    validate_state(wiki)
    objects = wiki.get("history_objects", {})
    if objects and wiki.get("history_format") != "content-addressed-v1":
        raise WikiError("History object storage needs a supported format marker.")
    for ref, item in objects.items():
        if digest(item) != ref:
            raise WikiError("History object checksum mismatch.")
    used_objects = set()
    checked_states = set()
    checked_items = set()
    audited_redactions = {}
    for entry in wiki["history"]:
        if entry["action"] == "redact":
            audit = entry["redaction"]
            if set(audit["source_ids"]) != set(audit["original_content_sha256"]):
                raise WikiError("Redaction audit source identities disagree.")
            for sid, original_hash in audit["original_content_sha256"].items():
                if sid in audited_redactions and audited_redactions[sid] != original_hash:
                    raise WikiError("Redaction audit original source hashes disagree.")
                audited_redactions[sid] = original_hash
    def check_state(state):
        state_hash = digest(state)
        if state_hash in checked_states:
            return
        # Validate each shared object once per validation, not once per revision.
        for key, schema_ref in [("sources", "provenance.schema.json#/$defs/source"),
                                ("cards", "card.schema.json"),
                                ("relations", "relations.schema.json#/$defs/relation")]:
            for item in state[key]:
                identity = (key, digest(item))
                if identity not in checked_items:
                    validator = schema_validator("wiki").evolve(schema={"$ref": "https://life-wiki.invalid/schemas/" + schema_ref})
                    if not validator.is_valid(item):
                        raise WikiError("Historical object schema check failed; inspect input locally.")
                    checked_items.add(identity)
        validate_state(state)
        checked_states.add(state_hash)
    previous = None
    seen = set()
    lifetime_sources, lifetime_events, lifetime_cards = {}, {}, {}
    def remember(state):
        for source in state["sources"]:
            sid = source["id"]
            if source.get("redacted") and audited_redactions.get(sid) != source["content_sha256"]:
                raise WikiError("Redacted evidence needs a matching permanent audit record.")
            if sid in lifetime_sources and lifetime_sources[sid] != source:
                raise WikiError("A source identity conflicts with its historical contents.")
            lifetime_sources[sid] = source
        for card in state["cards"]:
            old = lifetime_cards.get(card["id"])
            if old is not None and (card["revision"] < old["revision"] or (card["revision"] == old["revision"] and card != old)):
                raise WikiError("Card contents changed without a new revision, or revision regressed.")
            lifetime_cards[card["id"]] = card
            for event in card["timeline"]:
                eid = event["id"]
                if eid in lifetime_events and lifetime_events[eid] != event:
                    raise WikiError("An evidence identity conflicts with its historical contents.")
                lifetime_events[eid] = event
    for h in wiki["history"]:
        instant(h["recorded_at"])
        if h["operation_id"] in seen:
            raise WikiError("Duplicate history operation ID.")
        seen.add(h["operation_id"])
        before, after = snapshot_state(wiki, h["before"]), snapshot_state(wiki, h["after"])
        for side in ["before", "after"]:
            if h[side].get("encoding") == "sha256-refs":
                if wiki.get("history_format") != "content-addressed-v1":
                    raise WikiError("Compact history needs its format marker.")
                for key in ["sources", "cards", "relations"]:
                    used_objects.update(h[side][key])
        if h["before_sha256"] != digest(before) or h["after_sha256"] != digest(after):
            raise WikiError("History snapshot checksum mismatch.")
        if h["base_revision"] != before["revision"] or h["result_revision"] != after["revision"] or h["result_revision"] != h["base_revision"] + 1:
            raise WikiError("History revision transition is invalid.")
        if previous is None and h["base_revision"] != 0:
            raise WikiError("History must start at revision zero.")
        if previous is not None and before != previous:
            raise WikiError("History snapshots are not a continuous chain.")
        check_state(before)
        check_state(after)
        remember(before)
        remember(after)
        previous = after
    if used_objects != set(objects):
        raise WikiError("History object store contains unreferenced data.")
    if previous is not None and previous != state_of(wiki):
        raise WikiError("Current state differs from the last protected revision.")
    if previous is None and wiki["revision"] != 0:
        raise WikiError("A nonzero revision needs history.")
    remember(wiki)
    return wiki


def all_events(cards):
    return {e["id"]: e for c in cards for e in c["timeline"]}


def redaction_scope(wiki, source_ids):
    states = [state_of(wiki)] + list(history_states(wiki))
    known = {s["id"] for state in states for s in state["sources"]}
    selected, cards = set(source_ids), set()
    if not selected or not selected <= known:
        raise WikiError("Redaction needs existing source IDs; review the scope first.")
    # Conservative closure: a shared source or historical version may have
    # copied private text into another event in the same work card.
    changed = True
    while changed:
        old = (len(selected), len(cards))
        for state in states:
            for card in state["cards"]:
                used = {e["source_id"] for e in card["timeline"]}
                if card["id"] in cards or used & selected:
                    cards.add(card["id"])
                    selected.update(used)
        changed = old != (len(selected), len(cards))
    return selected, cards


def redact_history(wiki, operation):
    selected, affected_cards = redaction_scope(wiki, operation["source_ids"])
    def scrub(state):
        state = copy.deepcopy(state)
        for source in state["sources"]:
            if source["id"] in selected:
                for key in list(source):
                    if key not in {"id", "sent_at", "captured_at", "content_sha256"}:
                        del source[key]
                source.update(excerpt="[Redacted]", redacted=True)
        for card in state["cards"]:
            if card["id"] in affected_cards:
                card.update(title="[Redacted work]", summary="[Redacted]", status="unknown",
                            unknowns=["Evidence removed by privacy redaction; conclusions require new evidence."],
                            outcome={"state": "unknown", "evidence_ids": []})
                for event in card["timeline"]:
                    event.update(summary="[Redacted]", quote="[Redacted]", kind="unknown", basis="inferred", verification=False)
        # Free-text relation rationales and operation reasons can repeat mail.
        for relation in state["relations"]:
            relation.update(rationale="[Redacted]", certainty="uncertain", evidence_ids=[])
        return state
    result = {**scrub(state_of(wiki)), "history": []}
    for entry in wiki["history"]:
        sanitized = {k: copy.deepcopy(v) for k, v in entry.items() if k not in {"before", "after"}}
        for side in ["before", "after"]:
            sanitized[side] = scrub(snapshot_state(wiki, entry[side]))
            sanitized[side + "_sha256"] = digest(sanitized[side])
        sanitized["reason"] = "[Redacted prior operation reason]"
        result["history"].append(sanitized)
    sources = {s["id"]: s for state in [wiki] + list(history_states(wiki)) for s in state["sources"]}
    audit = {"actor": operation["actor"], "source_ids": sorted(selected), "card_ids": sorted(affected_cards),
             "original_content_sha256": {sid: sources[sid]["content_sha256"] for sid in sorted(selected)},
             "previous_wiki_sha256": digest(wiki), "reason_sha256": digest(operation["reason"])}
    return result, audit, affected_cards


def prepare(wiki, operation):
    validate(wiki)
    schema_validate(operation, "operation")
    instant(operation["recorded_at"])
    request_hash = digest(operation)
    for h in wiki["history"]:
        if h["operation_id"] == operation["operation_id"]:
            if h["request_sha256"] != request_hash:
                raise WikiError("Operation ID already used for different content.")
            return copy.deepcopy(wiki), False
    if operation["expected_revision"] != wiki["revision"]:
        raise WikiError("Stale revision; re-read and reconcile the current wiki.")
    action = operation["action"]
    redaction = None
    if action == "redact":
        wiki, redaction, redacted_cards = redact_history(wiki, operation)
    before = state_of(wiki)
    after = copy.deepcopy(before)
    old_cards = index_unique(before["cards"], "card")
    historical_card_ids = {c["id"] for state in history_states(wiki) for c in state["cards"]}
    if action == "revise":
        after = copy.deepcopy(operation["state"])
        if after["revision"] != wiki["revision"]:
            raise WikiError("Proposed state must use the expected current revision.")
        new_sources = index_unique(after["sources"], "source")
        if any(new_sources.get(s["id"]) != s for s in before["sources"]):
            raise WikiError("Existing source evidence is immutable; append corrections.")
        new_cards = index_unique(after["cards"], "card")
        for cid, old in old_cards.items():
            new = new_cards.get(cid)
            if new is None or new["lifecycle"] != old["lifecycle"] or new["replaced_by"] != old["replaced_by"]:
                raise WikiError("Removing or retiring cards requires merge/split/undo.")
            if new["revision"] != old["revision"]:
                raise WikiError("Card revision conflict; preserve the current revision in proposals.")
            new_events = all_events([new])
            if any(new_events.get(e["id"]) != e for e in old["timeline"]):
                raise WikiError("Original card evidence cannot be removed or rewritten.")
            if new != old:
                new["revision"] += 1
        if any(c["revision"] != 0 for c in after["cards"] if c["id"] not in old_cards):
            raise WikiError("New cards must start at revision zero.")
        if any(c["id"] in historical_card_ids for c in after["cards"] if c["id"] not in old_cards):
            raise WikiError("Historical card IDs remain reserved after undo; choose a fresh work ID.")
    elif action in {"merge", "split"}:
        selected = operation["card_ids"] if action == "merge" else [operation["card_id"]]
        if any(cid not in old_cards or old_cards[cid]["lifecycle"] != "active" for cid in selected):
            raise WikiError("Merge/split requires existing active cards.")
        replacements = [copy.deepcopy(operation["replacement"])] if action == "merge" else copy.deepcopy(operation["replacements"])
        new_ids = [c["id"] for c in replacements]
        if len(set(new_ids)) != len(new_ids) or any(cid in old_cards or cid in historical_card_ids for cid in new_ids):
            raise WikiError("Replacement cards need fresh unique IDs.")
        if any(c["revision"] != 0 or c["lifecycle"] != "active" or c["replaced_by"] for c in replacements):
            raise WikiError("Replacement cards must be new active revision-zero cards.")
        preserved = all_events([old_cards[cid] for cid in selected])
        if all_events(replacements) != preserved:
            raise WikiError("Merge/split must preserve all selected evidence exactly.")
        if action == "split" and sum(len(c["timeline"]) for c in replacements) != len(preserved):
            raise WikiError("Split must partition each evidence event exactly once.")
        old_unknowns = {u for cid in selected for u in old_cards[cid]["unknowns"]}
        if not old_unknowns <= {u for c in replacements for u in c["unknowns"]}:
            raise WikiError("Preserve unresolved questions in replacement cards.")
        for c in after["cards"]:
            if c["id"] in selected:
                c["lifecycle"] = "retired"
                c["replaced_by"] = new_ids
                c["revision"] += 1
        after["cards"].extend(replacements)
    elif action == "redact":
        for card in after["cards"]:
            if card["id"] in redacted_cards:
                card["revision"] += 1
    else:
        if not wiki["history"] or wiki["history"][-1]["operation_id"] != operation["target_operation_id"]:
            raise WikiError("Undo supports only the latest operation; review later changes first.")
        if wiki["history"][-1]["action"] == "redact":
            raise WikiError("Privacy redaction is irreversible; undo cannot restore removed content.")
        after = copy.deepcopy(snapshot_state(wiki, wiki["history"][-1]["before"]))
        for c in after["cards"]:
            current = old_cards.get(c["id"])
            prior_revs = [x["revision"] for state in history_states(wiki) for x in state["cards"] if x["id"] == c["id"]]
            c["revision"] = max(prior_revs + [c["revision"], current["revision"] if current else 0]) + 1
    after["revision"] = wiki["revision"] + 1
    result = {**after, "history": copy.deepcopy(wiki["history"])}
    if "history_objects" in wiki:
        result.update(history_format=wiki["history_format"], history_objects=wiki["history_objects"])
    result["history"].append({"operation_id": operation["operation_id"], "request_sha256": request_hash,
                              "action": action, "reason": operation["reason"], "recorded_at": operation["recorded_at"],
                              "base_revision": before["revision"], "result_revision": after["revision"],
                              "before": before, "after": after,
                              "before_sha256": digest(before), "after_sha256": digest(after)})
    if redaction is not None:
        result["history"][-1].update(redaction=redaction, reason="Privacy redaction requested; free-text reason retained only as SHA-256.")
    result = pack_history(result)
    validate(result)
    return result, True


def write_new_json(path, value):
    # Exclusive creation prevents accidental overwrites of drafts/exports.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def apply_file(path, operation):
    path = Path(path)
    if path.is_symlink():
        raise WikiError("Refusing a symlink snapshot; choose its reviewed destination explicitly.")
    lock = path.with_name(path.name + ".lock")
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise WikiError("An update lock already exists; check its owner and current revision.") from exc
    temporary = None
    try:
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
        result, changed = prepare(read_json(path), operation)
        if changed:
            temp_fd, temporary = tempfile.mkstemp(prefix=".life-wiki-", suffix=".json", dir=path.parent)
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, path)
            temporary = None
        return result, changed
    finally:
        if temporary is not None:
            os.unlink(temporary)
        lock.unlink()


def markdown_text(value):
    escaped = html.escape(value, quote=True)
    return re.sub(r"([\\`*_{}\[\]()#+.!|~-])", r"\\\1", escaped)


def card_markdown(card, wiki):
    m = markdown_text
    lines = [f"# {m(card['title'])}", "", f"Work ID: {card['id']}", f"Revision: {card['revision']}",
             f"Lifecycle: {card['lifecycle']}", f"Status: {card['status']}", f"Outcome: {card['outcome']['state']}",
             "", m(card["summary"]), "", "## Chronology and evidence", ""]
    for e in card["timeline"]:
        lines += [f"### {e['source_timestamp']} · {e['kind']}", "", m(e["summary"]), "",
                  *["> " + m(line) for line in e["quote"].splitlines()], "",
                  f"Evidence: {e['id']} · Source: {e['source_id']} · Basis: {e['basis']} · Verified: {str(e['verification']).lower()}", ""]
    lines += ["## Related work", ""]
    related = [r for r in wiki["relations"] if card["id"] in [r["from"], r["to"]]]
    for r in related:
        other = r["to"] if r["from"] == card["id"] else r["from"]
        lines += [f"- [{other}]({other}.md) · {r['type']} · {r['certainty']}: {m(r['rationale'])} (evidence: {', '.join(r['evidence_ids']) or 'none'})"]
    if not related:
        lines += ["No recorded relations."]
    lines += ["", "## Unknowns", "", *["- " + m(u) for u in card["unknowns"]]]
    if not card["unknowns"]:
        lines += ["No additional unknowns recorded; this is not a completion claim."]
    lines += ["", "## Provenance", ""]
    used = {e["source_id"] for e in card["timeline"]}
    for s in wiki["sources"]:
        if s["id"] in used:
            lines += [f"- {s['id']}: sent {s['sent_at']}; captured {s['captured_at']}; content SHA-256 `{s['content_sha256']}`"]
            if "uri" in s:
                lines += ["  Source locator (inert text): " + m(s["uri"])]
    if card["replaced_by"]:
        lines += ["", "Replaced by: " + ", ".join(f"[{cid}]({cid}.md)" for cid in card["replaced_by"])]
    relevant = [h for h in wiki["history"] if any(c["id"] == card["id"] for side in ["before", "after"] for c in snapshot_state(wiki, h[side])["cards"])]
    lines += ["", "## Revision history", "", *[f"- {h['operation_id']} · {h['action']} · {h['recorded_at']} · wiki {h['base_revision']} → {h['result_revision']}: {m(h['reason'])}" for h in relevant]]
    if not relevant:
        lines += ["Initial snapshot (revision zero)."]
    lines += ["", "The companion wiki.json contains the complete relation, source, and reversible history records.", ""]
    return "\n".join(lines)


def rename_new_directory(source, destination):
    """Atomic publish without replacing even a racing, empty destination."""
    if sys.platform == "win32":
        os.rename(source, destination)  # Windows rename never replaces a target.
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        status = rename(os.fsencode(source), os.fsencode(destination), 4)  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        status = rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1)  # AT_FDCWD, RENAME_NOREPLACE
    else:
        raise WikiError("Atomic export needs exclusive directory rename support on this platform.")
    if status:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def render(wiki, destination):
    validate(wiki)
    destination = Path(destination)
    # A fresh directory prevents silent loss of user-edited Markdown.
    if os.path.lexists(destination):
        raise FileExistsError("Export destination already exists.")
    staging = Path(tempfile.mkdtemp(prefix=".life-wiki-export-", dir=destination.parent))
    try:
        shutil.copytree(SKILL_ROOT / "assets" / "viewer", staging, dirs_exist_ok=True)
        staging.chmod(0o700)
        write_new_json(staging / "wiki.json", wiki)
        (staging / "cards").mkdir(mode=0o700)
        for card in wiki["cards"]:
            path = staging / "cards" / (card["id"] + ".md")
            path.write_text(card_markdown(card, wiki), encoding="utf-8")
            path.chmod(0o600)
        # The final rename is within one parent/filesystem. Recheck after all
        # writes so a destination created during generation is never replaced.
        if os.path.lexists(destination):
            raise FileExistsError("Export destination already exists.")
        rename_new_directory(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["validate", "normalize", "render", "apply", "redact-preview"]:
        p = sub.add_parser(name)
        p.add_argument("input")
        if name in {"normalize", "render"}:
            p.add_argument("--out", required=True)
        if name == "normalize":
            p.add_argument("--existing", help="Retain immutable source metadata from an existing wiki")
        if name == "apply":
            p.add_argument("operation")
        if name == "redact-preview":
            p.add_argument("--source-id", action="append", required=True)
    args = parser.parse_args()
    try:
        if args.command == "apply":
            result, changed = apply_file(args.input, read_json(args.operation))
            print(f"{'Applied' if changed else 'No-op replay'}; revision {result['revision']}.")
        else:
            value = read_json(args.input)
            if args.command == "validate":
                validate(value)
                print(f"Valid; revision {value['revision']}; {len(value['cards'])} cards.")
            elif args.command == "redact-preview":
                validate(value)
                sources, cards = redaction_scope(value, args.source_id)
                print(json.dumps({"source_ids": sorted(sources), "card_ids": sorted(cards),
                                  "all_relation_rationales_and_prior_reasons": "removed"}, indent=2))
            elif args.command == "normalize":
                sources = normalize_inbox(value, read_json(args.existing) if args.existing else None)
                write_new_json(args.out, sources)
                print(f"Normalized {len(sources)} unique sources; minimize excerpts before durable use.")
            else:
                render(value, args.out)
                print("Export created. Open index.html and select the exported wiki.json.")
    except (WikiError, OSError) as exc:
        if isinstance(exc, WikiError):
            print(str(exc), file=sys.stderr)
        else:
            print("File operation failed; check existence, permissions, and destination locally.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
