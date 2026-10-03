# Work boundaries and status

Choose the smallest coherent unit with a meaningful objective and outcome: for example, a pilot rollout, an onboarding checklist revision, or a handoff guide. Keep a stable ID after titles change.

Strong evidence of continuity includes an explicit work code or a statement that a new thread continues the same deliverable. Shared participants, similar wording, dates, or matching subjects are hints. They do not establish identity. An email requesting both a pilot and a checklist can contribute a separate excerpt to each card. A quoted or forwarded message does not add independent implementation evidence.

For plausible but unproven connections, retain distinct cards and an `uncertain` relation, usually `possible_same_work` or `related`. Include a rationale and the evidence needed to resolve it. `possible_same_work` can never be `confirmed`; confirmation should be followed by a user-directed merge or a different relation type. Confirmed dependencies require an explicit supporting excerpt. Relations describe work, not communication threads.

Each timeline event records one assertion and its exact excerpt. `kind` is `proposed`, `requested`, `approved`, `implemented`, or `unknown`. `basis` is `explicit` or `inferred`. Explain inferred assertions in the summary; never use inference to justify implemented status or outcome. A card's `status` represents its current supported phase, not a numeric maximum of all historic phases. For changes, rescinded approvals, or contradictions, select the defensible phase and state the issue in `unknowns`; do not erase the earlier event.

`status: implemented` requires explicit implemented evidence. Outcome:

- `unknown`: no adequate evidence of the work's result; cite no outcome evidence.
- `reported_implemented`: a source explicitly reports implementation; cite implemented events.
- `verified_implemented`: those implemented events must also have `verification: true`, set only after a distinct artifact or independent source actually verifies the result. A sender saying “done” is a report, not verification. Record what was checked in the event summary.

Neither implementation label means the work is permanently closed. Scope, later defects, and remaining work may still be unknown. No automatic “done” or archive rule exists. Preserve contradictory sources and partial outcomes in chronology and `unknowns`. The helper checks references and labels, while the assistant and user remain responsible for semantic judgment.
