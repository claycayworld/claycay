# Weekly updates

A world is a snapshot, so it goes stale and so does the person's spot on the leaderboard.
A weekly update keeps both fresh and opens with a "This week" chapter.

## Offering it

After the first delivery, offer once, in one line: "Want your world to update itself every
week?" Don't push. If they say yes:

1. **Post key (optional, for the leaderboard).** They sign in on claycay.com, open the Join
   section and press "Get my post key", then paste it to you. The key can only post their
   own score card (counts and achievement ids, never titles), and getting a new key turns
   the old one off. Without a key the update still rebuilds the world; it just doesn't post.
2. **Schedule it** only where the update can reach what you just gathered: the world (the
   published artifact or the local file) and the same tools you gathered with. Before you
   create a task, check that the scheduler on this surface runs with those tools, for example
   a Cowork scheduled task on the same computer. Claude Code's `/schedule` runs in the cloud,
   so it can't see this computer's Code sessions or a world saved as a local file: don't use
   it for this. Run the task weekly, Monday morning in their time zone, with the prompt below.
   The key goes in the prompt as plain text, so say it's only good for posting their score
   and can be replaced on claycay.com any time. With no suitable scheduler, tell them they
   can say "update my Claycay" whenever they like and it takes a minute.

## The weekly prompt

> Update my Claycay world at <artifact url, or the file path> using the claycay skill,
> following references/weekly.md. <Post key: cck_...>

## What an update does

Run the scripts with `python3` from the skill folder (use `python` if that's what exists).

1. **Get the old world.** A published world: read it with the Artifact tool
   (`action: "read"`) and save it as `old.html`. A local file: copy it to `old.html`. Then run
   `python3 scripts/extract_activity.py old.html -o activity.json`. It prints the time zone,
   `start`, and `last`: the newest date for each source. If it says there's no activity
   inside (a `--redact` world, or one from before skill 1.11), gather everything again as on
   the first build.
2. **Gather each source since its own date** in `last` (that day included, the merge drops
   repeats). `null` means it was never gathered: gather it in full from `start` if you can
   reach it now and add its key, otherwise keep leaving it out. A source you gathered before
   but can't reach from here (for example chats, when this run is in Claude Code): keep its
   old entries as they are. For Claude Code use
   `python3 scripts/collect_claude_code.py --since <start>`; the merge handles the overlap.
3. **Merge without duplicates.** Chats and artifacts match on `url` (title when there's no
   url); on a match keep the newer one, since a continued chat or edited artifact moves its
   date. Code sessions match on project plus `started_at`, runs on task plus `started_at`.
   Set `end` to today if it's set. Write `note` lines for new chats and refresh the chapters
   the new data changes. If there's no "What's next" chapter, add one from the best coach
   quest. Drop written quests that are done or that a coach quest now covers.
4. **Rebuild** with the old time zone and `--week --previous old.html`:
   `python3 scripts/build_world.py activity.json -o claycay.html --tz <tz> --week --previous old.html`
   (plus `--redact` if the world was redacted). Shop item codes are kept inside the activity
   (`item_codes`), so no flag is needed for them. Don't write a "This week" chapter yourself:
   the script adds it with the real numbers, covering everything since the old world.
5. **Put it back**: publish over the same artifact (pass its url), or overwrite the same
   local file, so the link and the quests the person ticked stay put.
6. **Post** with a post key: `python3 scripts/post.py claycay.html --key <key>`. It prints
   the new rank and the one before. Exit 2 means claycay.com couldn't be reached from here:
   say so and give the score card to paste on the site. Exit 1 means the board refused it
   (a replaced key, or posted less than 10 minutes ago): pass the message on.
7. **Tell them** in two lines, from the script's `week` and `since` output: what grew, any
   level-up or new achievement, the rank change if posted, and the first of `new_coach` if
   there is one. If a source couldn't be reached this time, add one line saying which.
