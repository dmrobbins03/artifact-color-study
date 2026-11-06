#!/usr/bin/env python3
"""Color swatch study generator.  python3 swatch_kit.py settings.json template.html out.html [config.json]
Builds the page from a small settings file and prints a short report (harmony, contrast, distance from reference colors,
any automatic adjustments). The template and color math are the color-swatch-study skill's; don't fork this per project:
put project specifics in the settings file.
 
settings keys
  title, eyebrow, heading, lede, footnote, mode ("dark" | "light")
  brand: [[name, hex, note?, role?]]   first entry is the primary; role "logo" (default) is used for harmony,
                                        role "reference" (e.g. a sibling site's colors) is shown but not used for harmony
  paper: light page color (dark mode: accent backdrop; light mode: brand swatch backdrop)
  avoid: [hex]  light colors this study must stay clearly apart from (sibling site's paper); min ΔE 5
  brand_sub: description for the Brand colors group
  sample: {tag, heading, cards:[{h,p,cta}]}
  dark palettes:  {name, sub, footer, bg, accent, light, red, red_name}
  light palettes: {name, sub, paper, area, band, ink, accent, red, red_name, comp: [3 hex] | "auto", comp_name}
  light palette option: sections [{key, hex, name, use}] (any count, row order; keys starting 'comp' count as complements) and stack (page order,
                  sec = a section key) override the six default sections and the global stack for that palette
  light only: section_uses [3], comp_uses [3], stack: [{sec: paper|area|band|comp1|comp2|comp3, kind: text|cards|cta, h, p}], stack_sub
  light palettes, optional: mood (the palette's character, shown first), tech (color notes), harmony (overrides the computed brand-harmony line),
                  stack_sub (this palette's page-order intro); top-level lede may hold paragraphs separated by a blank line
"""
import json, colorsys, sys, math
 
S = json.load(open(sys.argv[1])); TPL, OUT = sys.argv[2], sys.argv[3]; CFG = sys.argv[4] if len(sys.argv) > 4 else None
MODE = S.get('mode', 'dark'); BRAND = [b + [None] * (4 - len(b)) for b in S['brand']]
LOGOS = [b for b in BRAND if (b[3] or 'logo') == 'logo']
REPORT = []
 
def lum(h):
    c = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]; c = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in c]
    return .2126*c[0] + .7152*c[1] + .0722*c[2]
def ratio(a, b): x, y = lum(a), lum(b); return (max(x, y)+.05)/(min(x, y)+.05)
def hx(h, l, s): return '#%02X%02X%02X' % tuple(round(x*255) for x in colorsys.hls_to_rgb((h % 360)/360, max(0, min(l, 1)), max(0, min(s, 1))))
def hls(c): h, l, s = colorsys.rgb_to_hls(*[int(c[i:i+2], 16)/255 for i in (1, 3, 5)]); return h*360, l, s
def lab(h):
    c = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]; c = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in c]
    X = (c[0]*.4124 + c[1]*.3576 + c[2]*.1805)/.95047; Y = c[0]*.2126 + c[1]*.7152 + c[2]*.0722; Z = (c[0]*.0193 + c[1]*.1192 + c[2]*.9505)/1.08883
    f = lambda t: t**(1/3) if t > .008856 else 7.787*t + 16/116
    return 116*f(Y) - 16, 500*(f(X) - f(Y)), 200*(f(Y) - f(Z))
def dE(a, b): return math.dist(lab(a), lab(b))
def hdist(a, b): return abs(((a - b + 180) % 360) - 180)
 
LOGO = hls(BRAND[0][1])[0]; WARM = hls(BRAND[1][1] if len(BRAND) > 1 else BRAND[0][1])[0]
STEPS = [('third', .02, 1/6), ('half', .035, .25), ('full', .06, .5)]; SATCAP = .60
BOPTS = [('¼ step from fill', .015, .05), ('Base', .07, .15), ('+½ step', .105, .25), ('+1 step', .13, .35), ('+2 steps · bold', .19, .45), ('+3 steps · bold', .25, .55)]
OPTS_OVERLAY = [('−3 steps', -.18, 0), ('−2 steps', -.12, 0), ('−1 step', -.06, 0), ('−½ step', -.035, 0), ('−⅓ step', -.02, 0), ('−¼ step', -.015, 0),
                ('+¼ step', .015, 1/8), ('+⅓ step', .02, 1/6), ('+½ step', .035, .25), ('+1 step', .06, .5), ('+2 steps', .12, .65), ('+3 steps', .18, .8)]
AAA = 7.0  # WCAG AAA for normal text; light studies hold every text color to it, button labels included
SATFLOOR = .12 if MODE == 'light' else 0   # light mode: near-gray fills keep a little saturation so borders don't go dead gray
 
def near(fh): d = ((LOGO - fh + 180) % 360) - 180; return d, abs(d) < 45
def border_opts(fill):
    fh, fl, fs = hls(fill); sign = 1 if fl < .6 else -1; d, n = near(fh)
    return [{"hex": hx(fh + (d*bf if n else 0), fl + sign*dl, min(max(fs, SATFLOOR)*.8, .48)), "label": lb, **({"default": True} if lb == 'Base' else {})} for lb, dl, bf in BOPTS]
def overlay_opts(fill):
    fh, fl, fs = hls(fill); d, n = near(fh)
    return [{"hex": hx(fh + (d*hf if n else 0), max(0, min(.99, fl + dl)), min(fs, SATCAP) if dl > 0 else fs), "label": lb} for lb, dl, hf in OPTS_OVERLAY]
def harmony(c):
    ch, cl, cs = hls(c)
    if cs < .12 or cl > .97: return None
    best = min(((n, hdist(ch, hls(bc)[0])) for n, bc, *_ in LOGOS if hls(bc)[2] >= .12), key=lambda x: x[1], default=None)
    if not best: return None
    n, d = best
    lb = 'same family' if d <= 12 else 'near-miss, may read as a mismatch' if d <= 30 else 'analogous' if d <= 60 else 'complement' if d >= 150 else 'contrast'
    return f"{n} {round(d)}° ({lb})"
def tsearch(h, l, s, fills, minr, step):
    while 0 <= l <= 1:
        c = hx(h, l, s)
        if min(ratio(c, f) for f in fills) >= minr: return c
        l += step
    return '#FFFFFF' if step > 0 else '#000000'
def fit(c, fills, minr):
    # move a chosen color only as far as needed to pass on every fill
    h, l, s = hls(c)
    return c if min(ratio(c, f) for f in fills) >= minr else tsearch(h, l, s, fills, minr, -.01 if lum(fills[0]) > .18 else .01)
def text_opts(fill, also=(), P=None):
    fh, fl, fs = hls(fill); fills = [fill, *also]; mid = fh + (((LOGO - fh + 180) % 360) - 180)/2
    if ratio(fill, '#FFFFFF') >= ratio(fill, '#111111'):
        return [{"hex": tsearch(fh, .95, .40, fills, 7, .01), "label": "Light text"}, {"hex": tsearch(fh, .74, .22, fills, 4.5, .01), "label": "Muted text"},
                {"hex": tsearch(mid, .74, .55, fills, 4.5, .01), "label": "Light accent"}, {"hex": tsearch(WARM, .76, .65, fills, 4.5, .01), "label": "Light red accent"}]
    if MODE == 'light':
        ih = hls(P['ink'])[0] if P else fh
        return [{"hex": fit(P['ink'], fills, 7) if P else tsearch(fh, .14, .35, fills, 7, -.01), "label": "Heading ink"},
                {"hex": tsearch(ih, .42, .18, fills, AAA, -.01), "label": "Muted text"},
                {"hex": fit(P['accent'], fills, AAA) if P else tsearch(LOGO, .34, .6, fills, AAA, -.01), "label": "Accent"},
                {"hex": fit(P['red'], fills, AAA) if P else tsearch(WARM, .40, .7, fills, AAA, -.01), "label": "Red accent"}]
    return [{"hex": tsearch(fh, .14, .35, fills, 7, -.01), "label": "Dark text"}, {"hex": tsearch(fh, .36, .15, fills, 4.5, -.01), "label": "Muted text"},
            {"hex": tsearch(LOGO, .34, .6, fills, 4.5, -.01), "label": "Dark accent"}, {"hex": tsearch(WARM, .40, .7, fills, 4.5, -.01), "label": "Dark red accent"}]
def sw(hexc, name, on, use, texts=None, **kw):
    return {"hex": hexc, "name": name, "on": on, "borders": kw.pop('borders', None) or border_opts(hexc), "overlays": overlay_opts(hexc),
            "texts": texts if texts is not None else text_opts(hexc), "use": use, **kw}
 
