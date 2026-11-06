# New Statecraft palette study. Same generator as the color-swatch-study skill, with this project's parameters.
# python3 build_palette_swatches.py config.json && python3 fill.py swatch-template.html config.json out.html
import json, colorsys, sys
# ---- edit these ----
TITLE="Flag Blue Palettes"; EYEBROW="newstatecraft.org · color study"; HEADING="Old Glory and Federal navy"
LEDE="Two flag-blue directions to replace the frame's 207° airline blue. Cards are a third, half and full step brighter than the section background; as they brighten their hue moves toward the logo's 207° and saturation stays at 60% or below."
BRAND=[("Logo blue","#135389"),("Logo red","#E61C2C"),("Logo purple","#742376")]  # New Statecraft logo colors; first is the primary
LOGO_HEX=BRAND[0][1]
PAPER="#F6F3EC"
PALETTES=[
 dict(name="Old Glory",sub="Anchored on the official U.S. flag blue, #0A3161 (hue 213°). The smallest shift that reads as flag rather than airline. Buttons use the logo red.",footer="#071C36",bg="#0A3161",accent="#214D83",light="#E9EFF7",red="#E61C2C",red_name="Logo red"),
 dict(name="Federal navy",sub="Hue 218° with saturation pulled back, lifted a quarter step from #162B50 to #182E56. Reads like a government seal or a Senate binder: formal and inky without going glossy. Buttons use the logo red.",footer="#0C182C",bg="#182E56",accent="#2A4779",light="#EAEEF5",red="#E61C2C",red_name="Logo red"),
]
FOOTNOTE="Old Glory sits closer to the logo hue; Federal navy reads a little more violet than the logo. Contrast is calculated live from the hex values."
SAMPLE={"tag":"Featured projects","heading":"Two flagship endeavors","cards":[{"h":"Transformative Leadership Initiative","p":"Congress can work again if enough lawmakers put country before party.","cta":"Explore the Initiative"},{"h":"Elections Reality Project","p":"Accurate information is essential to a truthfully informed democracy.","cta":"Explore the Project"}]}
# --------------------
def lum(h):
    c=[int(h[i:i+2],16)/255 for i in (1,3,5)];c=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in c];return .2126*c[0]+.7152*c[1]+.0722*c[2]
def ratio(a,b):x,y=lum(a),lum(b);return (max(x,y)+.05)/(min(x,y)+.05)
hx=lambda h,l,s:'#%02X%02X%02X'%tuple(round(x*255) for x in colorsys.hls_to_rgb((h%360)/360,min(l,1),min(s,1)))
def hls(c):h,l,s=colorsys.rgb_to_hls(*[int(c[i:i+2],16)/255 for i in (1,3,5)]);return h*360,l,s
LOGO=hls(LOGO_HEX)[0]
STEPS=[('third',.02,1/6),('half',.035,.25),('full',.06,.5)]          # step, lightness lift, share of hue shift toward logo
SATCAP=.60
BOPTS=[('¼ step from fill',.015,.05),('Base',.07,.15),('+½ step',.105,.25),('+1 step',.13,.35),('+2 steps · bold',.19,.45),('+3 steps · bold',.25,.55)]  # label, lightness offset from the fill, share of hue shift toward logo
def border_opts(fill):
    # borders brighten on dark fills and darken on light ones; hue leans toward the logo only for fills within 45° of it
    fh,fl,fs=hls(fill); sign=1 if fl<.6 else -1
    d=((LOGO-fh+180)%360)-180; near=abs(d)<45
    return [{"hex":hx(fh+(d*bf if near else 0),max(0,min(1,fl+sign*dl)),min(fs*.8,.48)),"label":lab,**({"default":True} if lab=='Base' else {})} for lab,dl,bf in BOPTS]
def harmony(c):
    # hue relationship to the closest saturated brand color: same family <=12 deg, near-miss 12-30 (avoid), analogous 30-60, complement >=150
    ch,cl,cs=hls(c)
    if cs<.12: return None
    best=None
    for n,bc in BRAND:
        bh,bl,bs=hls(bc)
        if bs<.12: continue
        d=abs(((ch-bh+180)%360)-180)
        if best is None or d<best[1]: best=(n,d)
    if not best: return None
    n,d=best
    lab='same family' if d<=12 else 'near-miss, may read as a mismatch' if d<=30 else 'analogous' if d<=60 else 'complement' if d>=150 else 'contrast'
    return f"{n} {round(d)}° ({lab})"
OPTS_OVERLAY=[('−3 steps',-.18,0),('−2 steps',-.12,0),('−1 step',-.06,0),('−½ step',-.035,0),('−⅓ step',-.02,0),('−¼ step',-.015,0),('+¼ step',.015,1/8),('+⅓ step',.02,1/6),('+½ step',.035,.25),('+1 step',.06,.5),('+2 steps',.12,.65),('+3 steps',.18,.8)]  # label, lightness change, share of hue shift toward logo
def overlay_opts(fill):
    # the fill stepped darker and lighter; lighter steps lean toward the logo hue (fills within 45 deg of it), saturation capped like cards
    fh,fl,fs=hls(fill); d=((LOGO-fh+180)%360)-180; near=abs(d)<45
    return [{"hex":hx(fh+(d*hf if near else 0),max(0,min(.99,fl+dl)),min(fs,SATCAP) if dl>0 else fs),"label":lab} for lab,dl,hf in OPTS_OVERLAY]
