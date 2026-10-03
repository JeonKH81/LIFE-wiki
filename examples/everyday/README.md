# Fictional everyday life example / 가상 일상 예제

All people, dates, messages, and plans are invented. Addresses use reserved `.example` domains. No live email, actual reservation, calendar, payment, or personal record is used or changed.

업무와 일상의 맥락은 같은 출처·상태 원칙으로 정리합니다. 아래는 이메일을 직접 읽고 판단한 가상 예시이며, 도구가 자동으로 중요도를 정하거나 모든 메일을 카드로 분류한다는 뜻은 아닙니다.

[inbox.json](inbox.json) has eight messages. The reviewed [expected/wiki.json](expected/wiki.json) selects five sources for two coherent activities; its [Markdown cards](expected/cards/) are generated projections. The viewer's fictional demo combines these two cards with the four original work cards.

| Card | Expected interpretation | Boundary |
|---|---|---|
| ISLET 여행 예약 변경 | requested; outcome unknown | One trip spans a proposal, reservation confirmation, and later date-change request across threads. The latest request supersedes the earlier supported phase. A confirmed reservation does not prove travel, and the requested change is not confirmed. |
| PINE 드로잉 수업 등록 | implemented; reported_implemented | A request and enrollment notice concern the same course enrollment. The notice reports enrollment only. Attendance, learning completion, and independent verification remain unknown. |

The unrelated stationery receipt, general advertisement, and routine alert are excluded from the interpreted snapshot. They do not describe a meaningful decision or change in a selected activity. A receipt or alert that actually supports such a change could be retained as evidence for an existing card. Sharing the same mailbox does not justify a relation between ISLET and PINE, so no relation is invented.

An existing `work-*` ID remains the portable card identifier for both work and everyday life; schemas and relation type identifiers are unchanged.

To validate or view these cards using the repository helper:

```sh
python3 skills/life-wiki/scripts/wiki.py validate examples/everyday/expected/wiki.json
python3 skills/life-wiki/scripts/wiki.py render examples/everyday/expected/wiki.json --out /tmp/life-wiki-everyday-demo
```

Use a fresh destination. Open its local viewer and choose the exported `wiki.json` for these two cards. The “가상 예제 보기” button shows the combined six-card demo. Actual browser `file://` compatibility remains unverified.
