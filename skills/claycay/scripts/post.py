#!/usr/bin/env python3
"""Post a world's score card to the claycay.com leaderboard with a post key.

  python scripts/post.py claycay.html --key cck_xxx      # or set CLAYCAY_POST_KEY
  python scripts/post.py CC1.xxxx.yyy --key cck_xxx

The person gets the key on claycay.com (Join section, signed in). It can only post their
own card, the same counts-only card they could paste on the site, and a new key turns the
old one off. Prints JSON: posted, rank, before {rank, xp, level}, level, xp, honest.
Exits 1 when the board refuses the card, 2 when claycay.com can't be reached (sandboxes
often block it; then tell the person to paste the card on the site instead).
"""
import argparse, json, os, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import version
from rank import card_from
API = os.environ.get('CLAYCAY_POST_API', 'https://claycay.com/api/post')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('card', help='a world HTML file built by build_world.py, or a CC1. score card')
    ap.add_argument('--key', default=os.environ.get('CLAYCAY_POST_KEY'), help='post key from claycay.com')
    a = ap.parse_args()
    if not a.key:
        sys.exit('No post key. The person gets one on claycay.com (sign in, Join section, “Get my post key”).')
    body = json.dumps({'key': a.key.strip(), 'card': card_from(a.card)}).encode()
    req = urllib.request.Request(API, data=body, method='POST',
                                 headers={'Content-Type': 'application/json', 'User-Agent': f'claycay-skill/{version.VERSION}'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get('error')
        except Exception:
            msg = None
        print(json.dumps({'posted': False, 'status': e.code, 'error': msg or f'claycay.com said {e.code}'}, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'posted': False, 'error': f'Could not reach claycay.com ({e.__class__.__name__}). '
                          'Paste the score card on claycay.com instead.'}))
        sys.exit(2)
    out.pop('ok', None)
    print(json.dumps({'posted': True, **out}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
