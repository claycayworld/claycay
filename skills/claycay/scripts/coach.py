"""The coach: quests worked out from a person's own activity, so the world says what to try next.

Three kinds, shown in this order:
  todo      quests Claude wrote into activity.json (things it saw in the data or conversation)
  tune      patterns worth fixing: a task that keeps failing, one that mostly finds nothing new,
            a pile of chats that would work better as a project
  discover  a Claude surface the person hasn't used yet; the world draws it as a ghost island

Each coach quest carries an id, a `why` with the person's real numbers and a one-line `how`.
`met` lists the ids of checks that are already satisfied, so a world can tick off a quest it
showed in an earlier build once the person has done it.

A surface is only suggested when activity.json says it was looked at: its key is present
(an empty list means "looked, found none") and it isn't listed in `unseen`.
"""
import re
from collections import Counter

FAILS = {'blocked', 'error', 'unverified'}

DISCOVER = [
    # id, island the world draws as a ghost, text, why, how
    ('project', 'projects', 'Start your first project',
     'You have {chats} chats and no projects yet. A project keeps related chats together with shared files and instructions, so you stop re-explaining yourself.',
     'On claude.ai, open Projects in the sidebar, choose New project, and add the files and instructions you keep pasting.'),
    ('artifact', None, 'Make your first artifact',
     'Artifacts are things Claude makes that you keep: a page, a checklist, a small tool. Each one becomes a gold-roofed house in your village.',
     'In a chat, ask for something you will reuse, like “make me a packing checklist I can tick off”.'),
    ('task', 'tasks', 'Put Claude on a schedule',
     'Nothing runs on its own yet. A scheduled task does a job for you on a timer, like a morning briefing, and every run lands at your lighthouse.',
     'In Cowork, create a scheduled task, or type /schedule in Claude Code. Start with one small daily job.'),
    ('code', 'forge', 'Build something in Claude Code',
     'Claude Code works inside a folder on your computer and can build, run and fix whole projects. Everything it makes lands in the Forge.',
     'Install Claude Code, open a terminal in any folder, type claude, and ask for a small tool you have wanted for a while.'),
    ('cowork', 'workshop', 'Hand a job to Cowork',
     'Cowork takes on longer jobs with the files on your computer, like turning a folder of notes into a report. What it builds goes to the Workshop.',
     'Open the Claude desktop app, switch to Cowork, and describe the job and the folder it should use.'),
]


def first_word(title):
    w = re.split(r'[\s:\-–—_/]+', (title or '').strip())[0] if title else ''
    return w if len(w) >= 3 else ''


def coach_quests(raw, chats, arts, sessions, tasks, runs, redact=False):
    """Return (quests, met). chats/arts/sessions/tasks/runs are build_world's normalised lists."""
    unseen = {str(u).lower() for u in raw.get('unseen', [])}
    seen = lambda key, surface: key in raw and surface not in unseen
    projects = raw.get('projects', [])
    pnames = [(p.get('name') if isinstance(p, dict) else str(p)).lower() for p in projects]
    n_code = sum(a['src'] in ('code', 'design') for a in arts)
    n_cowork = sum(a['src'] == 'cowork' for a in arts)
    met, tune, discover = [], [], []

    # biggest group of chats sharing a first word, for project hints (never with --redact: it would leak a title)
    groups = Counter(first_word(c['t']).lower() for c in chats if first_word(c['t']))
    top_word, top_n = (groups.most_common(1)[0] if groups else ('', 0))
    shown_word = next((first_word(c['t']) for c in chats if first_word(c['t']).lower() == top_word), top_word)

    # ---- tune: scheduled tasks
    by_task = {}
    for r in sorted(runs, key=lambda r: r['when']):
        by_task.setdefault(r['task'], []).append(r)
    for t in tasks:
        rs = by_task.get(t['id'], [])
        last10, last20 = rs[-10:], rs[-20:]
        fails = [r for r in last10 if r['o'] in FAILS]
        quiet = [r for r in last20 if r['o'] == 'nothing_new']
        checks = {
            f't_dup:{t["id"]}': t['status'] == 'duplicate' and {
                'text': f'Delete the duplicate task “{t["name"]}”',
                'why': 'It runs alongside the original, so every run happens twice.',
                'how': 'Find it in your scheduled tasks and delete the copy you made last.'},
            f't_fail:{t["id"]}': t['status'] != 'retired' and (len(fails) >= 3 or t['status'] == 'broken') and {
                'text': f'Fix “{t["name"]}”',
                'why': (f'{len(fails)} of its last {len(last10)} runs failed, the latest on {fails[-1]["when"]:%d %b}.' if fails
                        else 'It is marked as broken.'),
                'how': 'Open its last failed run and ask Claude why it failed. A missing permission or a page that moved is the usual cause.'},
            f't_quiet:{t["id"]}': t['status'] != 'retired' and len(last20) >= 10 and len(quiet) / len(last20) >= .6 and {
                'text': f'Run “{t["name"]}” less often',
                'why': f'{len(quiet)} of its last {len(last20)} runs found nothing new.',
                'how': 'Stretch its schedule (hourly to daily, daily to weekly), or have it report only when something changed.'},
            f't_watch:{t["id"]}': t['status'] == 'watch' and {
                'text': f'Check on “{t["name"]}”',
                'why': 'It is on your watch list.',
                'how': 'Read its last few runs and decide: keep it, fix it, or retire it.'},
        }
        for qid, q in checks.items():
            if q:
                tune.append({'id': qid, 'kind': 'tune', **q})
            else:
                met.append(qid)

    # ---- tune: a big group of chats outside any project
    if not redact and projects and top_n >= 5 and not any(top_word in p for p in pnames):
        qid = f't_group:{top_word}'
        tune.append({'id': qid, 'kind': 'tune', 'text': f'Give your “{shown_word}” chats a project',
                     'why': f'{top_n} chats start with “{shown_word}”. In a project they share files and instructions, so each new chat starts with the context.',
                     'how': f'Make a project called {shown_word}, add your usual files and instructions, and start the next one there.'})

    # ---- discover: surfaces not used yet, only where we could actually look
    have = {'project': bool(projects), 'artifact': bool(arts), 'task': bool(tasks),
            'code': bool(n_code or sessions), 'cowork': bool(n_cowork)}
    looked = {'project': seen('projects', 'projects'), 'artifact': seen('artifacts', 'artifacts'),
              'task': seen('tasks', 'tasks') or seen('runs', 'tasks'), 'code': seen('code_sessions', 'code'),
              'cowork': seen('artifacts', 'cowork')}
    worth = {'project': len(chats) >= 5, 'artifact': len(chats) >= 3,
             'task': len(arts) >= 3 or len(sessions) >= 3 or len(chats) >= 15,
             'code': len(arts) >= 2 or len(chats) >= 10, 'cowork': len(arts) >= 3 or len(sessions) >= 3}
    for key, island, text, why, how in DISCOVER:
        qid = 'd_' + key
        if have[key]:
            met.append(qid)
            continue
        if not (looked[key] and worth[key]):
            continue
        why = why.format(chats=len(chats))
        if key == 'project' and not redact and top_n >= 3:
            why += f' Your {top_n} “{shown_word}” chats would make a good first one.'
        discover.append({'id': qid, 'kind': 'discover', 'island': island, 'text': text, 'why': why, 'how': how})

    order = ['t_dup', 't_fail', 't_watch', 't_quiet', 't_group']
    tune.sort(key=lambda q: order.index(q['id'].split(':')[0]))
    return tune[:3] + discover[:2], met
