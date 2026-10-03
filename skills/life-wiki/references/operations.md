# Protected operations and local export

Python 3.10+ and `jsonschema >=4.18,<5` are required for helpers. The installed skill is self-contained. From the project where it was copied, install its dependency into the chosen Python environment and invoke:

```sh
python3 -m pip install -r .agents/skills/life-wiki/requirements.txt
python3 .agents/skills/life-wiki/scripts/wiki.py validate /private/path/wiki.json
python3 .agents/skills/life-wiki/scripts/wiki.py normalize /private/path/inbox.json --existing /private/path/wiki.json --out /private/path/new-sources.json
python3 .agents/skills/life-wiki/scripts/wiki.py apply /private/path/wiki.json /private/path/operation.json
python3 .agents/skills/life-wiki/scripts/wiki.py render /private/path/wiki.json --out /private/path/new-export
```

Use the actual installed folder instead if it differs. The sample inbox, expected results, and top-level requirements are repository examples, not installed-skill dependencies. For a repository checkout demo, from its root:

```sh
python3 -m pip install -r requirements.txt
python3 skills/life-wiki/scripts/wiki.py validate examples/expected/wiki.json
python3 skills/life-wiki/scripts/wiki.py normalize examples/inbox.json --out /tmp/life-wiki-sources.json
python3 skills/life-wiki/scripts/wiki.py render examples/expected/wiki.json --out /tmp/life-wiki-demo
```

`normalize` deduplicates immutable mailbox/message identity and rejects conflicting content/time. With `--existing`, repeated sources retain their original capture timestamp and minimized excerpt, and conflicts with current or historical sources are rejected. It never decides work grouping. New draft excerpts contain full bodies: select minimum excerpts before saving. Create a revision-zero wiki with `history: []` from chosen sources and interpreted work cards, then validate. Store live data outside this repository, in a user-approved private directory.

For updates, write an operation JSON matching `../schemas/operation.schema.json`, validate the proposed change by review, then:

```sh
python3 skills/life-wiki/scripts/wiki.py apply /private/path/wiki.json /private/path/operation.json
```

All operations need a unique stable `operation_id`, `expected_revision`, timezone-aware `recorded_at`, and `reason`. Replaying the identical operation returns a no-op even if the old revision is stale. Reusing an ID with different contents is rejected. A different stale operation is rejected without writing. The helper locks cooperating writers and atomically replaces the snapshot; an existing lock stops the update. Do not delete a lock without checking its owner/process and the current file. Private snapshots and history are not public artifacts.

- `revise`: provide a complete `state` (without history), using the expected global revision and the current revision of each existing card. Unchanged cards retain their revision; changed cards advance by one. Existing sources, evidence events, and history cannot be rewritten or removed. Corrections add a new event and explain the conflict. Removing a card or changing its lifecycle/replacements requires merge/split/undo. New cards start at revision zero. Existing relations may be corrected in the proposed state, with the previous state preserved in history.
- `merge`: provide at least two active `card_ids` and a new-ID `replacement` card. Its timeline must preserve exactly the union of the selected events. Input cards become retired and point to the replacement. Provide a supported summary/status/outcome; the helper does not select the phase. Original relations remain attached to their original cards for review, rather than guessing how to reassign them.
- `split`: provide one active `card_id` and two or more new-ID `replacements`. Partition all original events exactly once. The original becomes retired and points to the new cards. Add shared context later with a protected revise. Keep original relations for user review.
- `undo`: provide `target_operation_id` for the latest operation only. It appends a restoration operation; history remains. Restored cards receive new revisions so revisions never go backwards. To reverse an older change, first review later dependent changes; arbitrary historical undo is not supported.

Operations cannot erase history or original evidence. The helper's lock does not constrain other editors; re-read after any outside edits and resolve conflicts before applying. Do not use it as a concurrent multi-user database.

`render` creates a new directory with `wiki.json`, Markdown cards, and an original static viewer. Open `index.html` locally and select that exported `wiki.json`, or choose the built-in fictional demo. It does not load data automatically or contact a server. The viewer displays untrusted text with DOM text nodes. It cannot modify cards, merge/split, follow source URLs, or save private content to browser storage.
