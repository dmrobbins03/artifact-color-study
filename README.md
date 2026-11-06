# Color Study Tool

Backup of the Color Study Tool folder: the color swatch study kit and the TLI (transformativeleaders.us) light-palette study built with it.

- `templates/` — the kit: `swatch_kit.py` (generator), `swatch-template.html`, `check.js` and `themes.js` (browser checks), `swatch-refs.json` (Wada combinations, community palettes, color names).
- `claude/` — study settings and Figma state (`tli-swatch-settings.json`, `tli-swatch-state.json`).
- `tli-light-palettes.html` — the built study; `tli-light-palettes-mood-review.txt` — its mood review sheet.

Rebuild (from a working folder): copy `templates/swatch_kit.py`, `templates/swatch-template.html` (as `template.html`), `templates/check.js` and `claude/tli-swatch-settings.json` into it with `templates/swatch-refs.json` saved as `refs.json`, then `python3 swatch_kit.py tli-swatch-settings.json template.html tli-light-palettes.html` and `node check.js tli-light-palettes.html` (needs Playwright).

Files with spaces in their names (`swatch kit.py`, `check.js.js`, `swatch refs.js`, `tile swatch settings.json`…) are older misnamed copies from a download; the hyphen/underscore names are current.