WARM_HEX=BRAND[1][1] if len(BRAND)>1 else LOGO_HEX  # second brand color tints the red/warm text option
def tsearch(h,l,s,fills,minr,step):
    while 0<=l<=1:
        c=hx(h,max(0,min(1,l)),s)
        if min(ratio(c,f) for f in fills)>=minr: return c
        l+=step
    return '#FFFFFF' if step>0 else '#000000'
def text_opts(fill,also=()):
    # four text colors that pass on this fill (and on every fill in `also`, so a palette's dark swatches share one set): light ones on dark fills, dark ones on light fills
    fh,fl,fs=hls(fill); wh=hls(WARM_HEX)[0]; mid=fh+(((LOGO-fh+180)%360)-180)/2; fill=[fill,*also]
    if ratio(fill[0],'#FFFFFF')>=ratio(fill[0],'#111111'):
        return [{"hex":tsearch(fh,.95,.40,fill,7,.01),"label":"Light text"},{"hex":tsearch(fh,.74,.22,fill,4.5,.01),"label":"Muted text"},
                {"hex":tsearch(mid,.74,.55,fill,4.5,.01),"label":"Light accent"},{"hex":tsearch(wh,.76,.65,fill,4.5,.01),"label":"Light red accent"}]
    return [{"hex":tsearch(fh,.14,.35,fill,7,-.01),"label":"Dark text"},{"hex":tsearch(fh,.36,.15,fill,4.5,-.01),"label":"Muted text"},
            {"hex":tsearch(LOGO,.34,.6,fill,4.5,-.01),"label":"Dark accent"},{"hex":tsearch(wh,.40,.7,fill,4.5,-.01),"label":"Dark red accent"}]
groups=[{"title":"Brand colors","sub":"The project's brand colors. Every palette below is checked against them for hue harmony.","swatches":[
    {"hex":bc,"name":n,"on":PAPER,"borders":border_opts(bc),"overlays":overlay_opts(bc),"texts":text_opts(bc),"use":f"Hue {round(hls(bc)[0])}°."+(" Primary: cards and borders lean toward this hue." if i==0 else "")} for i,(n,bc) in enumerate(BRAND)]}]
pairs=[]
for P in PALETTES:
    bg=P['bg'];h,l,s=hls(bg);cs=min(s*.85,SATCAP)
    cards={st:hx(h+(LOGO-h)*f,l+dl,cs) for st,dl,f in STEPS}
    bopts={st:border_opts(cards[st]) for st in cards}
    TX=text_opts(bg,(P['footer'],*cards.values()))  # one shared text set for the palette's dark swatches; it passes on all of them
    groups.append({"title":P['name'],"sub":P['sub']+f" Brighter cards shift from {round(h)}° toward the logo's {round(LOGO)}°. Brand harmony: "+"; ".join(f"{k} vs {v}" for k,v in (("background",harmony(bg)),("accent",harmony(P['accent'])),(P['red_name'].lower(),harmony(P['red']))) if v)+".","swatches":[
        {"hex":P['footer'],"on":P['footer'],"borders":border_opts(P['footer']),"overlays":overlay_opts(P['footer']),"texts":TX,"name":"Footer / ink","use":"Footer and darkest bands."},
        {"hex":bg,"name":"Section background","on":bg,"borders":border_opts(bg),"overlays":overlay_opts(bg),"texts":TX,"use":"Main dark section bands. Borders are for outlined elements and dividers sitting directly on it."},
        {"hex":cards['third'],"name":"Card · third step","on":bg,"borders":bopts['third'],"overlays":overlay_opts(cards['third']),"texts":TX,"use":"Subtle. Needs a 1px border to read as a panel."},
        {"hex":cards['half'],"name":"Card · half step","on":bg,"borders":bopts['half'],"overlays":overlay_opts(cards['half']),"texts":TX,"use":"Reads as a panel on large areas; a 1px border helps on small cards."},
        {"hex":cards['full'],"name":"Card · full step","on":bg,"borders":bopts['full'],"overlays":overlay_opts(cards['full']),"texts":TX,"use":"Clear lift on its own. The border is optional.","pick":True},
        {"hex":P['accent'],"name":"Accent","on":PAPER,"borders":border_opts(P['accent']),"overlays":overlay_opts(P['accent']),"texts":text_opts(P['accent']),"use":"Links and accents on the light paper."},
        {"hex":P['light'],"name":"Light panel","on":bg,"borders":border_opts(P['light']),"overlays":overlay_opts(P['light']),"texts":text_opts(P['light']),"use":"Pale panel for forms and light sections."},
        {"hex":P['red'],"on":P['red'],"borders":border_opts(P['red']),"overlays":overlay_opts(P['red']),"texts":text_opts(P['red']),"name":P['red_name'],"use":"Buttons and calls to action."}]})
    for st,label in (('full','full-step cards'),('half','half-step cards with border')):
        b=bopts['half'][1]['hex']
        pairs.append(dict(SAMPLE,title=f"{P['name']} · {label}",sub=f"{bg} band, {cards[st]} cards{', 1px '+b+' border' if st!='full' else ''}, {TX[0]['hex']} text.",bg=bg,tagColor=TX[2]['hex'],cardBg=cards[st],cardFg=TX[0]['hex'],button=True,btnColor=P['red'],**({"cardBorder":b} if st!='full' else {})))
cfg={"title":TITLE,"eyebrow":EYEBROW,"heading":HEADING,"lede":LEDE,  # the Brand colors group replaces the old single "anchor" swatch
     "groups":groups,"pairings":pairs,"footnote":FOOTNOTE}
json.dump(cfg,open(sys.argv[1] if len(sys.argv)>1 else 'swatch-config.json','w'),ensure_ascii=False)