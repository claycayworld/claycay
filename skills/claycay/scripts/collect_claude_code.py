#!/usr/bin/env python3
"""Collect Claude Code session history from this machine (Claude Code / terminal only).

Claude Code keeps one JSONL transcript per session under ~/.claude/projects/<encoded-path>/.
This reads only timestamps and the working directory of each session, never message
content, and prints a JSON list ready to paste into activity.json as "code_sessions".

Usage:  python collect_claude_code.py [--root ~/.claude/projects] [--since 2026-01-01] > sessions.json
"""
import argparse, glob, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.expanduser('~/.claude/projects'))
    ap.add_argument('--since', default='')
    a = ap.parse_args()
    if not os.path.isdir(a.root):
        sys.exit(f'No Claude Code history at {a.root}. This only works where Claude Code runs.')
    out = []
    for path in glob.glob(os.path.join(a.root, '*', '*.jsonl')):
        first, cwd, turns = None, None, 0
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    ts = rec.get('timestamp')
                    if ts and not first:
                        first = ts
                    cwd = cwd or rec.get('cwd')
                    if rec.get('type') in ('user', 'assistant'):
                        turns += 1
        except OSError:
            continue
        if not first or turns < 2 or first[:10] < a.since:
            continue
        proj = os.path.basename((cwd or '').rstrip('/')) or os.path.basename(os.path.dirname(path))
        out.append({'project': proj, 'started_at': first, 'title': f'{proj}: {turns} turns'})
    out.sort(key=lambda s: s['started_at'])
    json.dump(out, sys.stdout, indent=1)
    print(f'\n{len(out)} sessions', file=sys.stderr)


if __name__ == '__main__':
    main()
