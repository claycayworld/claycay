#!/usr/bin/env python3
"""Ask claycay.com where a score card stands on the public leaderboard.

  python scripts/rank.py CC1.xxxx.yyy          # a card code
  python scripts/rank.py claycay.html          # or a built world (reads its card)
  python scripts/rank.py --top 10              # just the top of the board

Sends the card only (counts, achievement ids, display name; never titles or links).
The lookup stores nothing and doesn't post the card: posting is done on claycay.com.
Prints JSON: players, top [{rank,name,level,xp}], you {xp, level, rank, month}, skill
{latest, url}, and update (one line, only when a newer skill is out).
"""
import argparse, json, os, re, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import version
API = os.environ.get('CLAYCAY_API', 'https://claycay.com/api/rank')


def card_from(arg):
    if re.match(r'^C[CW]1\.', arg.strip()):
        return re.sub(r'\s+', '', arg)
    html = open(arg, encoding='utf-8').read()
    m = re.search(r'"card":\s*(\{.*?"m":\s*\{[^}]*\}\})', html)
    if not m:
        sys.exit(f'No score card found in {arg}. Rebuild the world, or pass the CC1. code.')
    from build_world import card_code
    return card_code(json.loads(m.group(1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('card', nargs='?', help='CC1. score card, or a world HTML file built by build_world.py')
    ap.add_argument('--top', type=int, default=10, help='how many top players to list (0 to 50)')
    a = ap.parse_args()
    body = {'top': a.top, 'skill': version.VERSION}
    if a.card:
        body['card'] = card_from(a.card)
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method='POST',
                                 headers={'Content-Type': 'application/json', 'User-Agent': f'claycay-skill/{version.VERSION}'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get('error')
        except Exception:
            msg = None
        sys.exit(msg or f'claycay.com answered {e.code}.')
    except (urllib.error.URLError, TimeoutError) as e:
        sys.exit(f'Could not reach claycay.com ({getattr(e, "reason", e)}). This sandbox may block it; '
                 'the leaderboard is also at https://claycay.com/#leaderboard')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
