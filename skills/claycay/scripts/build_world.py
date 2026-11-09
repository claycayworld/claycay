#!/usr/bin/env python3
"""Turn a Claude activity file (activity.json) into a single self-contained world page.

Usage:
  python build_world.py activity.json -o world.html [--redact] [--tz Asia/Jerusalem] [--items CI1.xxx]

Everything the page needs (layout data, XP, achievements, chapters, quests) is computed
here and embedded, so the HTML works offline apart from three.js and two web fonts.
The schema of activity.json is in references/data-format.md.
"""
import argparse, datetime as dt, hashlib, json, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coach
import items as shop
import version

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, '..', 'assets', 'world-template.html')

XP = {'chat': 10, 'artifact': 30, 'session': 15, 'project': 20, 'quest': 50, 'achievement': 25,
      'run': {'delivered': 5, 'nudged': 4, 'nothing_new': 2, 'blocked': 1, 'error': 1, 'unverified': 1}}
OUTCOMES = set(XP['run'])
SOURCES = {'code', 'cowork', 'chat', 'design'}
STATUSES = {'ok', 'watch', 'broken', 'duplicate', 'retired'}
RTL = re.compile('[\u0590-\u08ff\ufb1d-\ufdff\ufe70-\ufeff]')


def die(msg):
    sys.exit(f'build_world: {msg}')


def parse_ts(s, tz):
    if not s:
        return None
    s = s.strip().replace('Z', '+00:00')
    if len(s) == 10:
        s += 'T12:00:00'
    t = dt.datetime.fromisoformat(s)
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(tz) if tz else t


def script_of(text):
    if RTL.search(text or ''):
        return 'rtl'
    if re.search('[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]', text or ''):
        return 'cjk'
    if re.search('[\u0400-\u04ff]', text or ''):
        return 'cyr'
    return 'latin'


def auto_group(title, counts):
    first = re.split(r'[\s:\-–—_/]+', (title or '').strip())[0] if title else ''
    return first if first and counts[first.lower()] >= 2 else 'other'


