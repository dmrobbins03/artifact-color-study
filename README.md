# Color Study Tool

The color swatch study kit (used with the `color-swatch-study` skill) plus the TLI (transformativeleaders.us) light-palette study built with it. This repo is the canonical copy of the kit for every project.

## What's here
- `templates/` — the kit, project-agnostic:
  - `swatch_kit.py` — generator; the settings schema is in its docstring
  - `swatch-template.html` — page template (save as `template.html`)
  - `check.js`, `themes.js` — Playwright checks (interactions, fit, theme switching, reset)
  - `swatch-refs.json` — reference libraries (Wada combinations, community palettes, color names); save as `refs.json` next to the settings
  - `figma_fingerprint.js`, `figma_state.py` — optional Figma freshness check
- `claude/tli-swatch-settings.json` — a complete worked example of a settings file (four light palettes, mood, mood review, card themes)
- `tli-light-palettes.html` — the built TLI study; `tli-light-palettes-mood-review.txt` — its mood review sheet

## Start a study for a new project
1. `git clone https://github.com/dmrobbins03/artifact-color-study` into a working folder.
2. Copy `templates/swatch_kit.py`, `templates/swatch-template.html` (as `template.html`), `templates/check.js`, `templates/themes.js` and `templates/swatch-refs.json` (as `refs.json`) into the folder.
3. Write `<project>-swatch-settings.json` using `claude/tli-swatch-settings.json` as the model: replace `brand`, `paper`, `avoid`, sample copy, `palettes`, section uses, `mood` and `mood_review`; keep the structure.
4. `python3 swatch_kit.py <project>-swatch-settings.json template.html <project>-palettes.html`, read the mood review sheet, then `node check.js <project>-palettes.html` and `node themes.js <project>-palettes.html` (Playwright).
5. Save the project's settings next to its other files (or in this repo under `claude/`); push kit changes back to `templates/`.

Files with spaces in their names (`swatch kit.py`, `check.js.js`, `swatch refs.js`, `tile swatch settings.json`…) are older misnamed copies from a download; the hyphen/underscore names are current.