AVOID = S.get('avoid', [])
WORDS = dict(enumerate('zero one two three four five six seven eight nine ten'.split()))
def auto_comp(ink, name):
    """three warm/opposite tints ~180° from the ink, stepped light→deep; nudged clear of `avoid` colors (reported)"""
    h0 = (hls(ink)[0] + 180) % 360; out = []
    for k, (l, s) in enumerate([(.92, .71), (.87, .61), (.80, .55)]):
        h = h0; c = hx(h, l, s); tries = 0
        while AVOID and min(dE(c, a) for a in AVOID) < 5 and tries < 12:
            tries += 1; h = h0 - 3*tries; s2 = min(s + .02*tries, .9); c = hx(h, l - .005*tries, s2)
        if tries: REPORT.append(f"  {name}: comp {k+1} nudged {tries}x to stay ΔE≥5 from {', '.join(AVOID)} → {c}")
        out.append(c)
    return out
def check_avoid(name, label, c):
    for a in AVOID:
        d = dE(c, a)
        if d < 5: REPORT.append(f"  ! {name}: {label} {c} only ΔE {d:.1f} from {a}")
def contrast_line(name, TX, fills):
    worst = [(t['label'], min(ratio(t['hex'], f) for f in fills)) for t in TX]
    need = {0: 7}; bad = [f"{l} {r:.2f}" for i, (l, r) in enumerate(worst) if r < need.get(i, 4.5) - 1e-9]
    REPORT.append(f"  {name}: text set {' / '.join(t['hex'] for t in TX)}; worst {min(r for _, r in worst):.2f}:1 over {len(fills)} fills" + (f"  ! below target: {', '.join(bad)}" if bad else ""))
 
HARMONIES = [("Monochromatic", 0), ("Analogous +30°", 30), ("Analogous −30°", -30), ("Complementary", 180), ("Split complementary +150°", 150),
             ("Split complementary −150°", -150), ("Triadic +120°", 120), ("Triadic −120°", -120), ("Tetradic +90°", 90), ("Tetradic −90°", -90)]
def _lin(v): return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
def _gam(v): return 12.92*v if v <= .0031308 else 1.055*v**(1/2.4) - .055
def oklch(h):
    r, g, b = [_lin(int(h[i:i+2], 16)/255) for i in (1, 3, 5)]
    l, m, s = [(x)**(1/3) for x in (.4122214708*r+.5363325363*g+.0514459929*b, .2119034982*r+.6806995451*g+.1073969566*b, .0883024619*r+.2817188376*g+.6299787005*b)]
    L, a, bb = .2104542553*l+.7936177850*m-.0040720468*s, 1.9779984951*l-2.4285922050*m+.4505937099*s, .0259040371*l+.7827717662*m-.8086757660*s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360
def from_oklch(L, C, H):
    """OKLCH → hex, reducing chroma until the color fits in sRGB"""
    while True:
        a, b = C*math.cos(math.radians(H)), C*math.sin(math.radians(H))
        l, m, s = [x**3 for x in (L+.3963377774*a+.2158037573*b, L-.1055613458*a-.0638541728*b, L-.0894841775*a-1.2914855480*b)]
        rgb = (4.0767416621*l-3.3077115913*m+.2309699292*s, -1.2684380046*l+2.6097574011*m-.3413193965*s, -.0041960863*l-.7034186147*m+1.7076147010*s)
        if all(-1e-4 <= v <= 1.0001 for v in rgb) or C <= 0: return '#%02X%02X%02X' % tuple(round(max(0, min(1, _gam(max(0, v))))*255) for v in rgb)
        C -= .002
DEFAULT_THEMES = [   # a pool of card themes by purpose; each section picks six (at least two dark) in its own order, most distinct first
  {"label": "Paper white", "note": "forms, program details, long reading: near-white with a trace of the section color, the border carries the edge",
   "tone": "white", "bg": ["section", "section", 0], "c": .9, "acc": ["ink", "Logo blue", .5]},
  {"label": "Section tonal", "note": "institutional content: the section's own color, one step deeper and greyer", "bg": ["section", "section", 0], "c": .7, "acc": ["accent", "section", .2]},
  {"label": "Civic blue", "cool": True, "note": "program pages: the section color pulled toward the logo blue", "bg": ["section", "Logo blue", .6], "c": 1.9, "acc": ["Logo blue", "ink", .15]},
  {"label": "Fellowship plum", "note": "cohorts, fellows and people: the section color pulled toward the logo purple", "bg": ["section", "Logo purple", .6], "c": 1.6, "acc": ["Logo purple", "Logo purple", 0]},
  {"label": "Capitol stone", "note": "history and institutional content: the section warmed toward limestone with a trace of logo red", "bg": ["section", "Logo red", .3], "shift": 35, "c": .8, "acc": ["ink", "ink", 0]},
  {"label": "Charter rose", "note": "announcements and calls to apply: the section pulled toward the logo red", "bg": ["section", "Logo red", .6], "c": 1.4, "acc": ["Logo red", "ink", .15]},
  {"label": "Slate", "cool": True, "note": "data, quotes and reference panels: the section pulled toward the navy ink and greyed", "bg": ["section", "ink", .6], "c": .5, "acc": ["Logo blue", "ink", .4]},
  {"label": "Harbor blue", "cool": True, "note": "news, updates and events: a clear light blue between the section and the logo blue",
   "bg": ["Logo blue", "section", .35], "c": 1.1, "acc": ["Logo blue", "ink", .3]},
  {"label": "Steel blue", "cool": True, "note": "data, research and scorecards: navy and logo blue, greyed into the section",
   "bg": ["ink", "Logo blue", .5], "s": .5, "c": 1.0, "acc": ["ink", "Logo blue", .4]},
  {"label": "Flag blue", "cool": True, "note": "civic moments, stats and pledges: the deep blue of the flag, tinted by the section",
   "tone": "dark", "bg": ["#0A3161", "section", .1], "acc": ["Logo blue", "Logo blue", 0]},
  {"label": "Federal navy", "cool": True, "note": "featured callouts and quotes: dark navy tinted by the section, the link back to New Statecraft",
   "tone": "dark", "bg": ["ink", "section", .15], "acc": ["Logo blue", "Logo blue", 0]},
  {"label": "Deep tone", "note": "section breaks and calls to apply: the section color taken dark with a touch of logo purple",
   "tone": "dark", "bg": ["section", "Logo purple", .3], "c": 1.3, "acc": ["section", "Logo red", .5]},
  {"label": "Oxblood", "note": "urgent calls to action and deadlines: logo red deepened with navy, tinted by the section",
   "tone": "dark", "bg": ["Logo red", "ink", .5], "s": .25, "shift": 12, "acc": ["Logo red", "section", .4]},   # shift: toward brick, away from wine-pink
  {"label": "Deep plum", "note": "fellow spotlights and testimonials: logo purple deepened with navy, tinted by the section",
   "tone": "dark", "bg": ["Logo purple", "ink", .4], "s": .25, "acc": ["Logo purple", "section", .4]},
  {"label": "Deep blue", "cool": True, "note": "program highlights and stats: logo blue deepened with navy, tinted by the section",
   "tone": "dark", "bg": ["Logo blue", "ink", .4], "s": .25, "acc": ["Logo blue", "section", .4]}]
def nudge(H, sec, amt=.3, cap=15):
    """turn a brand hue a little toward the section's hue (capped) so options stay on brand but belong to their section"""
    sL, sC, sH = oklch(sec)
    if sC < .008: return H
    d = ((sH - H + 180) % 360) - 180
    return (H + max(-cap, min(cap, d*amt))) % 360
def darken_to(c, bgs, minr=AAA, up=False):
    """move a color's OKLCH lightness (keeping hue and chroma) until it reaches minr on every background"""
    L, C, H = oklch(c)
    for i in range(200):
        h = from_oklch(min(max(L, 0), 1), C, H)
        if min(ratio(h, b) for b in bgs) >= minr: return h
        L += .005 if up else -.005
    return '#FFFFFF' if up else '#000000'
