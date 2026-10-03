# Protected operations and local export

The same protected operations apply to work and everyday life cards. Existing technical identifiers and schemas remain unchanged. A user-directed change to a reservation or learning record still requires source evidence; the helper does not book, cancel, change calendars, collect live email, or decide that an activity is complete.

Python 3.10+ and `jsonschema >=4.18,<5` are required. Timestamp checking is explicit; no optional format package is needed. The installed skill is self-contained. From the project where it was copied:

```sh
python3 -m pip install -r .agents/skills/life-wiki/requirements.txt
python3 .agents/skills/life-wiki/scripts/wiki.py validate /private/path/wiki.json
python3 .agents/skills/life-wiki/scripts/wiki.py normalize /private/path/inbox.json --existing /private/path/wiki.json --out /private/path/new-sources.json
python3 .agents/skills/life-wiki/scripts/wiki.py apply /private/path/wiki.json /private/path/operation.json
python3 .agents/skills/life-wiki/scripts/wiki.py render /private/path/wiki.json --out /private/path/new-export
```

Use the actual installed folder if it differs. Repository samples and top-level requirements are not installed-skill dependencies. For a repository demo:

```sh
python3 -m pip install -r requirements.txt
python3 skills/life-wiki/scripts/wiki.py validate examples/expected/wiki.json
python3 skills/life-wiki/scripts/wiki.py normalize examples/inbox.json --out /tmp/life-wiki-sources.json
python3 skills/life-wiki/scripts/wiki.py render examples/expected/wiki.json --out /tmp/life-wiki-demo
```

## Import and ordinary changes

`normalize` deduplicates mailbox/message identity and rejects conflicting content/time. New bodies use NFC/LF normalization. With `--existing`, repeated sources retain original capture time, minimized excerpt, and digest; conflicts with current or historical sources are rejected. Legacy raw-format digests remain unchanged. Existing redacted identities keep tombstones rather than producing full-body drafts. The helper never decides grouping. Other new excerpts contain full bodies: minimize them before saving. Create a revision-zero wiki with `history: []` from interpreted cards, then validate. Store live data outside this repository in a private directory.

Write operation JSON matching `../schemas/operation.schema.json`, review it, then use `apply`. All operations need a fresh stable `operation_id`, `expected_revision`, timezone-aware `recorded_at`, and `reason`. The explicit parser accepts lowercase `t`/`z` and arbitrary fractional lengths, compares at microsecond precision, and rejects leap seconds. Identical operation replay is a no-op even at its old stale revision. Reusing an ID with different content or applying a different stale operation is rejected without writing.

The helper locks cooperating writers and atomically replaces the snapshot. An existing lock stops an update. Do not delete a lock without checking its owner/process and current file. External editors bypass it; re-read and reconcile their changes. This is not a concurrent multi-user database.

The first successful non-replay change converts legacy snapshots to `history_format: "content-addressed-v1"`, with source/card/relation objects shared by SHA-256 inside the wiki. Ordinary conversion preserves decoded states and existing hashes. Each call checks the complete history and caches repeated object/state checks within that call only. Storage shrinks, but cumulative validation across many edits can remain roughly quadratic. See [data-model.md](data-model.md).

- `revise`: provide complete `state` without history, using expected global revision and each existing card's current revision. Unchanged cards retain revision; changed cards advance by one. Ordinary revision cannot rewrite or remove original sources/events. Append corrections. Removing cards or changing lifecycle/replacements requires merge/split/undo. New cards start at revision zero. Relations may be corrected, with old states retained.
- `merge`: provide at least two active `card_ids` and a fresh-ID `replacement` preserving their exact union of events and unresolved questions. Inputs become retired and point to the new card. Provide supported summary/status/outcome; the helper does not select the phase. Original relations stay on original cards for review.
- `split`: provide one active `card_id` and two or more fresh-ID `replacements`. Partition every original event exactly once and preserve unresolved questions. The original becomes retired and points to the new cards. Add shared context later with revise. Original relations remain for review.
- `undo`: provide `target_operation_id` for the latest operation only. Restoration is appended and card revisions advance. Historical IDs remain reserved. `redact` cannot be undone. Later ordinary changes can be undone without restoring deleted text. Arbitrary older undo is unsupported.

