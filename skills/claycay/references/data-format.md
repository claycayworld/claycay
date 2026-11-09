# activity.json

One file holds everything the world is drawn from. Every list is optional; the world only
draws islands for lists that have something in them. Timestamps are ISO 8601. With no
offset they're read as UTC; `tz` decides which calendar day an event lands on.

```json
{
  "owner": "Dana",
  "title": "Dana’s Claycay",
  "tz": "Europe/Berlin",
  "start": "2026-07-01",
  "end": "2026-10-30",

  "chats": [
    {"title": "Fixing the pool pump", "updated_at": "2026-08-02T09:14:00Z",
     "url": "https://claude.ai/chat/…", "note": "One short line, written for the reader."}
  ],
  "artifacts": [
    {"title": "Weft System Map", "updated_at": "2026-10-19T09:19:00Z",
     "source": "code", "url": "https://claude.ai/artifact/…", "group": "Weft", "note": ""}
  ],
  "code_sessions": [
    {"project": "weft", "started_at": "2026-10-12T07:55:00Z", "title": "weft: 84 turns"}
  ],
  "projects": [
    {"name": "Haruspex", "note": "The stock scoring platform. Shut down in September.", "retired": true},
    {"name": "Recipes"}
  ],
  "tasks": [
    {"id": "inbox", "name": "Daily Inbox Dispatch", "schedule": "Every day at 06:30",
     "status": "ok", "note": "Sorts the night’s mail before breakfast."}
  ],
  "runs": [
    {"task": "inbox", "started_at": "2026-10-30T03:34:00Z", "outcome": "delivered"}
  ],
  "quests": [{"text": "Delete the old duplicate of the triage task."}],
  "quips": {"inbox": {"blocked": ["The mailbox said no. Rude."]}},
  "chapters": [
    {"focus": "world", "title": "Your Claycay", "text": "…"},
    {"focus": "forge", "title": "The Forge", "text": "…"}
  ]
}
```

## Field notes

- **artifacts.source**: `code`, `cowork`, `chat` or `design`. Code and design artifacts
  live in the Forge, Cowork ones in the workshop, chat ones become gold-roofed houses in
  the village. The Artifact tool's `list` action reports this as "from code/cowork/chat".
- **artifacts.group**: colors the roof. Leave it out and the build script uses the first
  word of the title when two or more titles share it ("Weft …", "BeamDesk …").
- **tasks.status**: `ok`, `watch`, `broken`, `duplicate` (drawn as a see-through ghost),
  `retired` (a gravestone). Any run whose `task` isn't listed creates a plain task.
- **runs.outcome**: `delivered`, `nudged`, `nothing_new`, `blocked`, `error`, `unverified`.
  Anything else is skipped. With any runs, the world gets a Counting House islet (the value
  ledger): delivered and nudged runs are gold, the rest and every run of a duplicate task are
  chimney smoke. Display only, no XP.
- **quests**: up to 5 the person can tick off in the trophy room for 50 XP each:
  `{"text", "why", "how", "kind"}` where `kind` is `todo` (default) or `tune`, `why` holds
  their real numbers and `how` is one line. A plain string still works. The script then adds
  up to 5 coach quests of its own (`scripts/coach.py`): tune quests for duplicate, failing
  (3 of the last 10 runs), watched or quiet (60% nothing new over 10+ runs) tasks and for 5+
  chats sharing a first word outside any project, and up to 2 discover quests for surfaces
  not used yet (project, artifact, scheduled task, Claude Code, Cowork). Discover quests show
  as ghost islands. The page also gets `coachMet`, the checks already satisfied, so a quest
  shown in an earlier build ticks itself once it's done.
- **item_codes**: optional list of shop items codes (`CI1.`). The script also stores codes
  passed with `--items` here, so the world carries them and weekly updates keep the items.
- **unseen**: optional list of surfaces you couldn't check (`projects`, `tasks`, `code`,
  `cowork`, `artifacts`). A surface also counts as unchecked when its key (`projects`,
  `tasks`/`runs`, `code_sessions`, `artifacts`) is missing. The coach never suggests an
  unchecked surface, so leave keys out rather than writing empty lists you didn't check.
- **quips**: optional per-task lines for the speech bubbles, keyed by task id and outcome.
  Without them, generic jokes are used.
- **chapters.focus**: `world`, `tasks`, `bank`, `forge`, `workshop`, `village`, `projects`, a task
  id, an item id the script assigns (`a3`, `c12`, `p0`), or a ghost island (`g:projects`,
  `g:tasks`, `g:forge`, `g:workshop`) when a discover quest exists. Prefer island names.

## Scoring (fixed, so worlds are comparable)

| Earns | XP |
|---|---|
| Chat | 10 |
| Artifact | 30 |
| Claude Code session | 15 |
| Project | 20 |
| Scheduled run | 5 delivered, 4 nudged, 2 nothing new, 1 for a failure ("you still showed up") |
| Achievement | 25 |
| Quest ticked off | 50 |

Level *n* starts at `25 × n × (n−1)` XP: level 2 at 50, level 5 at 500, level 10 at 2,250.
Titles run from Curious Visitor to Beyond Mythic.

Achievements are computed by the script with the moment each was earned, so they pop
during playback: First Words, Polyglot, Shipwright, Forge Fire, Assembly Line, Night Owl,
Early Bird, On a Roll, Habit Formed, Seven-Day Week, Island Hopper, Clockwork, Centurion,
Stubborn, Comeback Kid, Archipelago, Gravedigger, plus the secret Haunted.

## Score cards

The build script also embeds `card`: owner name, date range, longest streak, achievement
ids, counts (chats, artifacts by source, sessions, runs by outcome, failures, projects)
and XP per month. No titles, links or notes. The page encodes it as
`CC1.<base64url JSON>.<fnv1a checksum>` (cards starting `CW1.` from before the rename are still accepted). A receiving page recomputes XP from the counts
and checks it against the monthly totals; if they disagree the card is flagged.

## Items codes (shop)

Not part of activity.json: pass with `--items` (repeatable). Format
`CI1.<base64url JSON>.<base64url signature>`, payload
`{"v":1,"u":"<account id>","n":"<name>","i":["snowcap"],"t":"<issue date>"}`, signed by
claycay.com with ECDSA P-256 / SHA-256 (raw r||s). `scripts/items.py` holds only the
public key, so it can check codes but not make them. All codes in one build must belong
to one account. Unknown item ids are skipped with a note. Valid ids end up in the page as
`items`; they never enter the score card, because items don't affect XP.

Items this skill draws: `snowcap` (Snowcap Isles: snow on high ground, ice at the shore
and floes in the water, aurora at night).
