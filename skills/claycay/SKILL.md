---
name: claycay
description: Claycay (clay-kay). Turns a person's Claude activity (chats, artifacts from Claude Code, Cowork and chat, Code sessions, projects, scheduled-task runs) into a playable blocky island world with a story, a day-by-day timeline, XP, levels, achievements and quests. Use this whenever someone asks to see, visualize, map, gamify, score, recap or "wrap" their Claude usage, wants a game or story made from their Claude history, asks for a "Claude Wrapped" or year-in-review, asks what level they are or what they've built with Claude, mentions Claycay, or asks for a voxel or blocky view of their work, even if they don't say "world" or "skill".
---

# Claycay

Claycay (pronounced clay-kay; a cay is a small island built up from sand and coral) is an
independent project, not affiliated with Anthropic. In anything user-facing, call the
product Claycay and refer to Claude only descriptively ("your Claude activity").

Build one self-contained web page where the person's Claude activity becomes islands:

- **Scheduled tasks** island: one tower per task, a lighthouse that collects successful runs,
  ghosts for duplicates, gravestones for retired tasks. Failed runs bonk, smoke and complain
  in speech bubbles.
- **The Forge**: artifacts built in Claude Code (and Code sessions), newest by the fire.
- **Cowork Workshop**: artifacts built in Cowork.
- **Chat Village**: one house per chat.
- **Project Archipelago**: one islet per project.
- **The islander**: a small voxel character who walks around the village square on days the
  person used Claude, and sleeps in a sleeping bag with floating Zzz on days they didn't
  ("asleep 4 days" for a streak). Scheduled runs alone don't wake them, which shows that
  the tasks keep working while the person rests.

On top sits a game layer: XP for everything, levels with titles, achievements that pop
during playback with the moment they were earned, quests the person can tick off for XP,
a blooper reel of failed runs, and a league: players swap score cards (a short code
with counts and achievements only, no titles) and the trophy room ranks everyone by
all-time XP or XP this month, with crowns for most built, chattiest, automation king,
longest streak, collector and most stumbles. The person opens it, presses play and watches their
history unfold with their score climbing.

## Workflow

1. **Gather.** Read `references/gathering.md` and collect what this surface can reach.
   Do it without asking first; only ask for things you genuinely can't get (for example
   project names when there's no list). Tell the person in one line what you could and
   couldn't see.
2. **Write the story.** Write 5 to 9 chapters (`chapters` in activity.json): an opening
   over the whole world, one per island that exists, and a closing one about score and
   quests. Each is 2 to 4 sentences, concrete, with real numbers and names from their
   data, and a bit of warmth or humor. Write them in the person's language. Write the chat
   `note` lines and any task `quips` the same way. This is what makes it theirs rather
   than a dashboard, so spend effort here.
3. **Quests.** Add 2 to 5 open to-dos you actually saw in the data or conversation
   (a broken task to fix, a duplicate to delete, a draft never sent). Don't make up chores.
4. **Build.** Save `activity.json` (schema: `references/data-format.md`) and run
   `python scripts/build_world.py activity.json -o /mnt/user-data/outputs/claycay.html --tz <their IANA zone>`
   (add `--redact` if they chose it). If they have an items code from the claycay.com shop
   (it starts with `CI1.`), add `--items <code>`. The script prints counts, XP, level,
   achievements, `items` and `item_notes`; read it to check nothing came out empty by
   mistake, and pass any item note on to the person in plain words. If `update` is set,
   a newer version of this skill is out: tell them in one line at the end and keep going.
   It's null when they're up to date or claycay.com can't be reached; then say nothing.
5. **Deliver.** If the Artifact tool is available, publish the file with it (favicon 🧱).
   Otherwise present the HTML file. On a second build for the same person, update the
   same artifact by passing its url.
6. **Tell them** their level and title, two or three achievements worth bragging about,
   one they're closest to unlocking, and how to play (press ▶, tap things, open 🏆). Mention
   📸 next to the trophy: it saves a postcard picture of their island with level and counts,
   never titles, ready to post.
   Mention the league in one line: 🏆 → copy the score card, then either post it on
   claycay.com (the public leaderboard) or send it to a friend who has their own Claycay.
   If the person asks where they rank, or has posted before, run `scripts/rank.py` (below).
   Keep it short and don't list every number; the page does that.

