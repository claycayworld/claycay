"""The skill's version, and a quick check for a newer one on claycay.com.

Bump VERSION whenever the skill changes, then run scripts/package-skill.sh, which
also publishes it as site/public/skill-version.json for older copies to compare with.
"""
import json, os, urllib.request

VERSION = '1.5'
URL = os.environ.get('CLAYCAY_VERSION_URL', 'https://claycay.com/skill-version.json')


def parts(v):
    return tuple(int(x) for x in str(v).split('.') if x.isdigit())


def latest(timeout=4):
    """Newest published version, or None if claycay.com can't be reached (sandboxes often block it)."""
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': f'claycay-skill/{VERSION}'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return str(json.load(r).get('version') or '') or None
    except Exception:
        return None


def update_note():
    """One plain line if a newer skill is out, else None. Never raises."""
    new = latest()
    if new and parts(new) > parts(VERSION):
        return f'A newer Claycay skill ({new}) is out. You have {VERSION}. Download it again from https://claycay.com'
    return None


if __name__ == '__main__':
    print(json.dumps({'version': VERSION, 'latest': latest(), 'update': update_note()}))
