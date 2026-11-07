#!/usr/bin/env python3
"""Compare a fresh Figma color fingerprint with the one saved at the last palette update.
  python3 figma_state.py state.json fresh.json          -> prints UNCHANGED or CHANGED with added/removed colors (exit 0/1)
  python3 figma_state.py state.json fresh.json --save   -> also records fresh as the new baseline with today's date
state.json: {"figma": {"file", "node", "hash", "list", "checked"}, "palette_updated", "artifact", "settings"}
fresh.json: the object returned by figma_fingerprint.js"""
import json, sys, datetime
st_path, fr_path = sys.argv[1], sys.argv[2]
st = json.load(open(st_path)); fr = json.load(open(fr_path)); old = st.get('figma', {})
if old.get('hash') == fr['hash']:
    print(f"UNCHANGED: {fr['frame']} has the same {fr['colors']} colors as on {old.get('checked')} (hash {fr['hash']}); no need to resample colors")
    code = 0
else:
    a, b = set(old.get('list', [])), set(fr['list'])
    print(f"CHANGED since {old.get('checked')}: hash {old.get('hash')} → {fr['hash']}")
    if b - a: print("  added:   " + ", ".join(sorted(b - a)))
    if a - b: print("  removed: " + ", ".join(sorted(a - b)))
    if a == b: print("  same colors, different usage counts (colors moved between layers)")
    code = 1
if '--save' in sys.argv:
    st['figma'] = {**old, 'hash': fr['hash'], 'list': fr['list'], 'frame': fr['frame'], 'checked': datetime.date.today().isoformat()}
    json.dump(st, open(st_path, 'w'), ensure_ascii=False, indent=1); print("  baseline saved")
sys.exit(code)
