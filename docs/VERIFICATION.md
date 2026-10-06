# Verification record

## Publication validation — 2026-10-06

The user explicitly requested GitHub publication of the reviewed changes. The remote main head still matched the inspected public baseline before publication. All 60 Python tests, the Node viewer and graph checks, and `git diff --check` passed again. The publication includes only source, documentation, installer, and test files; environments, generated verification output, and private material are excluded. Actual browser rendering remains unverified as described below. The same-day local release contains the direct installer and automatically loaded viewer snapshot, not the superseded trial-first onboarding.

## One-file opening update — 2026-10-05 (latest)

The user found project switching, selecting a skill, and choosing JSON too difficult. The current README now keeps installation and real-material work in the same Codex conversation: the agent reads the installed SKILL.md directly and gives one file link to the rendered index.html. New `initial-data.js` export snapshots let the viewer load records automatically without fetch, a server, or file selection. The optional picker remains for a different record file. This is a saved snapshot, not live synchronization: after updates the agent renders a fresh output and supplies that new index.html.

Render serializes the validated wiki with ASCII JSON escapes plus escaped `<`, `>`, and `&` into an external script. Both JSON and snapshot script contain private records/history and must remain private. The CSP was not weakened and no network/storage API was added. This functional change is independent of the earlier blocked browser attempt; no real-browser policy workaround was attempted.

A second complete macOS installation succeeded in a fresh verification folder with an empty wiki and an automatic-loading snapshot. All 60 Python tests passed, including two new export round-trip/escaping and empty-snapshot tests. Node viewer tests passed for automatic fixture loading without a sample button, invalid bootstrap handling, and empty JSON; graph tests passed. Real-browser rendering and user-interface discovery remain unverified. Documentation links and patch checks passed. No push, PR, or publication occurred.

Earlier same-day records below describe superseded onboarding steps.

## Direct installation update — 2026-10-05 (earlier)

The user rejected fictional onboarding and requested immediate installation. The current README now leads with a copyable local Codex installation request and a direct Terminal command. The fictional exercise was removed from both READMEs and prompt introductions. Developer fixtures remain optional test material, never a prerequisite.

Added `scripts/install.py`: it reserves a new destination without following/replacing an existing destination, copies the self-contained skill, creates a dedicated virtual environment, installs its declared dependencies from PyPI, validates an empty revision-zero wiki, and renders the seven-menu viewer. The installed skill assets and viewer omit the sample button and `demo-data.js`. No fictional cards or real email data are imported. Installation failures preserve the new incomplete folder; existing projects are never overwritten.

Executed the installer on macOS with Python 3.14.7 in a public verification folder, including actual dependency installation. It reported `Valid; revision 0; 0 cards.` and created `.agents/skills/life-wiki`, `.venv`, `data/wiki.json`, `viewer`, and `OPEN-ME.txt`. HTML references resolve and installed files have no sample button or sample data script. Re-running against the existing destination exited with code 2 and preserved the original installation.

All 58 Python tests passed (including four new installer tests for empty setup, existing records, symlinks, and missing parent). Node viewer and graph tests passed; viewer tests also mount without a demo button and load an empty wiki. Relative links and `git diff --check` passed. Fresh Codex UI discovery, actual browser rendering, Windows/Linux installation, and execution of the installation request in another AI service remain unverified. No push, PR, or publication occurred.

The older same-day record below describes the superseded trial-first draft, not the current installation entry point.

## Beginner guide and public node graph revision — 2026-10-05

Reviewed public baseline: `c31053e34d76ed9f76f569a9a63dede2e9a05669`. Work was done in a fresh clone containing only this public repository. No repository AGENTS.md or .agents instructions were present; the repository skill and its operation/data/input guidance were read. The initial clone was clean. No remote push, PR, publication, real mailbox operation, private record copy, or deployment configuration change was performed.

The original public package contained AI instructions/templates, Python file helpers, and a read-only list viewer. It did not contain a node graph. README now starts with a copyable two-message fictional exercise, distinguishes conversation output from installed tools, and links a separate Korean installation guide. The English README and prompts reflect the same feature boundaries. The old private-site illustration is no longer used as an installation result.

The user subsequently requested matching public menus and a node graph, and explicitly excluded personal email connections, automatic updating, and deployment. After explicit permission to read the authenticated reference interface, only menu names/order and menu colors/layout were used for implementation. Private records, email, configuration, and assets were not copied into the public files. No private screenshot is included.

The revised local viewer has seven menus in reference order: Connection map (연결 지도), My records (내 기록), Operational changes (운영 변경), Decisions and evidence (결정과 근거), Topic records (주제별 기록), People and roles (사람과 역할), Reference records (참고 기록). A dependency-free canvas projects spherical node positions and supports drag rotation, zoom, selection, and keyboard reset. Edges come only from saved relations; uncertain edges are dashed. Search/status filtering affects the map and list. Accessible buttons and textual connection lists remain available. Source text remains inert; no network or browser persistence API was introduced.

