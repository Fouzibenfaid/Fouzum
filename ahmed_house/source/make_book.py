"""builds the lookbook page: lime/oak/travertine palette, one section per space"""
import os, base64, io, sys
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(ROOT, 'final')

FIGS = {'street_day': 'West facade · fins 6 × 28 cm at 35 cm', 'street_dusk': 'Light 2700 K · no exterior spotlights', 'entry_eve': 'Canopy 3.5 m · pivot door 1.1 × 2.7 m', 'hall_day': 'Ceiling 3.35 m opening to 7 m', 'living_day': '47.1 m² with library, arrival & dining', 'living_eve': 'Cove light 2700 K, dimmable', 'library_day': 'Rooflight 5.5 × 1.4 m', 'courtyard_day': '8.8 m² open to the sky', 'kitchen_day': 'Kitchen + pantry 10.4 m² · island 2.3 m', 'majlis_eve': '13.8 m² · two sliding oak walls', 'master_day': '15.1 m² · dressing 5.4 m²', 'master_eve': '15.1 m² · ribbon window facing east', 'ensuite_day': '5.1 m² · walk-in rain shower'}

SECTIONS = [
    ('street_day', 'Exterior', 'From the street', 'One continuous screen of bronze aluminium fins wraps the first floor: afternoon shade and privacy, while you still see out. Warm lime-plaster render, a travertine band at the floor line and a slim bronze roof edge.'),
    ('street_dusk', 'Exterior', 'Blue hour', 'The house glows through the fins, with no exterior spotlights. Wall-washers light the plaster of the entry court and an uplight catches the olive tree.'),
    ('entry_eve', 'Arrival', 'The walled entry court', 'Your own bronze gate opens onto gravel, travertine stepping stones, a shallow stone water basin and an olive tree. A 3.5 m canopy with an oak soffit shelters the 1.1 × 2.7 m smoked-oak pivot door.'),
    ('hall_day', 'Arrival', 'Entrance hall', 'Compression, then release. A 3.35 m ceiling at the door opens to 7 m under the skylight. Floating oak treads rise beside you toward the light, past a travertine feature wall and a built-in smoked-oak bench wall.'),
    ('living_day', 'Family', 'Living room', 'A low L-shaped sofa in oatmeal bouclé, travertine block tables and a natural wool rug. Sheer linen softens the street glass, and an olive tree in terracotta brings the garden in.'),
    ('living_eve', 'Family', 'Living room, evening', 'Warm light only (2700 K), hidden in ceiling coves. Add a floor lamp, the bio-ethanol fire in the long travertine shelf, and no downlights.'),
    ('library_day', 'Family', 'Library alcove', 'An oak shelving wall faces a cushioned window seat, with light pouring in from the 5.5 m linear rooflight above. The smoked-oak TV wall closes the view.'),
    ('courtyard_day', 'The heart', 'Courtyard', 'A piece of garden in the middle of the house, open to the sky. One olive tree in a travertine planter, a built-in bench along the back wall and the same floor level inside and out.'),
    ('kitchen_day', 'Cooking', 'Dining & kitchen', 'A 2.3 m travertine island with waterfall ends is the clean show piece. The working kitchen sits behind a glass slider in smoked oak. An oak table seats eight on woven-seat chairs under paper globe pendants.'),
    ('majlis_eve', 'Guests', 'Majlis', 'Low, deep seating in sand linen, made modern: the majlis tradition with bolsters, a travertine table and a bronze coffee service. Two sliding oak walls open it to the living room and the arrival.'),
    ('master_day', 'Private', 'Master suite', 'The quietest room. A tall upholstered linen headboard, floating oak side tables with plaster wall lights and a bouclé bench at the foot of the bed. Morning light falls from the ribbon window above.'),
    ('master_eve', 'Private', 'Master suite, evening', 'Cove light, wall lights and a linen-shaded floor lamp by the reading chair: soft, warm, low.'),
    ('ensuite_day', 'Private', 'Wellness ensuite', 'Travertine from floor to ceiling, a walk-in rain shower under its own rooflight, a floating smoked-oak vanity, a stoneware basin and a round bronze mirror.'),
]