## Things to get right

- Only draw real items. If a list is empty, leave it out; the island simply won't appear.
- Use the person's own words for project and task names. Don't fix their typos.
- Keep notes free of sensitive specifics (health, money, family conflicts, legal trouble).
  Titles that already say it are their call, which is why the redact option exists.
- The template is copied verbatim; don't hand-edit it per person. Everything personal goes
  through activity.json, so the page stays consistent and the scoring stays fair.
- The look is Claycay's own voxel style. Don't add logos, characters, textures or names
  from any real game, even if someone asks for one by name; say this is Claycay's own
  style and move on. Don't compare it to other games either.
- The page needs WebGL and loads three.js r128 from cdnjs plus two Google Fonts. It works
  as a published claude.ai artifact and as a local file opened in a browser.

## Shop items

People who bought looks on claycay.com (island themes, avatars, objects, effects) get one
items code that covers everything they own. Ask once, briefly: "Got a Claycay items code?
Paste it and I'll add your items." Don't push it. Never invent or edit a code; the build
script checks its signature and skips anything that doesn't check out. Items are looks
only: they never change XP, level or the score card. If the script says an item needs a
newer skill, tell them to download the skill again from claycay.com. Keep the code with
their activity.json so the next rebuild keeps their items.

## Sharing a world

A shared world doubles as a challenge: whoever opens it can paste their own score card in
the trophy room and see where they rank against its owner. Two ways to share:

- **claude.ai link.** The published artifact's Share button. It starts private; whether
  viewers need a Claude account depends on the person's plan and current sharing
  settings, so suggest they test the link in a private window.
- **Anywhere else.** The page is one self-contained HTML file (three.js and fonts load
  from public CDNs), so it can go on GitHub Pages, Netlify, their own site, or be sent
  as a file.

Before a public share, offer a rebuild with `--redact`. Chat links in the page lead to the
owner's own chats, which nobody else can open anyway, and artifact links work only for
artifacts they've published. Quests ticked and rivals added live in each visitor's own
browser, so visitors never see or change the owner's.

## Checking their rank

`python scripts/rank.py /mnt/user-data/outputs/claycay.html` (or pass the `CC1.` card
code; `build_world.py` prints it as `card`) asks claycay.com where that card stands on the
public leaderboard. It prints JSON: `players` (how many are on the board), `top` (rank,
name, level, XP), and `you` with `rank` all-time and `month.rank` for XP this calendar
month (UTC). `--top 0` to 50 sets how many top players come back; with no card it lists
only the top. Use it when someone asks "what's my rank?", "who's winning?" or "how far
behind the leader am I?", and answer in a line or two ("You'd be #12 of 340, 410 XP behind
#11").

Things to know:

- It sends only the card (counts, achievement ids, display name) and stores nothing. It
  does not post: the rank is where this card *would* stand. To actually join the board they
  sign in on claycay.com and paste the card there.
- If the output has `update`, a newer version of this skill is out: after the rank, pass
  it on in one line and keep going.
- `rank` is null when the card doesn't add up (`honest: false`); say the numbers don't
  check out and suggest a rebuild.
- The claude.ai sandbox may block outside sites. If the script can't reach claycay.com,
  say so in one line and point them to https://claycay.com/#leaderboard. Don't retry in a
  loop and don't guess a rank.

## The league, honestly

Inside a world there's no central server: each page keeps its rivals in the viewer's
browser, so a league is whoever has swapped cards. The public board on claycay.com is the
one shared place. A card carries a checksum that catches typos and
casual edits (a card whose numbers don't add up gets ⚠️, ranks last and can't win
crowns), but it is not tamper-proof, since the scoring rules are public. Say so if asked;
it's a friendly league, not an anti-cheat system. Ask people to send a fresh card after
they rebuild their world, since cards are snapshots.

## Updating later

Keep the activity.json. Next time, gather only what's new since its `end`, merge it in,
rebuild and publish over the same artifact. Quests the person ticked off are remembered
by their browser, keyed to their name and start date.
