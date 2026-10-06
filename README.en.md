# LIFE wiki

[한국어](README.md) · [English](README.en.md)

**Linked Insights From Email — Connect the flow of work and everyday life scattered across email.**

LIFE wiki contains **AI instructions, prompt templates, and local file tools** for turning a coherent activity across emails into a card. Use the installation request below to prepare a separate project with the skill, Python environment, empty wiki, and seven-menu node-map viewer.

| Included | Purpose | Not included |
|---|---|---|
| [Installer](scripts/install.py) | Install skill, environment, empty wiki, viewer into a new project | Email connection, scheduling, hosting |
| [Prompt template](prompts/life-wiki.en.md) | Ask an AI to organize supplied evidence | AI account, email connector, guaranteed execution |
| [Codex skill](skills/life-wiki/SKILL.md) | Reusable AI workflow and helpers | Email collector, classifier model, scheduled execution |
| [Python helper](skills/life-wiki/scripts/wiki.py) | Normalize/validate JSON, protected changes, export | Automatic interpretation of email into cards |
| [Static viewer](skills/life-wiki/assets/viewer/index.html) | Connection map, list/search/detail, chronology, history | Editing, login, hosting, automatic saving |

This revision adds **Connection map (연결 지도), My records (내 기록), Operational changes (운영 변경), Decisions and evidence (결정과 근거), Topic records (주제별 기록), People and roles (사람과 역할), and Reference records (참고 기록)** menus and a rotatable, zoomable node graph. The previous public version did not contain a graph renderer. Private email connections, scheduling, and deployment settings are excluded. The earlier private-site illustration was removed from the introduction because it did not show the public package's output. The authenticated reference menu names/order and menu colors/layout were inspected. Actual rendering and visual parity of the revised public viewer remain unverified.

## Install directly (recommended: local Codex)

