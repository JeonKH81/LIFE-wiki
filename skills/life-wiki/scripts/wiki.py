#!/usr/bin/env python3
"""Offline evidence validation, protected transactions, and portable export."""
import argparse
import copy
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
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


def schema_validate(value, name):
    schemas = [json.loads(p.read_text()) for p in (SKILL_ROOT / "schemas").glob("*.json")]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    schema = next(s for s in schemas if s["$id"].endswith("/" + name + ".schema.json"))
    errors = list(Draft202012Validator(schema, registry=registry,
                                     format_checker=FormatChecker()).iter_errors(value))
    if errors:
        # jsonschema messages can contain raw input: do not echo them.
        raise WikiError(f"{name} schema check failed ({len(errors)} issue(s)); inspect input against schemas.")


def instant(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError
        return dt.astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise WikiError("Source timestamps must include a valid timezone.") from exc


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
        snapshots = [existing] + [s for h in existing["history"] for s in [h["before"], h["after"]]]
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
        body = message["body"].replace("\r\n", "\n").replace("\r", "\n")
        sid = source_id(scope, key)
        source = {"id": sid, "account_scope": scope, "message_key": key,
                  "sent_at": message["sent_at"], "captured_at": inbox["captured_at"],
                  "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(), "excerpt": body}
        prior = retained.get(sid)
        if prior is not None:
            if any(prior[k] != source[k] for k in ["account_scope", "message_key", "sent_at", "content_sha256"]):
                raise WikiError("Conflicting existing message identity; no source was overwritten.")
            source = copy.deepcopy(prior)
        if sid in sources and sources[sid] != source:
            raise WikiError("Conflicting repeated message identity; no source was overwritten.")
        sources[sid] = source
    result = sorted(sources.values(), key=lambda s: (instant(s["sent_at"]), s["id"]))
    schema_validate(result, "provenance")
    return result


def state_of(wiki):
    return copy.deepcopy({k: v for k, v in wiki.items() if k != "history"})


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
            if e["quote"] not in source["excerpt"]:
                raise WikiError("Evidence quote must match the retained source excerpt exactly.")
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
    previous = None
    seen = set()
    lifetime_sources, lifetime_events, lifetime_cards = {}, {}, {}
    def remember(state):
        for source in state["sources"]:
            sid = source["id"]
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
        if h["operation_id"] in seen:
            raise WikiError("Duplicate history operation ID.")
        seen.add(h["operation_id"])
        if h["before_sha256"] != digest(h["before"]) or h["after_sha256"] != digest(h["after"]):
            raise WikiError("History snapshot checksum mismatch.")
        if h["base_revision"] != h["before"]["revision"] or h["result_revision"] != h["after"]["revision"] or h["result_revision"] != h["base_revision"] + 1:
            raise WikiError("History revision transition is invalid.")
        if previous is None and h["base_revision"] != 0:
            raise WikiError("History must start at revision zero.")
        if previous is not None and h["before"] != previous:
            raise WikiError("History snapshots are not a continuous chain.")
        validate_state(h["before"])
        validate_state(h["after"])
        remember(h["before"])
        remember(h["after"])
        previous = h["after"]
    if previous is not None and previous != state_of(wiki):
        raise WikiError("Current state differs from the last protected revision.")
    if previous is None and wiki["revision"] != 0:
        raise WikiError("A nonzero revision needs history.")
    remember(wiki)
    return wiki


def all_events(cards):
    return {e["id"]: e for c in cards for e in c["timeline"]}


def prepare(wiki, operation):
    validate(wiki)
    schema_validate(operation, "operation")
    request_hash = digest(operation)
    for h in wiki["history"]:
        if h["operation_id"] == operation["operation_id"]:
            if h["request_sha256"] != request_hash:
                raise WikiError("Operation ID already used for different content.")
            return copy.deepcopy(wiki), False
    if operation["expected_revision"] != wiki["revision"]:
        raise WikiError("Stale revision; re-read and reconcile the current wiki.")
    before = state_of(wiki)
    after = copy.deepcopy(before)
    old_cards = index_unique(before["cards"], "card")
    historical_card_ids = {c["id"] for h in wiki["history"] for state in [h["before"], h["after"]] for c in state["cards"]}
    action = operation["action"]
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
    else:
        if not wiki["history"] or wiki["history"][-1]["operation_id"] != operation["target_operation_id"]:
            raise WikiError("Undo supports only the latest operation; review later changes first.")
        after = copy.deepcopy(wiki["history"][-1]["before"])
        for c in after["cards"]:
            current = old_cards.get(c["id"])
            prior_revs = [x["revision"] for h in wiki["history"] for state in [h["before"], h["after"]] for x in state["cards"] if x["id"] == c["id"]]
            c["revision"] = max(prior_revs + [c["revision"], current["revision"] if current else 0]) + 1
    after["revision"] = wiki["revision"] + 1
    result = {**after, "history": copy.deepcopy(wiki["history"])}
    result["history"].append({"operation_id": operation["operation_id"], "request_sha256": request_hash,
                              "action": action, "reason": operation["reason"], "recorded_at": operation["recorded_at"],
                              "base_revision": before["revision"], "result_revision": after["revision"],
                              "before": before, "after": after,
                              "before_sha256": digest(before), "after_sha256": digest(after)})
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
    relevant = [h for h in wiki["history"] if any(c["id"] == card["id"] for c in h["before"]["cards"] + h["after"]["cards"])]
    lines += ["", "## Revision history", "", *[f"- {h['operation_id']} · {h['action']} · {h['recorded_at']} · wiki {h['base_revision']} → {h['result_revision']}: {m(h['reason'])}" for h in relevant]]
    if not relevant:
        lines += ["Initial snapshot (revision zero)."]
    lines += ["", "The companion wiki.json contains the complete relation, source, and reversible history records.", ""]
    return "\n".join(lines)


def render(wiki, destination):
    validate(wiki)
    destination = Path(destination)
    # A fresh directory prevents silent loss of user-edited Markdown.
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    shutil.copytree(SKILL_ROOT / "assets" / "viewer", destination, dirs_exist_ok=True)
    destination.chmod(0o700)
    write_new_json(destination / "wiki.json", wiki)
    (destination / "cards").mkdir(mode=0o700)
    for card in wiki["cards"]:
        path = destination / "cards" / (card["id"] + ".md")
        path.write_text(card_markdown(card, wiki), encoding="utf-8")
        path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["validate", "normalize", "render", "apply"]:
        p = sub.add_parser(name)
        p.add_argument("input")
        if name in {"normalize", "render"}:
            p.add_argument("--out", required=True)
        if name == "normalize":
            p.add_argument("--existing", help="Retain immutable source metadata from an existing wiki")
        if name == "apply":
            p.add_argument("operation")
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
