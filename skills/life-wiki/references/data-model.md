# Portable data model (v1)

`wiki.json` is authoritative; generated `cards/<work-id>.md` are readable projections. Edit JSON through a protected operation, then regenerate cards. Manual Markdown edits are not imported automatically. Read them before updating and incorporate intended changes in the proposal. Export requires a new directory and leaves an existing destination unchanged.

Schemas are in `../schemas/`: `wiki.schema.json`, `card.schema.json`, `provenance.schema.json`, `relations.schema.json`, and `operation.schema.json`. Unknown properties are rejected. Validation checks schemas, references, timestamps, evidence, revisions, and the entire history chain.

## Current state and evidence

The state has `schema_version: 1`, global `revision`, `sources`, `cards`, and `relations`. A wiki also has `history`, and may have the paired fields `history_format` and `history_objects`. Current sources/cards/relations remain ordinary arrays in either history format. Existing v1 snapshots and fictional examples remain readable; this does not mean older helpers can read the new history format.

Cards have their own `revision`, `lifecycle` (`active`/`retired`), `replaced_by`, `title`, `summary`, `status`, `outcome`, `timeline`, and `unknowns`. IDs are lowercase slug-like strings, never paths. Retired cards retain evidence and replacement IDs during ordinary updates. Historical work IDs remain reserved after undo.

Ordinary sources store mailbox/message identity, `sent_at`, `captured_at`, `content_sha256`, minimized `excerpt`, and optional inert `uri`. New bodies normalize line endings to LF and Unicode to NFC before their content digest is calculated. Existing sources and raw-format digests are not rewritten on repeated imports.

Events reference a source ID, repeat its timestamp exactly, and contain supporting `quote`, interpretive `summary`, `kind`, `basis`, and `verification`. Quote inclusion is compared after NFC/LF normalization: canonically equivalent spelling is accepted but different wording is not. Events are ordered by timestamp instant, then ID. The explicit date parser accepts lowercase `t`/`z` and arbitrary fractional-second lengths, compares at Python datetime's microsecond precision, and rejects leap seconds. No optional format package is required.

An identical event may support several cards; it is still one piece of evidence. It cannot occur twice within a card or change under the same ID during ordinary updates. Relations have stable IDs, `from`, `to`, `type`, `certainty`, `rationale`, `evidence_ids`, and `recorded_at`. Endpoints and cited evidence must exist; evidence must belong to an endpoint. Confirmed relations need evidence, and `possible_same_work` stays uncertain.

## Two history representations

Legacy history contains complete `before`/`after` states without recursive history. The first successful non-replay operation converts the complete history to `history_format: "content-addressed-v1"`. Ordinary conversion changes storage only: decoded states and their existing `before_sha256`/`after_sha256` values remain unchanged.

Compact history keeps each distinct source, card, or relation once in `history_objects`, keyed by SHA-256. A state manifest has `encoding: "sha256-refs"`, `schema_version`, `revision`, and ordered `sources`/`cards`/`relations` arrays of object hashes. This store lives inside `wiki.json`, not external files. The helper resolves references, checks hashes, rejects missing or unreferenced objects, checks decoded states and revision continuity, and compares the last state with the current state.

Each operation retains identity/request digest, action, reason, timestamp, revision transition, and state hashes. General JSON hashes use UTF-8 canonical JSON with sorted keys, no extra whitespace, and unescaped Unicode. Body content digests instead hash normalized UTF-8 text. State hashes cover decoded states, not just manifests.

Object schema checks and duplicate state checks are cached within a validation call. Full history is still inspected for every operation, and packing walks it again. Reuse reduces duplicated storage and repeated checks within a call; it does not give incremental validation across calls, remove the viewer's 8MB limit, or eliminate roughly quadratic cumulative work across successive edits. Frequently changed cards and manifest lists still grow with history.

## Privacy redaction and its audit record

`redact` is an explicit exception to immutable evidence and preserved historical text. Selected source IDs expand through all past/current affected card versions and shared sources until no connected source/card remains outside the scope. See `redact-preview` in [operations.md](operations.md); this can remove more than the selected message.

Selected sources become tombstones: `id`, `sent_at`, `captured_at`, and previously stored `content_sha256` remain; `excerpt` becomes `[Redacted]`, `redacted` becomes `true`, and `account_scope`, `message_key`, and `uri` are removed. Every affected card's title, summary, unknowns, event quotes/summaries, status, and outcome are replaced with neutral text or unknown values. Event kinds become `unknown`, bases `inferred`, and verification flags `false`. Current affected card revisions advance; historical revisions keep their original order.

All relation rationales are replaced, certainty becomes `uncertain`, and evidence lists are cleared. All prior operation reasons are neutralized. Every historical state is sanitized, state hashes are recomputed, and the object store is rebuilt without old text. The appended redaction's `before` is already sanitized; it cannot retain a hidden original copy.

Its audit stores the non-identifying `actor`, expanded `source_ids`/`card_ids`, `original_content_sha256` values, the previous wiki's `previous_wiki_sha256`, and `reason_sha256`. Time is the entry's `recorded_at`. The reason hash covers the canonical JSON reason string; the original reason is not retained in the wiki. Existing operation IDs and request hashes remain. Individual old state hashes are recomputed during redaction; the previous wiki digest records the pre-redaction wiki as a JSON value without retaining its content.

Tombstones require a matching permanent audit hash. They remain protected through ordinary revisions, later undo, and repeated imports using the same existing wiki. Redaction itself cannot be undone. This is local unsigned audit information: actor aliases are supplied, not independently authenticated, and a person with file access can rewrite the file.

IDs, timestamps, hashes, and aliases may remain identifying. Sensitive text copied into unrelated cards without an evidence connection cannot be traced automatically. Source exports, operation files, old renders, backups, synchronization versions, and Git history are not erased. Review remaining prose and metadata before disclosure. Automated validation cannot prove faithful interpretation or complete removal of personal information.