def build(out_html):
    items = [(k, z, t, x) for (k, z, t, x) in SECTIONS if os.path.exists(os.path.join(FINAL, k + '.jpg'))]
    cards = []
    for i, (key, zone, title, text) in enumerate(items):
        iw, ih = Image.open(os.path.join(FINAL, key + '.jpg')).size
        cards.append(f'''
  <section class="shot" id="{key.replace('_', '-')}">
    <figure><img src="renders/{key}.jpg" alt="{title}" width="{iw}" height="{ih}" loading="{'eager' if i < 2 else 'lazy'}"></figure>
    <div class="cap">
      <div class="meta"><span class="zone">{zone}</span><span class="fig">{FIGS.get(key, '')}</span></div>
      <div class="txt"><h2>{title}</h2><p>{text}</p></div>
    </div>
  </section>''')
    html = f'''<title>Ahmed's House Renders</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gloock&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
/* Layout: a single gallery column, image first, caption set as a two-part legend like a drawing title block */
:root{{
  --bg:#EDE7DD; --surface:#F6F2EB; --ink:#2A241E; --muted:#6F6458; --rule:#D6CCBD; --bronze:#8A6A4A;
  --display:'Gloock', 'Times New Roman', serif; --body:'Hanken Grotesk', system-ui, sans-serif; --mono:'IBM Plex Mono', ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#1D1915;--surface:#26211C;--ink:#EEE6DA;--muted:#A99B8A;--rule:#3A322A;--bronze:#C49A6C;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#1D1915;--surface:#26211C;--ink:#EEE6DA;--muted:#A99B8A;--rule:#3A322A;--bronze:#C49A6C;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font:16px/1.6 var(--body);margin:0;padding-inline:16px}}
.wrap{{max-width:1180px;margin:0 auto;padding-block:48px 72px}}
header{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:28px 48px;align-items:end;padding-bottom:28px;border-bottom:1px solid var(--rule)}}
.kicker{{font:12px/1.4 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--bronze);margin:0 0 14px}}
h1{{font:400 clamp(40px,6.4vw,74px)/1.02 var(--display);margin:0;text-wrap:balance;letter-spacing:-.01em}}
.lead{{margin:0;color:var(--muted);max-width:60ch}}
.materials{{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:8px 18px;margin:6px 0 0;padding:0;list-style:none;font-size:13px;color:var(--muted)}}
.materials li{{display:flex;align-items:center;gap:8px}}
.materials i{{width:14px;height:14px;border-radius:3px;border:1px solid var(--rule);display:inline-block}}
.shot{{margin-top:56px}}
.shot figure{{margin:0;background:var(--surface);border-radius:4px;overflow:hidden}}
.shot img{{display:block;width:100%;height:auto;max-width:100%}}
.cap{{display:grid;grid-template-columns:220px minmax(0,1fr);gap:8px 32px;padding-top:16px}}
.meta{{display:flex;flex-direction:column;gap:4px;padding-top:6px}}
.zone{{font:12px/1.4 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--bronze)}}
.fig{{font:12px/1.5 var(--mono);color:var(--muted)}}
.txt{{min-width:0}}
h2{{font:400 28px/1.15 var(--display);margin:0 0 6px;text-wrap:balance}}
.txt p{{margin:0;color:var(--muted);max-width:68ch}}
footer{{margin-top:64px;padding-top:18px;border-top:1px solid var(--rule);font-size:13px;color:var(--muted);max-width:80ch}}
@media (max-width:760px){{header{{grid-template-columns:1fr}}.cap{{grid-template-columns:1fr}}.meta{{flex-direction:row;flex-wrap:wrap;gap:4px 14px;padding:0}}.shot{{margin-top:40px}}}}
</style>
<div class="wrap">
<header>
  <div>
    <p class="kicker">Ahmed's House · Rev D · 171.2 m² courtyard house</p>
    <h1>Warm minimal, built around one courtyard.</h1>
  </div>
  <p class="lead">Few materials, used everywhere, so the house reads as one calm piece. Lime plaster walls, oak underfoot, travertine where water and feet meet, bronze where hands touch. Warm light hidden in coves, soft bouclé and linen, and something green in every room.</p>
  <ul class="materials" aria-label="Material palette">
    <li><i style="background:#ECE5DA"></i>Lime plaster</li><li><i style="background:#D6BC98"></i>Light oak</li><li><i style="background:#DFCFB4"></i>Travertine</li>
    <li><i style="background:#4D3B2D"></i>Smoked oak</li><li><i style="background:#8E6E4E"></i>Bronze</li><li><i style="background:#D2C4AE"></i>Linen &amp; bouclé</li>
    <li><i style="background:#7C7A5A"></i>Olive</li><li><i style="background:#B66A48"></i>Terracotta</li>
  </ul>
</header>
<main>{"".join(cards)}
</main>
<footer>Rendered with physically based light in Blender Cycles, built from the Rev D plans: walls, glazing, rooflights, the courtyard and room sizes follow the drawings. Furniture, finishes and styling are design proposals. Compass orientation follows the north arrow on the plan sheet and should be confirmed on site.</footer>
</div>'''
    open(out_html, 'w').write(html)
    return len(items)

if __name__ == '__main__':
    print(build(sys.argv[1]))
