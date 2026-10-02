"""Assemble the Berlin Cafe site from src/ into site/."""
import html, os, re, sys
sys.path.insert(0, "src")
import menu_data as M

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
read = lambda p: open(p, encoding="utf-8").read()
esc = html.escape

PH = "/tmp/ph/package/assets/regular/"
def icon(name):
    svg = read(PH + name + ".svg")
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    return f'<svg class="icon" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true" focusable="false">{body}</svg>'

ICONS = {
    "ICON_ARROW": icon("arrow-right"), "ICON_UPRIGHT": icon("arrow-up-right"), "ICON_LEFT": icon("arrow-left"),
    "ICON_LIST": icon("list"), "ICON_X": icon("x"), "ICON_CLOCK": icon("clock"), "ICON_PIN": icon("map-pin"),
    "ICON_IG": icon("instagram-logo"), "ICON_FB": icon("facebook-logo"),
}

def fill_icons(s):
    for k, v in ICONS.items():
        s = s.replace("{{" + k + "}}", v)
    return s

FOOTER = """<footer class="footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="brand" href="./"><img src="img/logo-160.webp" alt="" width="56" height="56"><span>Berlin<small>Café &amp; Bistro</small></span></a>
        <p style="margin-top:16px;max-width:34ch">Specialty coffee, organic teas, German bakes and an all-day bistro in Mirpur, Dhaka. Est. 2026.</p>
      </div>
      <div>
        <h3>Visit</h3>
        <ul>
          <li>Mirpur, Dhaka</li>
          <li>9:00 AM to 11:00 PM</li>
          <li><a href="https://maps.app.goo.gl/bYZZ1aU8XZ1qJz4E9" target="_blank" rel="noopener">Get directions</a></li>
        </ul>
      </div>
      <div>
        <h3>Follow</h3>
        <ul>
          <li><a href="https://www.instagram.com/berlincafe_bistro" target="_blank" rel="noopener">Instagram</a></li>
          <li><a href="https://www.facebook.com/profile.php?id=61591191917873" target="_blank" rel="noopener">Facebook</a></li>
          <li><a href="menu.html">Full menu</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-base"><span>&copy; 2026 Berlin Café &amp; Bistro</span><span>Brewed for the restless</span></div>
  </div>
</footer>"""

COMMON = read("src/common.css")

# ---------------- home ----------------
sig_cards = []
for name, desc, price, img in M.SIGNATURES:
    shown = ("from " + price) if name.startswith("Froccinos") else price
    sig_cards.append(f"""        <a class="dish glass" href="menu.html">
          <div class="ph"><img src="img/{img}.webp" alt="{esc(name)}" loading="lazy"></div>
          <div class="meta"><h3>{esc(name)}</h3><span class="price">{shown}</span><p>{esc(desc)}</p></div>
        </a>""")

index = read("src/index.html")
index = index.replace("/*COMMON_CSS*/", COMMON)
index = index.replace("{{SIGNATURES}}", "\n".join(sig_cards))
index = index.replace("{{FOOTER}}", FOOTER)
index = index.replace("/*NAV_JS*/", read("src/nav.js"))
index = index.replace("/*HERO_JS*/", read("src/hero.js"))
index = index.replace("/*PAGE_JS*/", read("src/page.js"))
index = fill_icons(index)

# ---------------- menu ----------------
def flourish():
    return '<div class="flourish" aria-hidden="true"><span></span></div>'

def sec(id_, title, sub, inner):
    return f"""      <section class="sec" id="{id_}" aria-labelledby="{id_}-t">
        <div class="sec-title">{flourish()}<h2 id="{id_}-t">{esc(title)}</h2><p class="sub">{esc(sub)}</p></div>
{inner}
      </section>"""

def price_cell(v):
    return f"{v}/-" if isinstance(v, int) else esc(str(v))

def item(name, desc, price, img=None, tag=None):
    thumb = f'<div class="thumb"><img src="img/{img}.webp" alt="" loading="lazy"></div>' if img else ""
    tag_html = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    ds = f'<p class="ds">{esc(desc)}</p>' if desc else ""
    cls = "item has-ph" if img else "item"
    return f'<div class="{cls}">{thumb}<div class="nm"><b>{esc(name)}</b>{tag_html}</div><span class="pr">{price_cell(price)}</span>{ds}</div>'

parts = []

# Chef's picks: the framed layout the owner loved
plates = "\n".join(f"""          <figure class="plate">
            <div class="frame rv"><div class="ph"><img src="img/{img}.webp" alt="{esc(n)}" loading="lazy"></div></div>
            <h3>- {esc(n)} -</h3>
            <p>{esc(d)}</p>
            <span class="px">{p}/-</span>
          </figure>""" for n, d, p, img in M.FEATURED)
parts.append(sec("picks", "Chef's picks", "From the bistro kitchen", f'        <div class="plates">\n{plates}\n        </div>'))

