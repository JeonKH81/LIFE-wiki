# Portable data model (v1)

`wiki.json` is the authoritative snapshot; generated `cards/<work-id>.md` are readable portable projections. Edit the JSON through a protected operation, then regenerate cards. Manual edits to Markdown are not imported automatically. Read them before updating and incorporate intended changes in the proposal; do not render over an existing export. The export helper requires a new output directory.

JSON Schemas are in `../schemas/`: `wiki.schema.json`, `card.schema.json`, `provenance.schema.json`, `relations.schema.json`, and `operation.schema.json`. All objects reject unknown properties. The validator checks schema plus cross-record invariants.

The state has `schema_version: 1`, global `revision`, `sources`, `cards`, and `relations`. A wiki also has append-only `history`. Each card has its own `revision`, `lifecycle` (`active`/`retired`), `replaced_by`, `title`, `summary`, `status`, `outcome`, `timeline`, and `unknowns`. IDs are lowercase slug-like strings, never filenames or paths. Retired cards retain their evidence and replacement IDs after merges/splits.

Sources store normalized mailbox/message identity, `sent_at`, `captured_at`, digest, and a minimized exact `excerpt`; optional `uri` is inert text. Evidence events reference a source ID, repeat its source timestamp exactly, and contain an exact `quote`, an interpretive `summary`, `kind`, `basis`, and `verification`. A quote must occur literally in its source excerpt. Events are ordered by actual timestamp, then ID; timezone offsets must not be sorted as strings. An identical event may support multiple active or retired cards; this does not make it independent evidence. It cannot appear twice within a card or change content under the same ID, including after undo. Historical work IDs remain reserved.

Relations have stable IDs, `from`, `to`, `type`, `certainty`, `rationale`, `evidence_ids`, and `recorded_at`. Both endpoints and cited events must exist. Evidence must belong to one of the endpoints. Confirmed relations need evidence, and all relations need a rationale. Uncertain relations stay visible.

History records the operation identity/digest, action, reason, timestamp, revision transition, and complete before/after states (without recursive history). State hashes and a continuous revision chain detect accidental corruption. This is reversible local history, not signed audit logging. Anyone with file access can rewrite it, and external editors bypass the helper's lock. Use appropriate private storage and backups.

Summaries and unknowns are prose, so automated validation cannot prove that every interpretation is faithful or that text is free of personal data. Review substantive statements against timeline evidence and source context. No algorithm clusters arbitrary email automatically in this MVP.