def reddish(H): return H < 50 or H > 340   # OKLCH hues where a pale tint reads pink (logo red sits at 25°)
BRASS = 80   # light accents on dark grounds use brass (OKLCH hue 80) in place of red, so dark cards never carry pink
def accent_set(bases, bgs, avoid, dark=False, hues=3, per=3, gap=.09, sec=None):
    """accent options: up to `hues` clearly different colors (paired one first), each in `per` brightness steps `gap` OKLCH L apart,
    every value 7:1 on all of `bgs` and at least ΔE 10 from the text (`avoid`). bases: [(name, C, H)]."""
    out, firsts = [], []
    for nm, C, H in bases:
        if dark and reddish(H): nm, H = "Brass", BRASS   # a pale red on a dark ground reads pink
        C = .07 if dark else max(C, .06); v = []
        for i in range(0, 140):
            off = (.97 - oklch(sec)[0]) if sec else 0   # start follows the section's lightness, so same-hue sections get their own accents
            L = .45 + .005*i + off*.3 if dark else .86 - .005*i - off*.6
            c = from_oklch(L, C, H)
            if min(ratio(c, b) for b in bgs) >= AAA and dE(c, avoid) >= 10 and oklch(c)[1] >= .035: v.append((L, c))   # keep color (no white)
        if not v or any(dE(v[0][1], f) < 15 for f in firsts): continue
        firsts.append(v[0][1]); L0 = v[0][0]; pick = []
        for s in range(per):
            tgt = L0 + gap*.6*s if dark else L0 - gap*s
            c = min(v, key=lambda x: abs(x[0] - tgt))[1]
            if c not in pick: pick.append(c)
        names = (["vivid", "light", "palest"] if dark else ["bright", "mid", "deep"])
        out += [{"hex": c, "label": f"{nm} · {names[s]}"} for s, c in enumerate(pick)]
        if len(firsts) >= hues: break
    return out
def sec_text(sec, P):
    """section text options: brand ink, ink tinted to the section, a muted tone fitted to this section, accent and red, all 7:1"""
    iL, iC, iH = oklch(P['ink']); sH = oklch(sec)[2] if oklch(sec)[1] >= .008 else iH
    if is_dark(sec):   # a dark band in a light study: light text options
        bL, bC, bH = oklch(BRAND[0][1]); rL, rC, rH = oklch(P['red'])
        if reddish(sH): sH = BRASS   # a pale tint of a red band reads pink: warm the pale and muted lights to stone instead
        opts = [("#FFFFFF", "White"), (darken_to(from_oklch(.95, .02, sH), [sec], up=True), "Pale section tint"), (darken_to(from_oklch(.80, .03, sH), [sec], up=True), "Muted light"),
                (darken_to(from_oklch(.80, .08, bH), [sec], up=True), "Light accent"), (darken_to(from_oklch(.80, .07, BRASS), [sec], up=True), "Light brass accent"),
                (darken_to(from_oklch(.86, .035, 80), [sec], up=True), "Pale stone")]   # a warm limestone/parchment counterpoint, so dark bands aren't all pale blue
        out = {}
        for h, l in opts: out[h] = out[h] + " = " + l if h in out else l
        return [{"hex": h, "label": l} for h, l in out.items()]
    opts = [(fit(P['ink'], [sec], AAA), "Heading ink"), (darken_to(from_oklch(iL, max(iC, .05), nudge(iH, sec, .5, 30)), [sec]), "Ink tinted to section"),
            (darken_to(from_oklch(.5, .03, sH), [sec]), "Muted, section hue"), (darken_to(P['accent'], [sec]), "Accent"), (darken_to(P['red'], [sec]), "Red accent")]
    out = {}
    for h, l in opts: out[h] = out[h] + " = " + l if h in out else l
    return [{"hex": h, "label": l} for h, l in out.items()]
def ref(name, sec, P):
    if name.startswith('#'): return name
    return {"section": sec, "ink": P['ink'], "accent": P['accent'], "red": P['red']}.get(name) or next(bc for n, bc, *_ in BRAND if n == name)
def is_dark(c): return ratio(c, '#FFFFFF') > ratio(c, '#111111')
def mix(a, b, t):
    """OKLCH blend of two colors through Lab-style a/b (opposite hues meet in a muted middle, never an off-brand hue); returns (L, C, H)"""
    (L1, C1, H1), (L2, C2, H2) = oklch(a), oklch(b)
    x = (1-t)*C1*math.cos(math.radians(H1)) + t*C2*math.cos(math.radians(H2)); y = (1-t)*C1*math.sin(math.radians(H1)) + t*C2*math.sin(math.radians(H2))
    return L1 + (L2 - L1)*t, math.hypot(x, y), math.degrees(math.atan2(y, x)) % 360
MOOD = S.get('mood', {})   # {words, light_card_max_chroma, dark_card_max_chroma}: the brand's mood, used to generate and to review
MOOD_L, MOOD_C = .80, MOOD.get('light_card_max_chroma', .028)   # mood check: a very light card that is also noticeably colored reads as pastel (baby blue, bubblegum), off-mood for a civic brand
MOODLOG = []
def color_words(c):
    """plain-language name for a color, for the mood review sheet (e.g. 'pale dusty blue')"""
    L, C, H = oklch(c)
    lw = "very pale" if L > .95 else "pale" if L > .88 else "light" if L > .75 else "mid" if L > .55 else "deep" if L > .38 else "dark"
    if C < .012: return f"{lw} neutral grey"
    cw = "greyed" if C < .025 else "dusty" if C < .05 else "clear" if C < .10 else "vivid"
    hw = next(n for lim, n in [(15, "pink-red"), (40, "red"), (60, "terracotta"), (80, "clay/sand"), (105, "wheat/yellow"), (150, "olive/green"),
                               (200, "teal"), (240, "cyan-blue"), (275, "blue"), (300, "indigo"), (330, "purple"), (350, "plum/magenta"), (361, "rose")] if H < lim)
    return f"{lw} {cw} {hw}"
import os
REFS = json.load(open(S.get('refs', 'refs.json'))) if os.path.exists(S.get('refs', 'refs.json')) else None   # built from open palette libraries
if REFS:
    import numpy as np
    _NL = np.array([lab(h) for _, h in REFS['names']]); _NN = [n for n, _ in REFS['names']]
    _PALS = [[(oklch(h)[1], oklch(h)[2], oklch(h)[0]) for h in p] for p in REFS['wada']]   # Wada's curated combinations set the precedent
def hex_name(c):
    """nearest real color name for a hex (Color Name List), so colors are judged by what they are, not by a theme's label"""
    if not REFS: return color_words(c)
    return _NN[int(np.argmin(((_NL - np.array(lab(c)))**2).sum(1)))]
def _m(a, b): return (a[0] < .015 and b[0] < .03) or (a[0] >= .015 and b[0] >= .03 and hdist(a[1], b[1]) <= 20)
def precedent(*cols):
    """True when one library palette (Wada's combinations or the community palettes) holds a distinct match for every color
    (same hue within 20°, or both near-neutral); lightness is ignored because study colors are lightness-fitted variants"""
    if not REFS: return True
    want = [(oklch(c)[1], oklch(c)[2], oklch(c)[0]) for c in cols]; dl = want[1][2] - want[0][2] if len(want) > 1 else 0
    for p in _PALS:
        for i, a in enumerate(p):
            if not _m(want[0], a): continue
            for j, b in enumerate(p):   # the pair must also keep its light/dark relationship (a dark card on a light section needs a dark-on-light pair)
                if j != i and _m(want[1], b) and (abs(dl) < .25 or (b[2] - a[2]) * dl > 0 and abs(b[2] - a[2]) >= .2): return True
    return False
def library_themes(P):
    """up to three card themes sourced from Wada's combinations: partners that Wada pairs with a navy/blue like the brand's,
    kept only when they sit within 35° of a brand hue (so the library guides without replacing the brand)"""
    if not REFS: return []
    bh = [oklch(bc)[2] for n, bc, *_ in BRAND if oklch(bc)[1] >= .03] + [oklch(P['ink'])[2]]
    navy = [oklch(P['ink'])[2], oklch(BRAND[0][1])[2]]; cnt = {}
    for p in REFS['wada']:
        if not any(oklch(h)[1] >= .03 and min(hdist(oklch(h)[2], x) for x in navy) <= 15 and oklch(h)[0] < .6 for h in p): continue
        for h in p:
            L, C, H = oklch(h)
            if C >= .03 and min(hdist(H, x) for x in navy) > 15 and min(hdist(H, x) for x in bh) <= 35: cnt[h] = cnt.get(h, 0) + 1
    out = []
    for h, n in sorted(cnt.items(), key=lambda x: -x[1]):
        if any(dE(h, o['bg'][0]) < 15 for o in out): continue
        dark = oklch(h)[0] < .55
        out.append({"label": "Wada " + color_words(h).split()[-1].split('/')[0].split('-')[-1], "lib": True, "note": f"library pick: Wada pairs {hex_name(h)} ({h}) with navy in {n} combinations; supporting panels and features",
                    "tone": "dark" if dark else "panel", "bg": [h, "section", .25], "acc": (["Logo blue", "Logo blue", 0] if dark else ["ink", "ink", 0])})
        if len(out) == 3: break
    return out