### Checks actually performed

- macOS, Python 3.14.7, Node.js v24.13.0. A fresh `.venv` was created and `pip install -r requirements.txt` succeeded with jsonschema 4.26.0 from PyPI. The first restricted-network attempt failed DNS; the authorized dependency-only network retry succeeded.
- All 54 Python tests passed in the fresh environment after viewer changes. Node viewer checks passed for seven-menu navigation, graph alternatives, filtering, detail, fictional import, the 8MB limit, and inert text.
- New `node tests/graph.test.js` checks passed: evidence-only edges, uncertainty, filtering/empty input, spherical coordinates, canvas draw calls, node selection, drag rotation, wheel zoom, and keyboard reset. These use test doubles, not a real browser.
- Work snapshot: `Valid; revision 0; 4 cards.` Everyday snapshot: `Valid; revision 0; 2 cards.` Nine work input records normalized to eight sources. Both exports succeeded using the documented fresh destination commands; Markdown cards matched reviewed fixtures byte for byte.
- Exported directories contain `graph.js` and all scripts referenced by HTML. Relative links in the revised documentation and HTML IDs/script references were checked. `git diff --check` passed.
- Official Codex local skill discovery and explicit invocation guidance was checked against https://learn.chatgpt.com/docs/build-skills on this date. The self-contained copied-skill regression passed. Fresh Codex UI discovery/invocation was not exercised.
- The public offline-check workflow now calls the graph test as well as the existing checks. No hosted Actions run for these unpushed changes exists.

### Remaining limits

The browser tool rejected the local `file://` URL. No alternate-surface, HTTP-server, security-setting, or protocol workaround was attempted. Actual public viewer rendering, pointer behavior in a real browser, responsive layout, and visual parity with the reference site remain unverified. No generated or private-site screenshot is presented as proof. Windows/Linux installation commands and export behavior, different AI service prompt execution, and live email integration remain unverified.

Menus are aligned; private-site feature parity is not complete. Public JSON has no structured topic category or participant/role fields: topics use existing card titles and People and roles shows evidence and its limitation. Browser edits, direct addition, archive/trash management, server saving, private authentication, automatic updates, and deployment are not implemented. Operational changes is saved wiki history, not an automation/admin console.

The recommended fictional prompt was manually reviewed against its two messages. It was not executed in a separate AI account. It should yield one trip card with an unconfirmed date-change request; wording and output depend on the assistant. Mechanical tests do not establish semantic correctness or universal privacy erasure.

---

The sections below are historical records of earlier revisions, including earlier feature and visibility statements. The 2026-10-05 section above describes this unpushed revision.

## Work and everyday life positioning — 2026-10-03

The work-and-life revision updates visible viewer and exported-card wording, bilingual introductions and prompts, skill guidance, and fictional examples. Technical identifiers, schemas, original work-source fixtures, and the privacy-masked screenshot remain unchanged. The repository remains private until the user requests publication.

All 54 local Python checks passed with Python 3.14.7. Direct viewer checks passed with Node.js v24.13.0. The additional everyday life fixture contains two cards for a reservation change and learning enrollment, five retained email sources, and no invented relationship. Its eight-message input also includes an unrelated receipt, advertisement, and routine alert excluded from the manually interpreted output. The demo combines the four original work cards and these two everyday life cards. These results validate formatting, evidence integrity, and viewer behavior, not automatic email classification or real-world completion.

The prior commit `18554c42e71a3efb9aa7c47ee6be3a3c860bdca7` passed hosted run `37114687862` with 52 checks on each of Python 3.10/3.12/3.14 and Node.js 22. The revised workflow keeps those versions and also validates the everyday life JSON. Verify hosted results against the exact new commit in Actions; local results do not establish that the new hosted run has completed. No software was installed or browser protections relaxed for this revision.

## Earlier review fixes — 2026-10-03

This document records the local checks for the 2026-10-03 review fixes. The public comparison baseline was `1114830`. Results below distinguish reported execution from configured checks and unverified behavior. All fixtures and benchmarks are fictional; no real user material was permanently deleted.

## Baseline review

The supplied 2026-10-03 review reports 35 Python tests passing with Python 3.13/jsonschema 4.26, a passing Node viewer check, successful validation, nine inbox records normalized to eight sources, and rendered Markdown matching fixtures byte for byte. These are that review's results, not a new baseline execution by this document's author.

## Review-fix local checks

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
python3 skills/life-wiki/scripts/wiki.py validate examples/everyday/expected/wiki.json
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