def card_code(card):
    # same encoding as myCode() in the world page: CC1.<base64url JSON>.<fnv1a base 36>
    import base64
    b = base64.urlsafe_b64encode(json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode()).decode().rstrip('=')
    h = 0x811c9dc5
    for ch in b:
        h = ((h ^ ord(ch)) * 16777619) & 0xffffffff
    digits, out = '0123456789abcdefghijklmnopqrstuvwxyz', ''
    while True:
        h, r = divmod(h, 36)
        out = digits[r] + out
        if not h:
            return f'CC1.{b}.{out}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('activity')
    ap.add_argument('-o', '--out', default='world.html')
    ap.add_argument('--redact', action='store_true', help='hide chat titles, chat links and task notes')
    ap.add_argument('--tz', help='IANA time zone for day boundaries, e.g. Europe/London')
    ap.add_argument('--items', action='append', default=[], help='items code from claycay.com (CI1....); repeat for more')
    a = ap.parse_args()

    raw = json.load(open(a.activity, encoding='utf-8'))
    tzname = a.tz or raw.get('tz')
    tz = ZoneInfo(tzname) if (tzname and ZoneInfo) else dt.timezone.utc

    # ---- normalise every dated item
    items = []  # (when, kind, payload)
    chats, arts, sessions, runs = [], [], [], []
    for i, c in enumerate(raw.get('chats', [])):
        t = parse_ts(c.get('updated_at') or c.get('date'), tz)
        if not t or not c.get('title'):
            continue
        chats.append({'id': f'c{i}', 'when': t, 't': c['title'], 'url': c.get('url'), 'note': c.get('note', ''),
                      'script': script_of(c['title'])})
    gcount = Counter(re.split(r'[\s:\-–—_/]+', x.get('title', '').strip())[0].lower() for x in raw.get('artifacts', []))
    for i, x in enumerate(raw.get('artifacts', [])):
        t = parse_ts(x.get('updated_at') or x.get('date'), tz)
        src = (x.get('source') or 'code').lower()
        if not t or not x.get('title'):
            continue
        if src not in SOURCES:
            src = 'code'
        arts.append({'id': f'a{i}', 'when': t, 't': x['title'], 'src': src, 'url': x.get('url'), 'note': x.get('note', ''),
                     'group': x.get('group') or auto_group(x['title'], gcount)})
    for i, s in enumerate(raw.get('code_sessions', [])):
        t = parse_ts(s.get('started_at'), tz)
        if not t:
            continue
        proj = s.get('project') or 'a project'
        sessions.append({'id': f's{i}', 'when': t, 't': s.get('title') or f'Session in {proj}', 'group': proj,
                         'note': s.get('note', '')})
    tasks = []
    for tk in raw.get('tasks', []):
        st = (tk.get('status') or 'ok').lower()
        tasks.append({'id': str(tk['id']), 'name': tk.get('name') or tk['id'], 'schedule': tk.get('schedule', ''),
                      'status': st if st in STATUSES else 'ok', 'note': '' if a.redact else tk.get('note', '')})
    task_ids = {t['id'] for t in tasks}
    for r in raw.get('runs', []):
        t = parse_ts(r.get('started_at'), tz)
        o = (r.get('outcome') or '').lower()
        if not t or o not in OUTCOMES:
            continue
        if r.get('task') not in task_ids:
            tasks.append({'id': str(r['task']), 'name': str(r['task']), 'schedule': '', 'status': 'ok', 'note': ''})
            task_ids.add(str(r['task']))
        runs.append({'when': t, 'task': str(r['task']), 'o': o})

    dated = [x['when'] for x in chats + arts + sessions + runs]
    if not dated and not raw.get('projects'):
        die('nothing to draw: no chats, artifacts, sessions, runs or projects found')
    end = max(dated).date() if dated else dt.date.today()
    start = min(dated).date() if dated else end
    if raw.get('start'):
        start = dt.date.fromisoformat(raw['start'])
    if raw.get('end'):
        end = dt.date.fromisoformat(raw['end'])
    ndays = (end - start).days + 1
    if ndays > 400:
        print(f'note: {ndays} days is a long timeline; consider setting "start" to the last 6-12 months', file=sys.stderr)

    def dh(t):
        return (t.date() - start).days, round(t.hour + t.minute / 60, 2)

    # ---- achievements: each records the moment it was earned
    ach = {}

    def earn(key, name, icon, desc, when):
        if key not in ach and when is not None:
            ach[key] = {'id': key, 'name': name, 'icon': icon, 'desc': desc, 'when': when}

    ALL = [('chat', c['when'], c) for c in chats] + [('art', x['when'], x) for x in arts] + \
          [('session', s['when'], s) for s in sessions] + [('run', r['when'], r) for r in runs]
    ALL.sort(key=lambda e: e[1])
    surfaces_seen, scripts_seen, days_active, weekdays = {}, {}, set(), {}
    code_n = 0
    recent_ships = []
    task_runs, task_blocked, task_state = Counter(), Counter(), defaultdict(lambda: [False, 0])
    for kind, when, x in ALL:
        d = when.date()
        days_active.add(d)
        weekdays.setdefault(d.weekday(), when)
        if kind == 'chat':
            earn('first_chat', 'First Words', '💬', 'Started your first chat on the map.', when)
            scripts_seen.setdefault(x['script'], when)
            if len(scripts_seen) >= 2:
                earn('polyglot', 'Polyglot', '🌍', 'Chatted in more than one writing system.', when)
            surfaces_seen.setdefault('chat', when)
        elif kind == 'art':
            earn('first_ship', 'Shipwright', '⚓', 'Made your first artifact.', when)
            surfaces_seen.setdefault(x['src'] if x['src'] != 'design' else 'code', when)
            if x['src'] in ('code', 'design'):
                code_n += 1
                if code_n >= 10:
                    earn('forge10', 'Forge Fire', '🔥', 'Built ten things in Claude Code.', when)
            recent_ships = [w for w in recent_ships if (when - w).total_seconds() <= 600] + [when]
            if len(recent_ships) >= 5:
                earn('assembly', 'Assembly Line', '🏭', 'Five artifacts inside ten minutes.', when)
        elif kind == 'session':
            surfaces_seen.setdefault('code', when)
        elif kind == 'run':
            surfaces_seen.setdefault('scheduled', when)
            tid = x['task']
            task_runs[tid] += 1
            if sum(task_runs.values()) >= 100:
                earn('century', 'Centurion', '💯', 'A hundred scheduled runs logged.', when)
            if task_runs[tid] >= 20:
                earn('clockwork', 'Clockwork', '⏰', 'One scheduled task ran twenty times.', when)
            if x['o'] == 'blocked':
                task_blocked[tid] += 1
                if task_blocked[tid] >= 10:
                    earn('stubborn', 'Stubborn', '🧱', 'A task got blocked ten times and kept showing up.', when)
            st = task_state[tid]
            if x['o'] in ('blocked', 'error', 'unverified'):
                st[0], st[1] = True, 0
            else:
                st[1] += 1
                if st[0] and st[1] >= 3:
                    earn('comeback', 'Comeback Kid', '🔁', 'Three clean runs in a row after a failure.', when)
        h = when.hour
        if kind != 'run' and 0 <= h < 4:  # scheduled runs don't count: the person has to be awake
            earn('night_owl', 'Night Owl', '🦉', 'Did something with Claude between midnight and 4am.', when)
        if kind != 'run' and 4 <= h < 6:
            earn('early_bird', 'Early Bird', '🐦', 'Got going before 6am.', when)
        if len(surfaces_seen) >= 3:
            earn('hopper', 'Island Hopper', '🏝️', 'Used three different Claude surfaces.', when)
        if len(weekdays) == 7:
            earn('every_day', 'Seven-Day Week', '🗓️', 'Active on every day of the week at least once.', when)
        # streak
        streak, k = 1, d
        while k - dt.timedelta(days=1) in days_active:
            streak += 1
            k -= dt.timedelta(days=1)
        if streak >= 7:
            earn('streak7', 'On a Roll', '📅', 'Seven days in a row with Claude.', when)
        if streak >= 30:
            earn('streak30', 'Habit Formed', '🏅', 'Thirty days in a row with Claude.', when)
    first_when = ALL[0][1] if ALL else dt.datetime.combine(start, dt.time(12), tz)
    if len(raw.get('projects', [])) >= 10:
        earn('archipelago', 'Archipelago', '🗺️', 'Ten or more projects.', first_when)
    if any(t['status'] == 'duplicate' for t in tasks):
        earn('haunted', 'Haunted', '👻', 'Has a duplicate task that keeps running.', first_when)
    if sum(t['status'] == 'retired' for t in tasks) >= 5:
        earn('gravedigger', 'Gravedigger', '🪦', 'Retired five scheduled tasks.', first_when)

    CATALOG = [('first_chat', 'First Words', '💬', 'Start a chat.'), ('polyglot', 'Polyglot', '🌍', 'Chat in two writing systems.'),
               ('first_ship', 'Shipwright', '⚓', 'Make an artifact.'), ('forge10', 'Forge Fire', '🔥', 'Build ten things in Claude Code.'),
               ('assembly', 'Assembly Line', '🏭', 'Five artifacts inside ten minutes.'), ('night_owl', 'Night Owl', '🦉', 'Work between midnight and 4am.'),
               ('early_bird', 'Early Bird', '🐦', 'Start before 6am.'), ('streak7', 'On a Roll', '📅', 'Seven days in a row.'),
               ('streak30', 'Habit Formed', '🏅', 'Thirty days in a row.'), ('every_day', 'Seven-Day Week', '🗓️', 'Be active on every weekday.'),
               ('hopper', 'Island Hopper', '🏝️', 'Use three Claude surfaces.'), ('clockwork', 'Clockwork', '⏰', 'One scheduled task runs twenty times.'),
               ('century', 'Centurion', '💯', 'A hundred scheduled runs.'), ('stubborn', 'Stubborn', '🧱', 'A task blocked ten times that keeps going.'),
               ('comeback', 'Comeback Kid', '🔁', 'Three clean runs after a failure.'), ('archipelago', 'Archipelago', '🗺️', 'Ten projects.'),
               ('gravedigger', 'Gravedigger', '🪦', 'Retire five scheduled tasks.')]
    achievements, locked = [], []
    for key, name, icon, hint in CATALOG:
        if key in ach:
            d, h = dh(ach[key]['when'])
            achievements.append({'id': key, 'name': name, 'icon': icon, 'desc': ach[key]['desc'], 'd': max(0, d), 'h': h})
        else:
            locked.append({'id': key, 'name': name, 'icon': icon, 'desc': hint})
    if 'haunted' in ach:
        d, h = dh(ach['haunted']['when'])
        achievements.append({'id': 'haunted', 'name': 'Haunted', 'icon': '👻', 'desc': ach['haunted']['desc'], 'd': max(0, d), 'h': h})
    achievements.sort(key=lambda x: (x['d'], x['h']))

    # ---- quests: the ones written for this person first, then the coach's (see coach.py)
    quests = []
    for q in raw.get('quests', [])[:5]:
        q = q if isinstance(q, dict) else {'text': str(q)}
        if q.get('text'):
            quests.append({'kind': q.get('kind') if q.get('kind') in ('todo', 'tune') else 'todo', 'text': q['text'],
                           'why': q.get('why', ''), 'how': q.get('how', '')})
    coached, coach_met = coach.coach_quests(raw, chats, arts, sessions, tasks, runs, redact=a.redact)
    quests += coached

    # ---- page payload
    def pack_art(x):
        d, h = dh(x['when'])
        return {'id': x['id'], 't': x['t'], 'd': d, 'h': h, 'src': x['src'], 'group': x['group'], 'url': x['url'], 'note': x['note']}

    W = {
        'key': hashlib.sha1((raw.get('owner', '') + str(start)).encode()).hexdigest()[:10],
        'owner': raw.get('owner') or 'You', 'start': start.isoformat(), 'days': ndays, 'xp': XP,
        'tasks': tasks,
        'runs': [[*dh(r['when']), r['task'], r['o']] for r in runs],
        'artifacts': [pack_art(x) for x in arts],
        'chats': [{'id': c['id'], 't': (f'A chat from {c["when"].strftime("%d %b")}' if a.redact else c['t']),
                   'd': dh(c['when'])[0], 'h': dh(c['when'])[1], 'rtl': c['script'] == 'rtl' and not a.redact,
                   'url': None if a.redact else c['url'], 'note': '' if a.redact else c['note']} for c in chats],
        'sessions': [{'id': s['id'], 't': s['t'], 'group': s['group'], 'd': dh(s['when'])[0], 'h': dh(s['when'])[1], 'note': s['note']} for s in sessions],
        'projects': [{'name': p['name'] if isinstance(p, dict) else str(p), 'note': (p.get('note') if isinstance(p, dict) else '') or '',
                      'retired': bool(p.get('retired')) if isinstance(p, dict) else False} for p in raw.get('projects', [])],
        'achievements': achievements, 'locked': locked, 'quests': quests, 'coachMet': coach_met, 'quips': raw.get('quips', {}),
    }
    # ---- shop items: looks only, never XP, so they stay out of the score card
    W['items'], _, item_notes = shop.unlock(a.items)
    W['skill'] = version.VERSION

    # ---- chapters: use the ones written for this person, else sensible defaults
    ch = raw.get('chapters')
    if not ch:
        ch = [{'focus': 'world', 'title': 'Your Claycay',
               'text': f'Everything you did with Claude from {start:%d %B} to {end:%d %B %Y}, grown into islands. Press play to run the days and watch your XP climb, or tap anything to open it.'}]
        if runs:
            ch.append({'focus': 'tasks', 'title': 'Scheduled tasks', 'text': f'{len(tasks)} scheduled tasks ran {len(runs)} times. Gold blocks fly to the lighthouse when a run delivers; the rest complain out loud.'})
            ch.append({'focus': 'bank', 'title': 'The Counting House', 'text': 'Your value ledger: gold for runs that paid off, chimney smoke for the ones that came back quiet. Tap it to see which task earns its keep.'})
        if [x for x in arts if x['src'] in ('code', 'design')] or sessions:
            ch.append({'focus': 'forge', 'title': 'The Forge', 'text': f'{sum(x["src"] in ("code","design") for x in arts)} things built in Claude Code, newest closest to the fire.'})
        if [x for x in arts if x['src'] == 'cowork']:
            ch.append({'focus': 'workshop', 'title': 'Cowork Workshop', 'text': f'{sum(x["src"]=="cowork" for x in arts)} things built in Cowork.'})
        if chats:
            ch.append({'focus': 'village', 'title': 'Chat Village', 'text': f'{len(chats)} chats, one house each, newest closest to the well.'})
        if raw.get('projects'):
            ch.append({'focus': 'projects', 'title': 'Project Archipelago', 'text': f'{len(raw["projects"])} projects, one island each.'})
        nxt = next((q for q in coached if q['kind'] == 'discover'), coached[0] if coached else None)
        if nxt:
            ghost = nxt.get('island')
            ch.append({'focus': f'g:{ghost}' if ghost else 'world', 'title': 'What’s next',
                       'text': f'{nxt["why"]} {"Tap the ghost island to see how." if ghost else "Open 🏆 to see how."}'})
        ch.append({'focus': 'world', 'title': 'Your score', 'text': 'Open the trophy room to see your achievements and quests. Some quests come from your own data, and the ones you finish tick themselves off next time you rebuild.'})
    W['chapters'] = ch

    # ---- score card for competing with other players: counts only, no titles or links
    month_xp = Counter()
    first_month = (min(dated).strftime('%Y-%m') if dated else start.strftime('%Y-%m'))
    month_xp[first_month] += len(W['projects']) * XP['project']
    for c in chats: month_xp[c['when'].strftime('%Y-%m')] += XP['chat']
    for x in arts: month_xp[x['when'].strftime('%Y-%m')] += XP['artifact']
    for x in sessions: month_xp[x['when'].strftime('%Y-%m')] += XP['session']
    for r in runs: month_xp[r['when'].strftime('%Y-%m')] += XP['run'][r['o']]
    for key in ach: month_xp[ach[key]['when'].strftime('%Y-%m')] += XP['achievement'] if key in {x['id'] for x in achievements} else 0
    longest, run_len, prev = 0, 0, None
    for d in sorted(days_active):
        run_len = run_len + 1 if prev and (d - prev).days == 1 else 1
        longest, prev = max(longest, run_len), d
    oc = Counter(r['o'] for r in runs)
    W['card'] = {'v': 1, 'n': W['owner'], 's': start.isoformat(), 'e': end.isoformat(), 'st': longest,
                 'a': [x['id'] for x in achievements],
                 'k': {'chats': len(chats), 'arts': len(arts), 'code': sum(x['src'] in ('code', 'design') for x in arts),
                       'cowork': sum(x['src'] == 'cowork' for x in arts), 'sess': len(sessions), 'runs': len(runs),
                       'del': oc['delivered'], 'nud': oc['nudged'], 'nn': oc['nothing_new'],
                       'fail': oc['blocked'] + oc['error'] + oc['unverified'], 'proj': len(W['projects'])},
                 'm': dict(sorted(month_xp.items()))}

    total = len(W['projects']) * XP['project'] + len(chats) * XP['chat'] + len(arts) * XP['artifact'] + len(sessions) * XP['session'] \
        + sum(XP['run'][r['o']] for r in runs) + len(achievements) * XP['achievement']
    lvl = 1
    while 25 * (lvl + 1) * lvl <= total:
        lvl += 1

    html = open(TEMPLATE, encoding='utf-8').read()
    title = raw.get('title') or f'{W["owner"]}’s Claycay'
    html = html.replace('__TITLE__', title.replace('<', '&lt;')).replace('__WORLD__', json.dumps(W, ensure_ascii=False).replace('</', '<\\/'))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(html)
    print(json.dumps({'out': a.out, 'days': ndays, 'chats': len(chats), 'artifacts': len(arts), 'sessions': len(sessions),
                      'tasks': len(tasks), 'runs': len(runs), 'projects': len(W['projects']), 'xp': total, 'level': lvl,
                      'achievements': [x['name'] for x in achievements], 'locked': [x['name'] for x in locked],
                      'quests': len(quests), 'coach': [q['text'] for q in coached], 'card': card_code(W['card']), 'items': [shop.CATALOG[i] for i in W['items']], 'item_notes': item_notes, 'skill': version.VERSION, 'update': version.update_note(),
                      'bytes': len(html)}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