## Preview and authorize privacy redaction

`redact` deliberately removes evidence text from current and historical states and cannot be reversed. Identify source IDs, then inspect the expanded scope without changing the wiki:

```sh
python3 skills/life-wiki/scripts/wiki.py redact-preview /private/path/wiki.json --source-id src-example
```

Replace `src-example` with an actual source ID. Repeat `--source-id` for more starting sources. Output lists expanded source/card IDs and the global removal of relation rationales and previous reasons. It prints no excerpts, but IDs may themselves be sensitive.

Scope follows every historical/current affected card version and all sources shared with it until expansion stops. Mixed messages and earlier merges/splits can reach other cards and remove much more than one message. Explain the complete preview and obtain explicit deletion authorization before applying. Existing instructions clearly covering that full scope do not need redundant confirmation. Recheck revision if anything changes after preview.

Use a private operation file, for example:

```json
{
  "operation_id": "op-redact-1",
  "expected_revision": 3,
  "recorded_at": "2026-10-03T12:00:00Z",
  "reason": "Remove mistakenly retained sensitive evidence.",
  "action": "redact",
  "source_ids": ["src-example"],
  "actor": "privacy-operator"
}
```

Use actual reviewed IDs, current revision/time, and a fresh operation ID. `actor` is a non-identifying lowercase alias, not a person's name, email, or patient identifier. It is supplied metadata, not authenticated identity. Minimize the reason: its plaintext remains in the operation file even though the wiki retains only its canonical JSON SHA-256. Once authorized, apply with the same `apply` command above.

## What redaction changes and retains

Every expanded source becomes `[Redacted]` with `redacted: true`; `account_scope`, `message_key`, and `uri` are removed. Source ID, timestamps, and the stored content digest remain. Affected cards get neutral titles/summaries/unknowns, unknown status/outcome, and neutral events with `kind: unknown`, `basis: inferred`, and `verification: false`. Every relation rationale is neutralized, certainty becomes uncertain, and evidence lists are cleared. Every old operation reason is neutralized, including unrelated work's reasons.

Every past state is sanitized. Its state hashes are recomputed, and the object store is rebuilt without old content. The new redaction's own `before` is already sanitized. Audit records contain actor/time, expanded source/card IDs, stored original content hashes, previous wiki hash, and reason hash. Operation IDs, old request hashes, timestamps, card/event/relation IDs, lineage, and non-text metadata remain. A tombstone without a matching permanent audit hash is rejected.

Undo of redaction is rejected. Ordinary changes cannot overwrite tombstones; later undo and repeated import with `--existing` retain removal. Protection belongs to this wiki: omitting `--existing` cannot know its deletion history.

Free text copied into unrelated cards without evidence connections is not traced. Source files, supplied operation files, old exports, backups, sync versions, and Git history are not removed. IDs, dates, hashes, and aliases may remain identifying. Review remaining materials before sharing; this is not a guarantee of erasure of all personal data everywhere.

## Export and recovery

`render` validates the wiki, creates a temporary sibling directory, writes JSON/cards/viewer there, and publishes it by an exclusive atomic rename. The destination parent must exist. Existing destinations, including empty directories or symlinks, stay unchanged; a destination created during generation is not replaced. A normal write/rename failure removes staging output and allows retry at the same destination. Abrupt termination can leave a private staging directory requiring local review.

The code uses macOS `renamex_np`, Linux `renameat2`, or Windows rename semantics. Platforms lacking required exclusive rename fail explicitly. Implementing these paths does not establish that each operating system has been exercised; see the repository [verification summary](../../../docs/VERIFICATION.md).

Open `index.html` locally and select its exported JSON, or the fictional demo. Data do not load automatically or contact a server. The viewer uses text nodes, cannot change records or follow source URLs, and saves no personal data in browser storage. The file limit remains 8MB. Actual browser CSP behavior under `file://` remains unverified; Node tests do not establish Chrome/Firefox local-file compatibility. Keep exports private and review the complete JSON/history before publication.
