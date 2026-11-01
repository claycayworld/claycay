"""Claycay shop items: check a signed items code and return the item ids it unlocks.

A code looks like CI1.<base64url JSON>.<base64url signature>. claycay.com signs it with a
private key when someone buys an item; this file holds only the matching public key, so it
can check codes but never make them. Items are looks only and never change XP.

The check is pure Python (ECDSA P-256 with SHA-256) so it runs anywhere without installs.
Someone could edit this file to skip the check, but that only changes their own copy of
their own world: the leaderboard reads owned items from the server, never from a world.
"""
import base64, hashlib, json

# public key of the claycay.com item signer (P-256 point)
ITEM_KEY = (0x8a61437234c73aebaca93c968b046b35bc5ebda6d314d861d02b6e9fdd40e3f4,
            0xcf820fb47102ae38c39824ebdfe906b0cc8ea0cc742a3a5a9ccee9668d11dcfa)

# items this version of the skill knows how to draw
CATALOG = {
    'snowcap': 'Snowcap Isles',
}
# items sold on the site that a newer skill draws
LATER = {'captain': 'Clay Captain', 'ember_forge': 'Ember Forge', 'lantern': 'Lantern Lighthouse',
         'desert': 'Desert Atoll', 'fireworks': 'Level-up Fireworks'}

P = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
A = P - 3
N = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
G = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
     0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)


def _add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    if p[0] == q[0] and (p[1] + q[1]) % P == 0:
        return None
    if p == q:
        m = (3 * p[0] * p[0] + A) * pow(2 * p[1], -1, P) % P
    else:
        m = (q[1] - p[1]) * pow(q[0] - p[0], -1, P) % P
    x = (m * m - p[0] - q[0]) % P
    return x, (m * (p[0] - x) - p[1]) % P


def _mul(k, p):
    r = None
    while k:
        if k & 1:
            r = _add(r, p)
        p = _add(p, p)
        k >>= 1
    return r


def _verify(msg, sig, key=ITEM_KEY):
    if len(sig) != 64:
        return False
    r, s = int.from_bytes(sig[:32], 'big'), int.from_bytes(sig[32:], 'big')
    if not (0 < r < N and 0 < s < N):
        return False
    e = int.from_bytes(hashlib.sha256(msg).digest(), 'big')
    w = pow(s, -1, N)
    pt = _add(_mul(e * w % N, G), _mul(r * w % N, key))
    return pt is not None and pt[0] % N == r


def _b64(s):
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def read_code(code):
    """Return the payload dict of a valid code, or None."""
    parts = (code or '').strip().split('.')
    if len(parts) != 3 or parts[0] != 'CI1':
        return None
    try:
        if not _verify(f'{parts[0]}.{parts[1]}'.encode(), _b64(parts[2])):
            return None
        payload = json.loads(_b64(parts[1]))
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict) or not payload.get('u') or not isinstance(payload.get('i'), list):
        return None
    return payload


def unlock(codes):
    """Check codes (all must belong to one account). Returns (item ids, uid, notes for the person)."""
    items, uid, notes = [], None, []
    for code in codes:
        p = read_code(code)
        if not p:
            notes.append('an items code didn’t check out (a typo, or not from claycay.com), so it was skipped')
            continue
        if uid and p['u'] != uid:
            notes.append('an items code belongs to a different Claycay account, so it was skipped')
            continue
        uid = p['u']
        for i in p['i']:
            if i in CATALOG and i not in items:
                items.append(i)
            elif i not in CATALOG:
                notes.append(f'“{LATER.get(i, i)}” needs a newer Claycay skill; download it again from claycay.com')
    return items, uid, notes