MOOD_RULES = S.get('mood_review', [])   # [{"theme": label, "section": hex or "*", "why": "..."}]: themes judged not to fit, left out of those sections
PAIRLOG = []   # (section, what) for every card background that failed the section/card pairing check
def pair_ok(sec, card, white=False):
    """section + card background read as a deliberate pair: visibly apart (ΔE >= 3, unless a white card whose border carries the edge)
    and not a hue near-miss (both colored and 12–30° apart reads as a mistake rather than a choice)"""
    if not white and dE(sec, card) < 3: return False
    (sL, sC, sH), (cL, cC, cH) = oklch(sec), oklch(card)
    return not (sC >= .012 and cC >= .012 and 12 < hdist(sH, cH) <= 30)
def card_themes(sec, P, TX):
    """Card themes from S['card_themes'] (DEFAULT_THEMES if absent). tone "panel" (default): section chroma times "c", default reads
    as a panel on the section (ΔE 6–10); "white": the lightest values, default the whitest, border carries the edge; "dark": light
    text, default nearest the ink's lightness. Every value keeps the theme's heading and body text at 7:1. Six values, .02 L apart.
    Returns [(label, hue, [bg hexes], default index, recipe, chroma)]."""
    secL, C0, _ = oklch(sec); C = max(.014, min(C0, .035)); out = []
    # the mood is a source as well as a limit: settings mood.themes (recipes drawn from the mood's materials and references) join the pool,
    # take the first pick and get a preference in the most-distinct picks
    BN = {n for n, *_ in BRAND} | {"section", "ink", "accent", "red"}
    def known(R): return all(not isinstance(x, str) or x.startswith('#') or x in BN for x in R['bg'][:2] + R['acc'][:2])
    # dark bands get tonal dark cards (the section's own color a step lighter, nudged toward ink or stone) for the subtle half
    TONAL = [{"label": "Tonal step", "note": "institutional content on a dark band: the section's own color, a step lighter", "tone": "dark", "tonal": True,
              "bg": ["section", "section", 0], "acc": ["accent", "section", .2]},
             {"label": "Tonal deep", "note": "quotes and supporting panels: the section's own color, a step deeper", "tone": "dark", "tonal": True, "lift": "down",
              "bg": ["section", "section", 0], "acc": ["accent", "section", .2]},
             {"label": "Tonal stone", "note": "forms and details on a dark band: the section greyed toward limestone, a step lighter", "tone": "dark", "tonal": True,
              "bg": ["section", "#D9CCB0", .12], "c": .4, "acc": ["accent", "accent", 0]}] if is_dark(sec) else []
    for R in [R for R in S.get('card_themes', DEFAULT_THEMES) + [{**m, "mood": True} for m in MOOD.get('themes', [])] + library_themes(P) + TONAL if known(R)]:   # skip recipes naming a brand color the settings no longer list
        tone = R.get('tone', 'panel'); mL, mC, mH = mix(ref(R['bg'][0], sec, P), ref(R['bg'][1], sec, P), R['bg'][2])
        if R.get('s'): mL, mC, mH = mix(from_oklch(mL, mC, mH), sec, R['s'])
        if mC < .008: mH = oklch(P['ink'])[2]   # near-grey blend: lean on the ink hue rather than an unstable one
        H = (mH + R.get('shift', 0)) % 360
        # hue guard: a blend of near-opposite colors can land on an off-brand hue (wheat + logo blue gave cyan); snap it to the nearest
        # brand / ink / section hue when it is more than 35° from all of them, and report it
        anchors = [oklch(bc)[2] for n, bc, *_ in BRAND if oklch(bc)[1] >= .03] + [oklch(P['ink'])[2]] + ([oklch(sec)[2]] if oklch(sec)[1] >= .012 else []) + \
                  [oklch(r)[2] for r in R['bg'] if isinstance(r, str) and r.startswith('#')]   # a recipe's own material color is an anchor too
        near_h = min(anchors, key=lambda a: hdist(H, a))
        if hdist(H, near_h) > 35 and not R.get('shift'):   # a recipe with a deliberate `shift` (Capitol stone's limestone) is exempt
            REPORT.append(f"  hue guard: {R['label']} on {sec} {round(H)}° → {round(near_h)}°"); H = near_h
        if tone == 'dark':
            Cq = min(max(mC*R.get('c', 1), .03), MOOD.get('dark_card_max_chroma', .08)); mut = from_oklch(.88, .02, H); ok = []
            for i in range(0, 61):
                L = .15 + .005*i; c = from_oklch(L, Cq, H)
                if ratio('#FFFFFF', c) >= AAA and ratio(mut, c) >= AAA: ok.append((L, c))
            j = min(range(len(ok)), key=lambda m: abs(ok[m][0] - mL))
            if is_dark(sec):   # dark card on a dark band: a step above the section (ΔE 6–14), or below it for recipes with lift "down"
                up_ = [m for m in range(len(ok)) if (ok[m][0] <= secL - .02 if R.get('lift') == 'down' else ok[m][0] >= secL + .02)]
                if up_: j = min(up_, key=lambda m: (0 if 6 <= dE(ok[m][1], sec) <= 14 else 1, abs(dE(ok[m][1], sec) - 10)))
        else:
            Cq = C*(R.get('c', 1) if mC >= .02 else min(R.get('c', 1), 1)); ok = []   # no chroma boost when the blend left almost no color
            for i in range(0, 41):
                L = .997 - .005*i; c = from_oklch(L, min(Cq, MOOD_C) if L >= MOOD_L else Cq, H)   # mood check: tone pastels down to a dusty version
                if L >= MOOD_L and Cq > MOOD_C and (sec, R['label']) not in MOODLOG: MOODLOG.append((sec, R['label']))
                if ratio(TX[0]['hex'], c) >= AAA and ratio(TX[1]['hex'], c) >= AAA: ok.append((L, c))
            if tone == 'white': j = 0
            elif is_dark(sec):   # light card on a dark band: a clean pale panel (Wada pairs deep navy with clear pale colors), not the greyest value AAA allows
                j = min(range(len(ok)), key=lambda m: abs(ok[m][0] - .94))
            else:
                def score(x):
                    # a panel sits a step deeper than its section where AAA allows (lighter panels read as Paper white); then ΔE 6–12, chroma kept
                    sep = dE(x[1], sec); return (0 if x[0] < secL - .01 else 1, 0 if 6 <= sep <= 12 else 1, 0 if oklch(x[1])[1] >= .75*Cq else 1, abs(sep - 8), -x[0])
                j = ok.index(min(ok, key=score))
                if dE(ok[j][1], sec) < 6: REPORT.append(f"  ! {R['label']} card on {sec}: under ΔE 6 with AAA text; the border carries the edge")
        gap = max(1, min(6, (len(ok) - 1)//5))   # up to .03 L apart, so neighbouring values stay visibly different
        start = min(max(0, j - 2*gap), max(0, len(ok) - 1 - 5*gap))
        idx = [start + gap*m for m in range(6) if start + gap*m < len(ok)]
        if j not in idx: idx[min(range(len(idx)), key=lambda m: abs(idx[m] - j))] = j
        steps_ = [ok[m][1] for m in idx]; di_ = idx.index(j); wt = tone == 'white'
        keep = [m for m, c in enumerate(steps_) if m == di_ or pair_ok(sec, c, wt)]   # drop background values that don't pair with the section
        if len(keep) < len(steps_): PAIRLOG.append((sec, f"{len(steps_) - len(keep)} {R['label']} values"))
        out.append((R['label'], H, [steps_[m] for m in keep], keep.index(di_), R, Cq))
    # pick six for this section: start from a light theme chosen by the section, then add the most distinct remaining theme each time,
    # keeping at least two dark (a third), so every row gets its own set and order
    bad = [t for t in out if not pair_ok(sec, t[2][t[3]], t[4].get('tone') == 'white')
           or any(r['theme'] == t[0] and r.get('section', '*') in ('*', sec) for r in MOOD_RULES)
           or (t[4].get('tone', 'panel') == 'panel' and oklch(t[2][t[3]])[0] > .965 and oklch(t[2][t[3]])[1] < .012)]   # toned down to plain white = a Paper white duplicate   # pairing failures and mood-review drops   # a theme whose default doesn't pair is replaced
    for t in bad: PAIRLOG.append((sec, f"{t[0]} theme"))
    good = [t for t in out if t not in bad]
    light = [t for t in good if t[4].get('tone') != 'dark']; dark = [t for t in good if t[4].get('tone') == 'dark']
    # fallback when too few themes survive: relax the pairing check, but never bring back a theme the mood review dropped;
    # a dark section needs only one dark card (see the pick below), so it doesn't trigger the fallback by itself
    mood_out = [t for t in out if any(r['theme'] == t[0] and r.get('section', '*') in ('*', sec) for r in MOOD_RULES)]
    if len(light) < 1 or len(dark) < (1 if is_dark(sec) else 2):
        light = [t for t in out if t[4].get('tone') != 'dark' and t not in mood_out]; dark = [t for t in out if t[4].get('tone') == 'dark' and t not in mood_out]
    # half subtle, half bold: subtle cards share the section's lightness (a panel a step off it), bold ones take the opposite lightness.
    # On a light section that's light panels + dark cards; on a dark band, dark cards lifted a step above it + light cards.
    N = S.get('card_theme_count', 6); nsub = N // 2
    if is_dark(sec):
        nd, nl = nsub, N - nsub
        # subtle means low contrast with the band: dark cards within ΔE 18 of it (in practice the tonal ones); a navy card on brick is ΔE ~50
        close = [t for t in dark if dE(t[2][t[3]], sec) <= 18]
        dark = close if len(close) >= nd else sorted(dark, key=lambda t: dE(t[2][t[3]], sec))[:max(nd, len(close))]
    else:
        nl, nd = nsub, N - nsub
    if len(dark) < nd: nd = len(dark); nl = N - nd
    if len(light) < nl: nl = len(light); nd = min(len(dark), N - nl)
    ml = [t for t in light if t[4].get('mood')] or light
    pick = [ml[int(sec[1:], 16) % len(ml)]]
    sL_, sC_, sH_ = oklch(sec); warm = sC_ >= .01 and 20 <= sH_ <= 120   # warm sections get at least two cool themes
    def room(t): return (sum(1 for p in pick if (p[4].get('tone') == 'dark') == (t[4].get('tone') == 'dark')) < (nd if t[4].get('tone') == 'dark' else nl))
    while warm and sum(1 for p in pick if p[4].get('cool')) < 2:
        cool = [t for t in light + dark if t[4].get('cool') and t not in pick and room(t) and t not in bad]   # the cool quota draws only from the subtle/bold pools and never brings back a dropped theme
        if not cool: break
        pick.append(max(cool, key=lambda t: min(dE(t[2][t[3]], q) for q in [sec] + [p[2][p[3]] for p in pick])))
    while len(pick) < nl + nd:
        pool = [t for t in (light if sum(1 for p in pick if p[4].get('tone') != 'dark') < nl else []) + (dark if sum(1 for p in pick if p[4].get('tone') == 'dark') < nd else []) if t not in pick and t[0] not in {p[0] for p in pick}]   # one theme per name (library themes can repeat a name)
        pick.append(max(pool, key=lambda t: min(dE(t[2][t[3]], q) for q in [sec] + [p[2][p[3]] for p in pick]) + (1.5 if t[4].get('mood') else 0)))
    sub = lambda t: (t[4].get('tone') == 'dark') == is_dark(sec)
    out = [t for t in pick if sub(t)] + [t for t in pick if not sub(t)]   # subtle first, then bold
    for i, t in enumerate(out):   # a default within ΔE 4 of an earlier pick moves to its own most distinct background value
        prev = [q[2][q[3]] for q in out[:i]] + [sec]
        if i and min(dE(t[2][t[3]], q) for q in prev) < 4:
            k = max(range(len(t[2])), key=lambda m: min(dE(t[2][m], q) for q in prev))
            out[i] = (t[0], t[1], t[2], k, *t[4:])
    d = [dE(x[2][x[3]], y[2][y[3]]) for i, x in enumerate(out) for y in out[i+1:]]
    if d and min(d) < 2.5: REPORT.append(f"  ! card themes on {sec}: two defaults only ΔE {min(d):.1f} apart")
    return out
def extras(sec, P, cards, TX):
    """section-row option sets: section accent (top bar) and the card themes with their background, border, accent, text and button"""
    def o(pairs):   # identical colors (e.g. reds that converge once darkened to AAA) share one chip with merged labels
        out = {}
        for h, l in pairs: out[h] = out[h] + " = " + l if h in out else l
        return [{"hex": h, "label": l} for h, l in out.items()]
    accs = [(P['accent'], "Palette accent"), (BRAND[0][1], BRAND[0][0])] + ([(BRAND[2][1], BRAND[2][0])] if len(BRAND) > 2 else []) + [(P['red'], "Red")]
    rh, rl, rs = hls(P['red']); themes = card_themes(sec, P, TX); allbg = [c for t in themes if t[4].get('tone') != 'dark' for c in t[2]]
    btn = lambda h: fit(h, ['#FFFFFF'], AAA)   # white button label at 7:1
    ca = o([(fit(h, allbg, AAA), l) for h, l in accs])
    ct = o([(fit(h, allbg, AAA), l) for h, l in [(TX[0]['hex'], "Heading ink"), (TX[1]['hex'], "Muted text"), (TX[2]['hex'], "Accent"), ("#111111", "Near black")]])
    rL, rC, rH = oklch(P['red']); iL, iC, iH = oklch(P['ink'])
    cc = o([(btn(P['red']), P['red_name'] + " (AAA)"), (btn(from_oklch(rL - (.97 - oklch(sec)[0])*.25, rC, nudge(rH, sec, .3, 12))), "Red tuned to section"),
            (btn(from_oklch(iL, max(iC, .05), nudge(iH, sec, .5, 30))), "Ink tinted to section"), (btn(BRAND[1][1]), BRAND[1][0] + " (AAA)"), (btn(hx(rh, rl - .06, rs)), "Red, 1 step darker"), (btn(P['ink']), "Ink"), (btn(P['accent']), "Accent")])
    names = ["Lighter 2", "Lighter 1", "Default", "Deeper 1", "Deeper 2", "Deeper 3"]
    def theme(label, H, steps, di, R, Cq, *_):
        # accent = the recipe's brand blend, six values that each keep 7:1 on every background of this theme
        dark = R.get('tone') == 'dark'; aL, aC, aH = mix(ref(R['acc'][0], sec, P), ref(R['acc'][1], sec, P), R['acc'][2]); acc = []
        aH = nudge(aH, sec, .3, 8)   # small turn toward the section; larger turns drifted blues to teal and reds to brown
        if dark and reddish(aH): aH, aC = BRASS, .06   # dark cards: brass instead of a pale red (pink)
        sl = oklch(sec)[0]
        def acc_list(aC, aH):   # six values of one accent hue that keep 7:1 on every background of this theme; start follows the section's lightness
            out = []
            for i in range(0, 66):
                c = from_oklch(.55 + .007*i + (.97 - sl)*.3 if dark else .80 - .01*i - (.97 - sl)*.6, max(aC, .06) if not dark else .07, aH)
                if min(ratio(c, b) for b in steps) >= AAA: out.append(c)
            return list(dict.fromkeys(out[::4]))[:6]
        acc = acc_list(aC, aH)
        an = label + " accent"; steps_lbl = ["most vivid", "step 2", "step 3", "step 4", "step 5", "palest"] if dark else ["brightest", "step 2", "step 3", "step 4", "step 5", "deepest"]
        if dark:
            sH = oklch(sec)[2] if oklch(sec)[1] >= .008 else H
            mH = nudge(H, sec, .5, 40); mH = BRASS if reddish(mH) else mH   # pale reds read pink: stone instead
            mut = darken_to(from_oklch(.80 + (oklch(sec)[0] - .9)*.5, .03, mH), steps, up=True)
            sc = darken_to(sec, steps, up=True); sc = darken_to(from_oklch(.9, .025, BRASS), steps, up=True) if reddish(oklch(sec)[2]) and oklch(sec)[1] >= .03 else sc
            tl = [("#FFFFFF", "White"), (sc, "Section color" if sc == darken_to(sec, steps, up=True) else "Pale stone"), (mut, "Muted light")]
            tx = {"opts": [{"hex": h, "label": l} for h, l in tl if min(ratio(h, b) for b in steps) >= AAA], "def": 0}
        else:
            th_ = nudge(H, sec, 0, 0); iL_, iC_, iH_ = oklch(P['ink'])
            mut = darken_to(from_oklch(.42, .03, H), steps)
            tl = [(darken_to(P['ink'], steps), "Heading ink"), (darken_to(from_oklch(iL_, max(iC_, .05), H), steps), "Ink tinted to card"),
                  (mut, "Muted, card hue"), (darken_to(from_oklch(.2, .02, oklch(sec)[2]), steps), "Near black, section hue")]
            tx = {"opts": o(tl), "def": 0}
        # each card text brings its own accent list: text 0 the theme accent, the others the first unused brand accent clearly apart from it
        BL = [(n, bc) for n, bc, *_ in LOGOS] + [("Palette", P['accent'])]
        if dark: BL = list({(("Brass", from_oklch(.8, .06, BRASS)) if reddish(oklch(h)[2]) else (n, h)) for n, h in BL})   # dark cards: brass in place of red
        BL.sort(key=lambda x: x[0])
        cands = [(an, acc)] + [(nm + " accent", acc_list(oklch(h)[1], nudge(oklch(h)[2], sec))) for nm, h in BL]
        cb = [(an, aC, aH)] + [(nm + " accent", oklch(h)[1], nudge(oklch(h)[2], sec, .3, 6)) for nm, h in BL]
        cb = [x for x, (n, l) in zip(cb, cands) if l]; cands = [(n, l) for n, l in cands if l]; used = set()
        for i, t in enumerate(tx['opts']):
            j = 0 if i == 0 else next((j for j, (n, l) in enumerate(cands) if j not in used and dE(l[0], t['hex']) >= 12),
                                       next((j for j, (n, l) in enumerate(cands) if dE(l[0], t['hex']) >= 12), 0))
            used.add(j)
            t['accs'] = accent_set([cb[m] for m in [j] + [m for m in range(len(cb)) if m != j]], steps, t['hex'], dark, sec=sec) or [{"hex": cands[j][1][0], "label": cands[j][0]}]
        label = f"{label} · {R.get('note', '')}".rstrip(' ·')
        red_theme = hdist(H, oklch(BRAND[1][1])[2]) <= 45 if len(BRAND) > 1 else False
        # buttons for this theme: each must stand out from every card background (3:1, WCAG non-text contrast); dark cards also get light
        # buttons with a dark label; default red, ink for red-leaning themes, else the first that passes
        cct = [dict(x) for x in cc if min(ratio(x['hex'], b) for b in steps) >= 3]
        if dark:
            rL_, rC_, rH_ = oklch(P['red'])
            for h, l in [("#FFFFFF", "White, ink label"), (from_oklch(.92, .035, BRASS), "Pale stone, ink label"), (from_oklch(.92, .03, oklch(BRAND[0][1])[2]), "Pale blue, ink label")]:
                f = darken_to(P['ink'], [h])
                if min(ratio(h, b) for b in steps) >= 3 and ratio(f, h) >= AAA: cct.append({"hex": h, "label": l, "fg": f})
        if not cct: cct = [dict(x) for x in cc]; REPORT.append(f"  ! {label} on {sec}: no button reaches 3:1 on the card")
        ci = next((i for i, x in enumerate(cct) if 'Ink' in x['label']), 0) if red_theme else 0
        bg = [{"hex": c, "label": names[j] if j < len(names) else f"Step {j+1}"} for j, c in enumerate(steps)]
        return {"hex": steps[di], "label": label, "cb": {"opts": bg, "def": di},
                "cbd": {"opts": [{"hex": b['hex'], "label": b['label']} for b in border_opts(steps[di])], "def": 1},
                "ca": {"opts": tx['opts'][0]['accs'], "def": 0}, "ct": tx, "mut": mut, "cc": {"opts": cct, "def": ci}}
    TH = [theme(*t) for t in themes]
    return {
      "a":   {"label": "Accent", "var": "--acc", "def": 0, "opts": o([(fit(h, [sec], AAA), l) for h, l in accs])},
      "th":  {"label": "Card theme", "var": "--th", "def": 0, "opts": TH},
      "cb":  {"label": "Card background", "var": "--cbg", "def": TH[0]['cb']['def'], "opts": TH[0]['cb']['opts']},
      "cbd": {"label": "Card border", "var": "--cbd", "def": 1, "opts": TH[0]['cbd']['opts']},
      "ca":  {"label": "Card accent", "var": "--cacc", "def": 0, "opts": TH[0]['ca']['opts']},
      "ct":  {"label": "Card text", "var": "--ctx", "def": 0, "opts": TH[0]['ct']['opts']},
      "cc":  {"label": "Card button", "var": "--cta", "def": TH[0]['cc']['def'], "opts": TH[0]['cc']['opts']}}
 
paper = S.get('paper', '#F6F3EC')
groups = [{"title": "Brand colors", "compact": True, "sub": S.get('brand_sub', "The project's brand colors. Every palette below is checked against them for hue harmony."), "swatches": [
    sw(bc, n, paper, f"Hue {round(hls(bc)[0])}°." + (" Primary: cards and borders lean toward this hue." if i == 0 else (" " + note if note else "")))
    for i, (n, bc, note, _) in enumerate(BRAND)]}]
pairs = []; sample = S['sample']
for P in S['palettes']:
    name = P['name']
    if MODE == 'dark':
        bg = P['bg']; h, l, s = hls(bg); cs = min(s*.85, SATCAP)
        cards = {st: hx(h + (LOGO - h)*f, l + dl, cs) for st, dl, f in STEPS}; bopts = {st: border_opts(cards[st]) for st in cards}
        TX = text_opts(bg, (P['footer'], *cards.values()))
        hm = "; ".join(f"{k} vs {v}" for k, v in (("background", harmony(bg)), ("accent", harmony(P['accent'])), (P['red_name'].lower(), harmony(P['red']))) if v)
        groups.append({"title": name, "sub": P['sub'] + f" Brighter cards shift from {round(h)}° toward the logo's {round(LOGO)}°. Brand harmony: " + hm + ".", "swatches": [
            sw(P['footer'], "Footer / ink", P['footer'], "Footer and darkest bands.", TX),
            sw(bg, "Section background", bg, "Main dark section bands. Borders are for outlined elements and dividers sitting directly on it.", TX),
            sw(cards['third'], "Card · third step", bg, "Subtle. Needs a 1px border to read as a panel.", TX, borders=bopts['third']),
            sw(cards['half'], "Card · half step", bg, "Reads as a panel on large areas; a 1px border helps on small cards.", TX, borders=bopts['half']),
            sw(cards['full'], "Card · full step", bg, "Clear lift on its own. The border is optional.", TX, borders=bopts['full'], pick=True),
            sw(P['accent'], "Accent", paper, "Links and accents on the light paper."),
            sw(P['light'], "Light panel", bg, "Pale panel for forms and light sections."),
            sw(P['red'], P['red_name'], P['red'], "Buttons and calls to action.")]})
        for st, label in (('full', 'full-step cards'), ('half', 'half-step cards with border')):
            b = bopts['half'][1]['hex']
            pairs.append(dict(sample, title=f"{name} · {label}", sub=f"{bg} band, {cards[st]} cards{', 1px '+b+' border' if st != 'full' else ''}, {TX[0]['hex']} text.", bg=bg,
                              tagColor=TX[2]['hex'], cardBg=cards[st], cardFg=TX[0]['hex'], button=True, btnColor=P['red'], **({"cardBorder": b} if st != 'full' else {})))
        contrast_line(name, TX, [bg, P['footer'], *cards.values()])
        for k, v in (("background", harmony(bg)), ("accent", harmony(P['accent'])), ("CTA", harmony(P['red']))):
            if v and 'near-miss' in v: REPORT.append(f"  ! {name}: {k} {v}")
        continue
    # light mode
    area = P['area']; h, l, s = hls(area); d, n = near(h); ink = P['ink']; ih = hls(ink)[0]
    PS = P.get('sections')   # optional per-palette section list [{key, hex, name, use}] in page-row order; replaces paper/area/band + 3 comp
    comp = [x['hex'] for x in PS if x['key'].startswith('comp')] if PS else auto_comp(ink, name) if P.get('comp', 'auto') == 'auto' else P['comp']
    cards = {st: hx(h + (d*f if n else 0), min(l + dl, 1), min(s, SATCAP)) for st, dl, f in STEPS}
    if P['paper'] == "#FFFFFF": cards['full'] = "#FFFFFF"
    bopts = {st: border_opts(cards[st]) for st in cards}
    secs = [x['hex'] for x in PS] if PS else [P['paper'], area, P['band'], *comp]
    TX = text_opts(area, tuple(c for c in (*[c for c in secs if c != area], *cards.values()) if not is_dark(c)), P)
    hm = "; ".join(f"{k} vs {v}" for k, v in (("area", harmony(area)), ("ink", harmony(ink)), ("accent", harmony(P['accent'])), ("CTA", harmony(P['red']))) if v)
    su = S.get('section_uses', ["Lightest band: intro copy and long-form reading.", "Middle band: card grids and forms. Cards below sit on it.", "Deepest cool band: replaces a dark band."])
    cu = P.get('comp_uses') or S.get('comp_uses', ["Warm counterpoint to Section 1: long copy.", "Warm mid band: a pull quote or feature.", "Deepest warm band: calls to action."])
    cb = bopts['full'][1]['hex']; c0 = sample['cards'][0]
    LY = dict(eyebrow=sample['tag'], h=sample['heading'], cardH=c0['h'], cardP=c0['p'], ctaLabel=c0['cta'],
              accent=TX[2]['hex'], muted=TX[1]['hex'], cta=P['red'], card=cards['full'], cardBorder=cb)
    names = ["Section 1 · paper", "Section 2 · tint", "Section 3 · deep tint", "Section 4 · light complement", "Section 5 · mid complement", "Section 6 · deep complement"]
    uses = [*su, *[cu[k] + f" Hue {round(hls(c)[0])}°, {round(hdist(hls(c)[0], ih))}° from the ink's {round(ih)}°." for k, c in enumerate(comp)]]
    if PS:
        names = [f"Section {i+1} · {x['name']}" for i, x in enumerate(PS)]
        uses = [x.get('use', '') + (f" Hue {round(hls(x['hex'])[0])}°, {round(hdist(hls(x['hex'])[0], ih))}° from the ink's {round(ih)}°." if x['key'].startswith('comp') else "") for x in PS]
    cm = comp[len(comp)//2] if comp else area
    groups.append({"title": name, "one": True, "sub": P['sub'] + f" Complement: {P.get('comp_name', 'opposite tints')} at {round(hls(cm)[0])}°, {round(hdist(hls(cm)[0], ih))}° from the {round(ih)}° ink. Brand harmony: {P.get('harmony') or hm}.", **({"mood": P['mood']} if P.get('mood') else {}), **({"tech": P['tech']} if P.get('tech') else {}), "swatches": [
        sw(c, nm, c, u, sec_text(c, P), layout=LY, extra=extras(c, P, cards, TX)) for c, nm, u in zip(secs, names, uses)]})
    secmap = {x['key']: (x['hex'], i+1) for i, x in enumerate(PS)} if PS else {'paper': (P['paper'], 1), 'area': (area, 2), 'band': (P['band'], 3), 'comp1': (comp[0], 4), 'comp2': (comp[1], 5), 'comp3': (comp[2], 6)}
    stack = [dict(bg=secmap[b['sec']][0], n=secmap[b['sec']][1], kind=b['kind'], h=b.get('h', sample['heading']), **({"p": b['p']} if 'p' in b else {}),
                  **({"fg": "#FFFFFF", "muted": darken_to(from_oklch(.86, .03, oklch(secmap[b['sec']][0])[2]), [secmap[b['sec']][0]], up=True),
                      "tag": darken_to(from_oklch(.82, .08, oklch(BRAND[0][1])[2]), [secmap[b['sec']][0]], up=True)} if is_dark(secmap[b['sec']][0]) else {})) for b in P.get('stack', S['stack'])]
    pairs.append(dict(sample, title=f"{name} · {WORDS.get(len(stack), len(stack))} sections in page order", sub=P.get('stack_sub') or S.get('stack_sub', "The section backgrounds in page order."), stack=stack, before=name,
                      muted=TX[1]['hex'], headFg=TX[0]['hex'], tagColor=TX[2]['hex'], cardBg=cards['full'], cardBorder=bopts['full'][1]['hex'], cardFg=TX[0]['hex'], button=True, btnColor=P['red']))
    for s in groups[-1]['swatches']:   # each section text option carries a matching base accent: the first unused one clearly apart from it
        A = s['extra']['a']['opts']; used = set()
        for i, t in enumerate(s['texts']):
            j = 0 if i == 0 else next((j for j, a in enumerate(A) if j not in used and dE(a['hex'], t['hex']) >= 12),
                                       next((j for j, a in enumerate(A) if dE(a['hex'], t['hex']) >= 12), 0))
            t['acc'] = j; used.add(j)
            # the accent list that comes with this text: its paired accent first, then other brand accents, each in three brightness steps
            order = [j] + [m for m in range(len(A)) if m != j]
            t['accs'] = accent_set([(A[m]['label'].split(' = ')[0], *oklch(A[m]['hex'])[1:]) for m in order], [s['hex']], t['hex'], is_dark(s['hex']), sec=s['hex']) or [A[j]]
        s['extra']['a'] = {**s['extra']['a'], "opts": s['texts'][0]['accs'], "def": 0}
    contrast_line(name, TX, [c for c in [*secs, *cards.values()] if not is_dark(c)])
    for k, v in (("area", harmony(area)), ("ink", harmony(ink)), ("accent", harmony(P['accent'])), ("CTA", harmony(P['red']))):
        if v and 'near-miss' in v: REPORT.append(f"  ! {name}: {k} {v}")
    for i, c in enumerate(secs): check_avoid(name, f'Section {i+1}', c)
    if PS:
        order = [secmap[b['sec']][0] for b in P.get('stack', S['stack'])]
        REPORT.append(f"  {name}: section step ΔE in row order {[round(dE(a, b), 1) for a, b in zip(secs, secs[1:])]}; in page order {[round(dE(a, b), 1) for a, b in zip(order, order[1:])]}")
    else:
        steps = [round(dE(a, b), 1) for a, b in zip(secs[:3], secs[1:3])] + [round(dE(a, b), 1) for a, b in zip(comp, comp[1:])]
        REPORT.append(f"  {name}: section step ΔE cool {steps[:2]} warm {steps[2:]}")
    worst = []
    for s in groups[-1]['swatches']:
        X = s['extra']; sec = s['hex']; cbs = [x['hex'] for t in X['th']['opts'] for x in t['cb']['opts']]
        worst += [(ratio(t['hex'], sec), f"section text {t['hex']} on {sec}") for t in s['texts']]
        worst += [(ratio(a['hex'], sec), f"section accent {a['hex']} on {sec}") for t in s['texts'] for a in t.get('accs', X['a']['opts'])]
        worst += [(ratio(t['hex'], c), f"card accent {t['hex']} on {c}") for T in X['th']['opts'] for c in [x['hex'] for x in T['cb']['opts']] for t in T['ca']['opts']]
        for T in X['th']['opts']:
            tb = [x['hex'] for x in T['cb']['opts']]
            worst += [(ratio(t['hex'], c), f"card text {t['hex']} on {c}") for c in tb for t in T['ct']['opts']]
            worst += [(ratio(a['hex'], c), f"card accent {a['hex']} on {c}") for c in tb for t in T['ct']['opts'] for a in t['accs']]
            worst += [(ratio(T['mut'], c), f"card body {T['mut']} on {c}") for c in tb]
        worst += [(ratio(b.get('fg', '#FFFFFF'), b['hex']), f"button label on {b['hex']}") for T in X['th']['opts'] for b in T['cc']['opts']]
    w = min(worst)
    REPORT.append(f"  {name}: AAA audit of {len(worst)} text pairings: worst {w[0]:.2f}:1 ({w[1]})" + ("" if w[0] >= AAA - 1e-9 else "  ! FAILS AAA"))
 
cfg = {"title": S['title'], "eyebrow": S['eyebrow'], "heading": S['heading'], "lede": S['lede'], "groups": groups, "pairings": pairs, "footnote": S.get('footnote', '')}
if CFG: json.dump(cfg, open(CFG, 'w'), ensure_ascii=False)
html = open(TPL).read()
assert html.count('__CONFIG__') == 1 and html.count('__TITLE__') == 1, "template must contain each placeholder exactly once"
# ---- clean-up pass: every option must be on brand and clearly different from its neighbours in the same control ----
SEP = {"text": 8, "accent": 8, "button": 8, "background": 3, "border": 3, "overlay": 2.5}
def clean(L, kind, anchors, bgs=None, de=0, label=lambda o: o.get('label', ''), tally=None):
    """returns (list, new default index). Off-brand colors (chroma >= .03, hue > 35° from every anchor) are redone at the nearest anchor hue
    (contrast refitted to 7:1 on `bgs` when given) or dropped; then items closer than SEP[kind] ΔE to one already kept are dropped.
    The default is always kept (redone if it was off brand)."""
    if not L: return L, de
    out = []
    for i, o in enumerate(L):
        c = o['hex']; Lc, Cc, Hc = oklch(c)
        if Cc >= .03 and min(hdist(Hc, a) for a in anchors) > 35:
            a = min(anchors, key=lambda a: hdist(Hc, a)); n = from_oklch(Lc, Cc, a)
            if bgs: n = darken_to(n, bgs, up=is_dark(bgs[0]))
            if not bgs or min(ratio(n, b) for b in bgs) >= AAA - 1e-9:
                o = {**o, "hex": n}; tally['redone'] += 1
            elif i != de: tally['removed'] += 1; continue
        out.append((i, o))
    keep = [x for x in out if x[0] == de][:1]
    for i, o in out:
        if keep and (i, o) == keep[0]: continue
        if all(dE(o['hex'], q['hex']) >= SEP[kind] for _, q in keep): keep.append((i, o))
        else: tally['close'] += 1
    keep.sort(key=lambda x: x[0]); nd = next((j for j, (i, _) in enumerate(keep) if i == de), 0)
    return [o for _, o in keep], nd
for P in S['palettes'] if MODE == 'light' else []:
    g = next(g for g in groups if g['title'] == P['name']); T_ = {"redone": 0, "removed": 0, "close": 0}
    secs_ = [s['hex'] for s in g['swatches']]
    anchors = [oklch(bc)[2] for n, bc, *_ in BRAND if oklch(bc)[1] >= .03] + [oklch(P[x])[2] for x in ('ink', 'accent', 'red')] + \
              [oklch(c)[2] for c in secs_ if oklch(c)[1] >= .012] + [oklch(r)[2] for R in S.get('card_themes', DEFAULT_THEMES) + MOOD.get('themes', []) + library_themes(P) for r in R['bg'] + R['acc'] if isinstance(r, str) and r.startswith('#')]
    for s in g['swatches']:
        X = s.get('extra'); sec = s['hex']
        s['overlays'], _ = clean(s['overlays'], 'overlay', anchors, tally=T_)
        bd = next((i for i, b in enumerate(s['borders']) if b.get('default')), 1); s['borders'], _ = clean(s['borders'], 'border', anchors, de=bd, tally=T_)
        s['texts'], _ = clean(s['texts'], 'text', anchors, [sec], 0, tally=T_)
        for t in s['texts']:
            if 'accs' in t: t['accs'], _ = clean(t['accs'], 'accent', anchors, [sec], 0, tally=T_)
        if not X: continue
        X['a'] = {**X['a'], "opts": s['texts'][0].get('accs', X['a']['opts']), "def": 0}
        for T in X['th']['opts']:
            T['cb']['opts'], T['cb']['def'] = clean(T['cb']['opts'], 'background', anchors, de=T['cb']['def'], tally=T_)
            T['cbd']['opts'], T['cbd']['def'] = clean(T['cbd']['opts'], 'border', anchors, de=T['cbd']['def'], tally=T_)
            bgs = [o['hex'] for o in T['cb']['opts']]
            T['ct']['opts'], T['ct']['def'] = clean(T['ct']['opts'], 'text', anchors, bgs, T['ct']['def'], tally=T_)
            for t in T['ct']['opts']: t['accs'], _ = clean(t['accs'], 'accent', anchors, bgs, 0, tally=T_)
            T['ca'] = {"opts": T['ct']['opts'][0]['accs'], "def": 0}
            T['cc']['opts'], T['cc']['def'] = clean(T['cc']['opts'], 'button', anchors, None, T['cc']['def'], tally=T_)
        T0 = X['th']['opts'][0]
        for key in ('cb', 'cbd', 'ca', 'ct', 'cc'): X[key] = {**X[key], "opts": T0[key]['opts'], "def": T0[key]['def']}
    pl = [w for s_, w in PAIRLOG if s_ in secs_]
    REPORT.append(f"  {P['name']}: brand + separation check: {T_['redone']} off-brand colors redone, {T_['removed']} removed, {T_['close']} too-close options dropped; "
                  f"mood check: {len([1 for s_, w in MOODLOG if s_ in secs_])} pastel themes toned down; section/card pairing: {len(pl)} fixes" + (f" ({', '.join(pl[:6])}{'…' if len(pl) > 6 else ''})" if pl else ""))
# mood review sheet: every section's themes in plain words beside the brief and each theme's job, for a "does this fit?" read
if MODE == 'light':
    NOPRE = []
    lines = [f"MOOD REVIEW · {S['title']}", f"Mood: {MOOD.get('words', '(none set: add settings mood.words)')}",
             "Ask of every theme: does this color fit the mood, the palette's brief and the theme's job? Record misfits in settings mood_review.", ""]
    for P in S['palettes']:
        g = next(g for g in groups if g['title'] == P['name']); lines += [f"## {P['name']}: {P['sub'][:220]}"]
        for s in g['swatches']:
            lines.append(f"- section {s['hex']} \"{hex_name(s['hex'])}\" ({color_words(s['hex'])}):")
            for T in s['extra']['th']['opts']:
                nm, _, job = T['label'].partition(' · ')
                bt = T['cc']['opts'][T['cc']['def']]['hex']; pr = precedent(s['hex'], T['hex']); NOPRE.append(0 if pr else 1)
                lines.append(f"    {nm}: {T['hex']} \"{hex_name(T['hex'])}\" ({color_words(T['hex'])}); accent \"{hex_name(T['ca']['opts'][0]['hex'])}\"; button \"{hex_name(bt)}\""
                             + ("" if pr else "  [no library precedent for this section + card pair]") + f" | job: {job[:80]}")
        lines.append("")
    open(OUT.rsplit('.', 1)[0] + '-mood-review.txt', 'w').write("\n".join(lines))
    REPORT.append(f"  mood review sheet: {OUT.rsplit('.', 1)[0]}-mood-review.txt ({len(MOOD_RULES)} saved mood drops applied; {sum(NOPRE)} of {len(NOPRE)} section + card pairs have no library precedent"
                  + ("" if REFS else "; refs.json missing: names and precedent skipped") + ")")
def pack(x):
    # accent lists go out short: [[name, dark, hex, hex, hex], ...]; the template's unA() expands them (cuts the page by about a third)
    if isinstance(x, dict): return {k: (packA(v) if k == 'accs' else pack(v)) for k, v in x.items()}
    if isinstance(x, list): return [pack(v) for v in x]
    return x
def packA(L):
    out = []
    for a in L:
        n, _, s = a['label'].rpartition(' · '); n = n or a['label']
        if not out or out[-1][0] != n: out.append([n, int(s in ("vivid", "light", "palest"))])
        out[-1].append(a['hex'])
    return out
# section-specific check: every option list should differ between the sections of a palette
for g in groups:
    sws = [s for s in g['swatches'] if s.get('extra')]
    if len(sws) < 2: continue
    def lists(s):
        X = s['extra']; d = {'section text': [t['hex'] for t in s['texts']], 'button': [o['hex'] for o in X['cc']['opts']], 'theme order': [T['label'] for T in X['th']['opts']]}
        for T in X['th']['opts']:
            n = T['label'].split(' ·')[0]; d[n + ' background'] = [o['hex'] for o in T['cb']['opts']]; d[n + ' text'] = [o['hex'] for o in T['ct']['opts']]
            d[n + ' accents'] = [a['hex'] for t in T['ct']['opts'] for a in t['accs']]
        return d
    L = [lists(s) for s in sws]; rp = []
    for key in sorted({x for l in L for x in l}):
        vals = [tuple(l[key]) for l in L if key in l]
        if len(set(vals)) < len(vals): rp.append(f"{key} {len(set(vals))}/{len(vals)}")
    REPORT.append(f"  {g['title']}: section-specific check: " + ("every option list differs" if not rp else "repeats in " + ", ".join(rp)))
html = html.replace('__TITLE__', S['title']).replace('__CONFIG__', json.dumps(pack(cfg), ensure_ascii=False, separators=(',', ':')))
open(OUT, 'w').write(html)
print(f"{OUT}: {len(html)//1024} KB, {sum(len(g['swatches']) for g in groups)} swatches, {len(pairs)} previews, mode {MODE}")
print("\n".join(REPORT) if REPORT else "  no issues")