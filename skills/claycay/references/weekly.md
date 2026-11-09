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
2. **Schedule it** if this surface can run scheduled tasks (Cowork scheduled tasks, or
   `/schedule` in Claude Code): create one that runs weekly, Monday morning in their time
   zone, with the prompt below filled in. The key goes in the prompt as plain text, so say
   that it's only good for posting their score and they can replace it on claycay.com any
   time. If this surface can't schedule, tell them they can say "update my Claycay" whenever
   they like and it takes a minute.

## The weekly prompt

> Update my Claycay world at <artifact url> using the claycay skill, following
> references/weekly.md. <Post key: cck_...> Tell me the week in two lines.

## What an update does

1. Read the published world with the Artifact tool (`action: "read"`), save it, and run
   `python scripts/extract_activity.py world.html -o activity.json`. It prints the time zone
   and the last activity date. If it says there's no activity inside (a `--redact` world or
   one from before skill 1.11), gather everything again as on the first build.
2. Gather only what's new since that date (`references/gathering.md`), merge it in without
   duplicates (same title and date is the same item), and set `end` to today if it's set.
   Write `note` lines for the new chats and refresh the chapters that changed; keep the rest.
3. Rebuild with the same flags as before plus `--week`:
   `python scripts/build_world.py activity.json -o claycay.html --tz <tz> --week`.
   Add `--items <code>` if they have one. Don't write a "This week" chapter yourself; the
   script adds it with the real numbers.
4. Publish over the same artifact (pass its url), so the link and the quests the person
   ticked stay put.
5. With a post key: `python scripts/post.py claycay.html --key <key>`. It prints the new
   rank and the one before. Exit 2 means claycay.com couldn't be reached from here: say so
   and give the score card to paste on the site instead. Exit 1 means the board refused it
   (a replaced key, or posted less than 10 minutes ago): pass the message on.
6. Tell them the week in two lines: what grew (from the script's `week` output), the rank
   change if posted, and one coach tip if there's a new one. Nothing else.
