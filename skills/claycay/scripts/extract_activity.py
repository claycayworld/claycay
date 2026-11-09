#!/usr/bin/env python3
"""Get the activity.json back out of a world page, to update it later.

  python3 scripts/extract_activity.py claycay.html -o activity.json

build_world.py tucks the activity into every page it builds (except --redact ones, which
may be shared), so an update can start from the published world: read it, extract, gather
each source since its own last date, merge, rebuild. Prints JSON: the time zone the world
was built with, `last` (the newest date per source, or null for a source never gathered,
which means gather it in full), and the shop item codes it carries.
"""
import argparse, json, re, sys


def read_state(path):
    """The state block of a world page, or None (redacted, or built before skill 1.11)."""
    html = open(path, encoding='utf-8').read()
    m = re.search(r'<script type="application/json" id="claycay-activity">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('world', help='a world HTML file built by build_world.py')
    ap.add_argument('-o', '--out', default='activity.json')
    a = ap.parse_args()
    state = read_state(a.world)
    if not state:
        sys.exit('No activity inside this world. It was built with --redact or by a skill older than 1.11, '
                 'so gather everything again for this update.')
    act = state['activity']
    json.dump(act, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def newest(key):
        if key not in act:
            return None   # never gathered: gather it in full this time
        ds = [x.get(k) for x in act[key] for k in ('updated_at', 'date', 'started_at') if x.get(k)]
        return max(ds)[:10] if ds else 'none found'
    last = {key: newest(key) for key in ('chats', 'artifacts', 'code_sessions', 'runs')}
    last['projects'] = 'listed' if 'projects' in act else None
    print(json.dumps({'out': a.out, 'tz': state.get('tz'), 'built_with': state.get('skill'), 'start': act.get('start'),
                      'last': last, 'item_codes': len(act.get('item_codes', []))}, indent=1))


if __name__ == '__main__':
    main()
