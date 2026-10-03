# Verification record for the 2026-10-03 review fixes

This document records the local checks for the 2026-10-03 review fixes. The public comparison baseline was `1114830`. Results below distinguish reported execution from configured checks and unverified behavior. All fixtures and benchmarks are fictional; no real user material was permanently deleted.

## Baseline review

The supplied 2026-10-03 review reports 35 Python tests passing with Python 3.13/jsonschema 4.26, a passing Node viewer check, successful validation, nine inbox records normalized to eight sources, and rendered Markdown matching fixtures byte for byte. These are that review's results, not a new baseline execution by this document's author.

## Current local checks

All 52 local Python checks passed under Python 3.14.7 and 3.12.2. Direct viewer checks passed with Node.js v24.13.0, all five schema meta-checks passed, and the four-card fixture validated. The checks cover legacy/compact history, corruption, Unicode/timestamps, conservative redaction, tombstone protection, failed writes, and exclusive export rename. Independent review found and rechecked fixes for viewer line-ending comparison and UTC date overflow; no remaining critical issue was found within this review scope. The final local checks passed after those fixes.

Python 3.10 is not installed in the verification environment. Python-source syntax checks for 3.10 passed, which does not establish runtime compatibility. The workflow configures Python 3.10/3.12/3.14 and Node.js 22 and calls Node directly, and it had not run at the time of these local checks. Consult the repository Actions run for the exact published commit to verify hosted results. No software was installed for these checks. The helper itself does not require Node; the complete regression suite does.

A local benchmark of 60 successive fictional summary edits, using pretty UTF-8 JSON, produced:

| Measurement | Baseline | Review fixes |
|---|---:|---:|
| Final JSON size | 1,618,407 bytes | 354,222 bytes |
| Cumulative elapsed time | 6.6802 seconds | 5.4218 seconds |

That is about 78% less storage and 19% less elapsed time in this workload. These are not guarantees for other data, hardware, or workloads. Full history is still checked each time; cumulative work across edits remains roughly quadratic.

## Reproduce repository checks

Install `requirements.txt` in the chosen Python environment; provide Node.js for the suite. Then run:

```sh
python3 -m unittest discover -s tests -v
node tests/viewer.test.js
python3 skills/life-wiki/scripts/wiki.py validate examples/expected/wiki.json
python3 skills/life-wiki/scripts/wiki.py normalize examples/inbox.json --out /tmp/life-wiki-check-sources.json
python3 skills/life-wiki/scripts/wiki.py render examples/expected/wiki.json --out /tmp/life-wiki-check-export
```

Use fresh output names; existing output is not overwritten. Compare exported cards with `examples/expected/cards`.

## Limits of the evidence

- macOS exclusive directory rename was checked locally. Windows/Linux execution is not established by that result.
- Actual browser `file://` CSP behavior is unverified. The available browser tool rejected the scheme; Firefox was not separately exercised. CSP was not weakened. Node tests exercise viewer code and a DOM double, not a real browser's local-file policy.
- Claude Code installation/live use, ChatGPT plugin-market installation, and live mailbox behavior are unverified.
- Redaction covers the managed wiki's linked text/history. Remaining metadata, unlinked text copies, source/operation files, old exports, backups, synchronization versions, and Git history need separate review.
- Local hashes, revision chains, and actor aliases are not signed or authenticated audit records.
