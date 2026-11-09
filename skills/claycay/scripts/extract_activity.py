#!/usr/bin/env python3
"""Get the activity.json back out of a world page, to update it later.

  python scripts/extract_activity.py claycay.html -o activity.json

build_world.py tucks the activity into every page it builds (except --redact ones, which
may be shared), so an update can start from the published world: read it, extract, gather
only what's new since its `end`, merge, rebuild. Prints the time zone the world was built
with and the activity's last date, as JSON.
"""
import argparse, json, re, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('world', help='a world HTML file built by build_world.py')
    ap.add_argument('-o', '--out', default='activity.json')
    a = ap.parse_args()
    html = open(a.world, encoding='utf-8').read()
    m = re.search(r'<script type="application/json" id="claycay-activity">(.*?)</script>', html, re.S)
    if not m:
        sys.exit('No activity inside this world. It was built with --redact or by a skill older than 1.11, '
                 'so gather everything again for this update.')
    state = json.loads(m.group(1))
    act = state['activity']
    json.dump(act, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    dates = [x.get(k) for key in ('chats', 'artifacts', 'code_sessions', 'runs') for x in act.get(key, [])
             for k in ('updated_at', 'date', 'started_at') if x.get(k)]
    print(json.dumps({'out': a.out, 'tz': state.get('tz'), 'built_with': state.get('skill'),
                      'last_activity': max(dates)[:10] if dates else None, 'end': act.get('end')}, indent=1))


if __name__ == '__main__':
    main()
