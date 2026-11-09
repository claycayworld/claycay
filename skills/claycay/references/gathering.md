# Gathering activity

Use whatever this surface offers and skip what it doesn't. A world with only chats is
still a good world. Never invent items to fill an island. Leave out the key of anything you
couldn't look at; an empty list tells the coach you looked and found nothing, and it will
then suggest trying that feature.

## claude.ai (chat)

**Chats.** `recent_chats` with `n: 20`, paging backwards with `before` set to the oldest
`updated_at` of the previous batch. Stop after about 5 calls or once you pass the start
date. Skip chats whose content is redacted. Chats inside projects are only searchable from
inside that project, so from a normal chat you'll only see chats outside projects; say so.
Write each chat a `note` of under 12 words in plain language ("Turning a green pool blue
again."), drawn from the summary. Don't put health, money or relationship details in a
note; the title is enough.

**Artifacts.** The Artifact tool, `action: "list"`, `limit: 200`. Each row says
"from code", "from cowork" or "from chat": that's the `source`. The link is the `url`.
Leave out the world page itself if it already exists.

**Projects.** Project names may appear in the memory listing as `/projects/<id>/ — Name`.
Use those names. If there's no list, ask the person to paste their project names, or skip
the archipelago.

**Scheduled tasks and runs.** Only if the person keeps a run log. Look in memory for
something like a run ledger and read its database with the Artifact tool (`read_db`).
Map its fields onto `tasks` and `runs`. Without a log, leave both out.

## Claude Code

Run `scripts/collect_claude_code.py` to list sessions from `~/.claude/projects`. It reads
timestamps and folder names only, never message content. Artifacts made in Code can also
come from the Artifact list if that tool is connected.

## Cowork

Use the Artifact list (rows "from cowork") and any scheduled-task log the person has.
Cowork's own task history, if a tool exposes it, maps onto `tasks` and `runs`.

## Privacy

The finished page shows chat titles and project names. Before building, ask one question
if the person might share it: real titles, or `--redact` (titles become "A chat from 12
Aug", links and task notes are dropped). Published artifacts start private either way.