# Coffee
groups = []
for g, rows in M.COFFEE.items():
    rs = []
    for n, reg, lg in rows:
        r = f"{reg}" if reg else '<span class="na">-</span>'
        rs.append(f'<div class="item"><div class="nm"><b>{esc(n)}</b></div><span class="pr two"><span>{r}</span><span>{lg}</span></span></div>')
    groups.append(f"""          <div class="group"><h3>{esc(g)}<span class="cols-lbl"><span>Regular</span><span>Large</span></span></h3>{''.join(rs)}<p class="note">{esc(M.COFFEE_NOTES[g])}</p></div>""")
ref = "".join(item(n, d, p if p == "MRP" else int(p)) for n, d, p in M.REFRESHERS)
wat = "".join(item(n, d, "At MRP") for n, d, p in M.WATER)
groups.append(f'          <div class="group"><h3>Refreshers</h3>{ref}<h3 style="margin-top:26px">Drinks</h3>{wat}</div>')
band = """        <div class="photo-band">
          <figure class="rv"><img src="img/latte.webp" alt="Cafe latte with latte art" loading="lazy"></figure>
          <figure class="rv"><img src="img/shakes.webp" alt="Chocolate froccinos" loading="lazy"></figure>
          <figure class="rv"><img src="img/cake-iced.webp" alt="Iced drink with chocolate cake" loading="lazy"></figure>
        </div>"""
parts.append(sec("coffee", "The Coffee Chapter", "Espresso classics, froccinos, iced and refreshers", band + '\n        <div class="groups">\n' + "\n".join(groups) + "\n        </div>"))

# Teas
teas = "\n".join(f'          <div class="tea rv"><h3>{esc(n)}</h3><p>{esc(d)}</p></div>' for n, d in M.TEAS)
parts.append(sec("teas", "Organic Blended Teas", "Six house blends", f'        <div class="teas">\n{teas}\n        </div>\n        <p class="tea-foot"><span>{M.TEA_PRICE}/- each</span><span>{esc(M.TEA_ADDON)}</span></p>'))

# Bakery
bg = []
for g, rows in M.BAKERY.items():
    bg.append(f'          <div class="group"><h3>{esc(g)}</h3>' + "".join(item(n, "", p) for n, p in rows) + "</div>")
bake_band = """        <div class="photo-band">
          <figure class="rv"><img src="img/croissant.webp" alt="Croissant sandwich" loading="lazy"></figure>
          <figure class="rv"><img src="img/cake-iced.webp" alt="Chocolate cake slice" loading="lazy"></figure>
          <figure class="rv"><img src="img/shakes.webp" alt="Shakes with a cookie" loading="lazy"></figure>
        </div>"""
parts.append(sec("bakery", "Die Bäckerei", "Brownies, cookies, pastries, donuts and croissants",
                 bake_band + '\n        <div class="groups">\n' + "\n".join(bg[:2]) + "\n" + bg[2] + "\n        </div>"))

# Kitchen sections
def food(id_, title, sub, rows, one=False):
    half = (len(rows) + 1) // 2
    if one:
        inner = '        <div class="groups one"><div class="group">' + "".join(item(n, d, p, img) for n, d, p, img in rows) + "</div></div>"
    else:
        a = "".join(item(n, d, p, img) for n, d, p, img in rows[:half])
        b = "".join(item(n, d, p, img) for n, d, p, img in rows[half:])
        inner = f'        <div class="groups"><div class="group">{a}</div><div class="group">{b}</div></div>'
    return sec(id_, title, sub, inner)

parts.append(food("appetizers", "Appetizer", "Small plates and sharing", M.APPETIZERS))
parts.append(food("sandwiches", "Sandwich & Wraps", "Served with fries or chips", M.SANDWICHES))
parts.append(food("salads", "Salad", "Fresh and generous", M.SALADS, one=True))
parts.append(food("breakfast", "Breakfast", "Morning plates", M.BREAKFAST, one=True))

menu = read("src/menu.html")
menu = menu.replace("/*COMMON_CSS*/", COMMON)
menu = menu.replace("{{SECTIONS}}", "\n".join(parts))
menu = menu.replace("{{FOOTER}}", FOOTER)
menu = menu.replace("/*NAV_JS*/", read("src/nav.js"))
menu = fill_icons(menu)

os.makedirs("site", exist_ok=True)
open("site/index.html", "w", encoding="utf-8").write(index)
open("site/menu.html", "w", encoding="utf-8").write(menu)
# local preview copy of the home page with a document shell (the artifact host adds this itself)
open("site/preview.html", "w", encoding="utf-8").write(
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>'
    + index + "</body></html>")
# standalone static site for regular hosting (Vercel etc.): full documents + images
import shutil
if os.path.isdir("web"): shutil.rmtree("web")
shutil.copytree("site/img", "web/img")
open("web/index.html", "w", encoding="utf-8").write(open("site/preview.html", encoding="utf-8").read())
shutil.copy("site/menu.html", "web/menu.html")
print("built", len(index), len(menu))
for f in ("site/index.html", "site/menu.html"):
    s = read(f)
    left = re.findall(r"\{\{[A-Z_]+\}\}|/\*[A-Z_]+\*/", s)
    if left: print("UNFILLED", f, left)
    if "—" in s or "–" in s: print("DASH FOUND", f)
