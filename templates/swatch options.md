Swatch study: standard options

David's format for color swatch studies (reused across projects via his color-swatch-study skill, which holds the full rules). Live examples: https://claude.ai/artifact/J79cVDhAabrksZCVZFWWjB (NSI dark palettes), https://claude.ai/artifact/FHLCgkWTUfCnL5ijfhbxKU (TLI light palettes, six section backgrounds each).

Kit (2026-11-05)

The skill embeds these files and extracts them with one command; these copies are the fallback.

templates/swatch_kit.py: the generator. python3 swatch_kit.py settings.json swatch-template.html out.html builds the page from a small settings file and prints a short report (contrast, near-miss hues, ΔE from avoid colors, section steps). Handles dark and light studies, section stacks and complements ("auto" is a first draft only). Reproduces the TLI page byte-for-byte and the skill's dark generator exactly.
templates/check.js: node check.js out.html [--shot s.png N] prints pass/fail for page errors, click speed (median under 25 ms; the old container-query layout measures 30+), every interaction, copy behavior and chip fit at 1280/700/380 px.
templates/figma_fingerprint.js + templates/figma_state.py: Figma freshness check. The fingerprint script (run read-only through use_figma) returns the frame's colors and a hash; figma_state.py compares it with the saved baseline and lists added/removed colors.
templates/swatch-template.html: the page template.
Superseded: build_palette_swatches.py and fill.py (kept until NSI's dark palettes move to a settings file).
Project settings and state
claude/tli-swatch-settings.json: TLI light palettes (six sections each).
claude/tli-swatch-state.json: Figma baseline for frame 4:992 (26 colors, hash a9248bc2, checked 2026-11-05), artifact link, last palette update.
New Statecraft parameters
Logo colors: blue
#135389 (primary; cards, borders and lighter overlays lean toward its 207° hue), red
#E61C2C (buttons), purple
#742376.
Shortlist: Old Glory (
#0A3161) and Federal navy at a quarter step lighter (
#182E56).
Note: the TLI Figma frame itself currently uses navy
#041E4A /
#062B66 and red
#C4262E, not
#182E56 and the logo red.
Page structure
Brand colors group.
Per palette: Footer, Section background, Card third/half/full step, Accent on paper, Light panel, Logo red (dark studies); or six section backgrounds, three card steps, ink, accent, CTA (light studies). Text colors live in each swatch.
Dark studies: two live pairings per palette. Light studies: one stacked preview of the section backgrounds in page order.
Swatch card
1:1 preview, three per row (two below 900px, one below 560px). Contrast ratio and grade sit below the preview next to the name, measured between the current text and current background.
Stage top-left: reset icon, shown only while the preview differs from the recommendation (border, overlay or text).
Stage top-right, above the preview box: "Border options" label + 6 square border chips (¼ step from fill, Base, +½, +1, +2 bold, +3 bold).
Stage bottom-right, below the preview box: "Text options" label + 4 square text chips.
Inside the preview box: 12 square overlay chips top-left with one 1px outline around the whole strip in the current border color; "Aa" / "Small text" bottom-left, and a second copy bottom-right only while an overlay is previewed.
Every swatch gets all three option sets (border, overlay, text), not filtered by usage.
Below the details: Selected colors (Background, Border, Text, with Copy), then Border, Overlay and Text options accordions. Chips and rows only preview; Copy buttons only copy. Accordions never auto-open.