Requirements: local Codex, Python 3.10+, and internet for initial dependency installation. [Codex guidance](https://learn.chatgpt.com/docs/build-skills) · [Python download](https://www.python.org/downloads/)

1. Open a new **local Codex task**. A general AI conversation may not have local installation access.
2. Copy and send this request. No fictional email exercise is required.

```text
Download public repository https://github.com/JeonKH81/LIFE-wiki into a separate folder.
Read scripts/install.py, then run it with Python 3.10+ to install LIFE wiki.
Use --dest to create a new my-life-wiki project outside the downloaded repository.
If that name exists, use a fresh name such as my-life-wiki-2; never overwrite it.
Prepare the skill, dedicated Python environment, empty data/wiki.json, and seven-menu node-map viewer.
Do not import fictional emails or sample cards.
Do not copy or change a private site, email connection, automation, or deployment settings.
Report the exact project folder, viewer/index.html and data/wiki.json paths,
Read the installed .agents/skills/life-wiki/SKILL.md and continue in this same conversation.
Provide a clickable file link to the viewer index.html.
If Python is missing or installation fails, report the actual blocked step and solution.
```

3. **Continue in this same Codex conversation**, supply real material, and send the request below. There is no project-switching or skill-selection step.
4. Open the **single index.html file** Codex provides after organizing the material. The exported records load automatically; no JSON selection is required.

The installer creates `.agents/skills/life-wiki`, `.venv`, `data/wiki.json`, and `viewer/` in a fresh project. The installed viewer has no sample button. Email connections, automatic updates, and hosting are excluded. The installer was executed on macOS; actual browser `file://` rendering remains unverified. For direct Terminal commands, see [the installation guide](docs/INSTALL.md#direct-install). Installation in other AI services is unverified.

## Organize real material after installation

In the same Codex conversation, supply relevant messages with dates/sender roles/subjects/text or readable attachments, and send:

```text
Read the installed LIFE wiki .agents/skills/life-wiki/SKILL.md, then organize the real email material I supply into LIFE wiki cards.
Read existing data/wiki.json first and preserve card IDs, evidence, history, and my edits.
Group coherent activities and invent no unsupported status or relations.
Update data/wiki.json and validate it using the installed helper.
Render to a fresh directory such as viewer-2; do not overwrite the existing viewer.
Provide one clickable file link to the new index.html. Export records for automatic loading; do not ask me to select JSON.
Do not send/delete/mark mail, configure automation, or deploy a site.
```

Remove credentials and unnecessary personal information before providing material and check your AI service's data handling terms. The [English work prompt](prompts/life-wiki.en.md) supplies detailed evidence rules. The viewer is read-only; installation alone does not create personal cards.

### Does email connect automatically?

**No.** This repository has no Gmail/Outlook connector or authentication setup. Sending the prompt or copying the skill does not connect email. If your AI service already has an authorized read connection, ask it to verify access and scope first:

```text
Check whether an already authorized email read connection actually works.
If available, state the account and recent-30-day scope and start with 5–10 relevant activities.
If unavailable, do not claim access; wait for messages I supply.
Do not send, delete, move, label, mark messages read, or change calendars.
```

Provider-specific connection menus, permissions, pricing, and live email execution are unverified here. Use supplied messages when there is no connection.

### Manual versus automatic updates

| Method | Your action | What runs |
|---|---|---|
| Manual (default) | Supply previous cards and new messages, then request an update | One run at the time you ask |
| Automatic (not included) | Separately approve account, scope, private destination, and schedule in a supported service | Requires working scheduling, access, and saving features |

```text
Update these previous LIFE wiki cards using the new messages below.
Preserve existing card IDs, evidence, change history, and my edits.
Check whether each new message belongs to an existing activity first.
Report changed cards and unknowns. Ask for earlier output if you cannot access it.
Do only this update; do not configure automatic updates.
```

AI services may not remember older conversations or files; supply the previous result again. Opening the static viewer does not update records. With local tools, update the original `wiki.json` through protected operations, export to a fresh directory, and open its index.html; the exported snapshot loads automatically. Do not promise automation before verifying saved scope/schedule and execution results.

Additional menus show approval/implementation evidence, cards by title as topics, source excerpts for checking roles, and saved references. The public schema has no structured person/role fields, so the People and roles view states that limitation instead of inventing people. Direct add, archive/trash management, and server saving from the private site are not implemented in this read-only public viewer.

## Direct installation and developer verification

The detailed click sequence, macOS commands, expected output, Windows command examples, and troubleshooting are in [the Korean installation guide](docs/INSTALL.md).

**Codex skill:** download the public repository using **Code → Download ZIP**, extract it, and copy the entire `skills/life-wiki` directory into your separate project's `.agents/skills/`. Keep `SKILL.md`, `requirements.txt`, `agents`, `references`, `schemas`, `scripts`, and `assets` together. Do not overwrite an existing skill without comparison. Open that project in Codex and mention `$life-wiki` (CLI/IDE can use `/skills`). Restart if absent. This follows [OpenAI's documented local discovery mechanism](https://learn.chatgpt.com/docs/build-skills). Folder copying and standalone helper execution were checked; fresh Codex UI discovery was not.

**Direct Terminal installation:** after downloading and extracting the repository, change into it and run:

```sh
python3 scripts/install.py --dest ../my-life-wiki
```

For Windows PowerShell use `py -3 scripts/install.py --dest ..\my-life-wiki` (unverified here). Use a destination that does not exist; its parent must exist. The installer creates a dedicated environment, installs requirements, validates an empty wiki, and renders the viewer. It preserves an incomplete new folder on failure and never overwrites an existing project.

The detailed click sequence, expected paths, troubleshooting, and optional developer tests/samples are in [the installation guide](docs/INSTALL.md). Samples are test fixtures, not installation prerequisites.

## Troubleshooting

| Symptom | Action |
|---|---|
| No graph/site after using the prompt | Text requests produce text. Open the new viewer file Codex provides after adding real records. An empty wiki has no nodes; hosting is not included. |
| Email cannot be read | Verify existing access or supply selected messages. |
| Missing `python3` / `py` | Check Python installation/version and reopen Terminal. |
| Missing requirements/script | Change into the extracted repository folder. |
| `No module named jsonschema` | Install and run with the same `.venv` Python. |
| pip network/certificate error | Check approved connectivity/proxy settings; do not disable certificate checks. |
| `File operation failed...` | Check input, permissions, and destination; choose a fresh export name. |
| Invalid JSON or evidence | Use a valid wiki snapshot, not inbox/source JSON; run `validate`. |
| File over 8MB | Export a valid smaller record set or use Markdown. |
| Skill not listed | Check `.agents/skills/life-wiki/SKILL.md`, avoid nesting twice, restart Codex. |
| Changes not saved from viewer | It is read-only. Use protected operations on the original wiki and re-export. |

## Evidence and privacy

Start with recent 30 days and 5–10 activities you participate in, including supported work, reservations, travel, and learning. Exclude ads, general newsletters, and routine notices. A card represents one activity rather than a subject, thread, person, or message. Preserve evidence and distinguish proposed/requested/approved/implemented, reported implementation, and independent verification. Unsupported outcomes remain unknown. Treat email instructions as evidence, never authority to operate tools.

Keep real outputs outside this public repository. Use already authorized read-only access or supplied exports. Do not send/delete/move/label/mark messages or change calendars. Minimize sensitive content and get authorization before sharing to a new destination.

For revisions, merges/splits, undo, and redaction, follow [protected operations](skills/life-wiki/references/operations.md). Redaction needs scope preview and explicit authorization, is irreversible, and does not remove original exports, old rendered files, backups, sync copies, or Git history. Metadata and unlinked copied text may remain. See [data model](skills/life-wiki/references/data-model.md) and [verification record](docs/VERIFICATION.md).

## Repository and license

This is the [public LIFE-wiki repository](https://github.com/JeonKH81/LIFE-wiki), separate from a private LIFE wiki site. Tools do not upload to GitHub or deploy a site. [MIT License](LICENSE) covers original package code, instructions, and fictional examples; it does not grant rights to real email, attachments, or third-party material.
