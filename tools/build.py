#!/usr/bin/env python3
"""Собирает сайт Silk Road из tools/content.py: английская версия в site/, русская в site/ru/.

Запуск из корня проекта:  python3 tools/build.py
Страницы: index, catalog, about, contacts, credits и objects/<slug>.html на каждом языке.
Общие файлы (styles.css, app.js, catalog.js, contacts.js, gallery.js, img/) лежат только в site/.
"""
import html, json, math, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from content import CITIES, PLACES, UI

SITE = Path(__file__).resolve().parent.parent / "site"
credits = json.loads((SITE / "img" / "credits.json").read_text())
e = html.escape
MAPLIBRE = "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl"


def shots(p):
    """Список фото объекта: главное первым."""
    if p["kind"] == "object":
        return []
    n = p.get("gallery", 1)
    name = lambda i: f"img/{p['slug']}.jpg" if i == 1 else f"img/{p['slug']}-{i}.jpg"
    return [name(i) for i in p.get("order", range(1, n + 1))] + p.get("extra", [])


def meters(a, b):
    k = math.pi / 180
    x = (b["lng"] - a["lng"]) * k * math.cos((a["lat"] + b["lat"]) / 2 * k)
    y = (b["lat"] - a["lat"]) * k
    return 6371000 * math.hypot(x, y)


def facts(p, t):
    """Факты объекта + расстояние до ближайшего ориентира (по прямой, из координат)."""
    out = list(p[t["lang"]]["facts"])
    if p["kind"] == "object":
        marks = [q for q in PLACES if q["kind"] == "landmark" and q["city"] == p["city"]]
        q = min(marks, key=lambda q: meters(p, q))
        out.append((t["near"], f"{q[t['lang']]['name']}, {round(meters(p, q), -1):.0f} {t['m']}"))
    return out


def dl(items, cls=""):
    return f'<dl{cls}>' + "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in items) + "</dl>"


def shell(t, path, title, body, scripts="", head="", desc="", robots=""):
    """Общая обёртка. path — путь страницы от корня языка, например 'objects/ark.html'."""
    depth = path.count("/") + (1 if t["lang"] == "ru" else 0)
    asset = "../" * depth                      # до site/
    home = "../" * path.count("/")             # до корня своего языка
    other = ("" if t["lang"] == "ru" else "ru/")
    other_url = ("../" * depth) + other + path.replace("index.html", "")
    def url(href):
        if href.startswith("#"):
            return href if path == "index.html" else (home or "./") + href
        return home + href if href else (home or "./")
    links = "".join(f'<li><a href="{url(href)}"{" aria-current=page" if href and href == path else ""}>{e(name)}</a></li>'
                    for name, href in t["nav"])
    return f"""<!doctype html>
<html lang="{t['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
{f'<meta name="description" content="{e(desc)}">' if desc else ''}
{robots}<link rel="alternate" hreflang="{t['other']}" href="{other_url or './'}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
{head}<link rel="stylesheet" href="{asset}styles.css">
</head>
<body>
<header class="nav">
  <div class="container nav__in">
    <a class="nav__mark" href="{home or './'}">Silk Road</a>
    <ul class="nav__links">{links}</ul>
    <a class="nav__lang" href="{other_url or './'}" hreflang="{t['other']}" lang="{t['other']}" aria-label="{t['other_label']}">{t['short']}</a>
    <details class="nav__menu"><summary>{t['menu']}</summary><ul>{links}</ul></details>
    <a class="btn btn--primary" href="{home}contacts.html#form">{e(t['cta'])}</a>
  </div>
</header>
{body}
<footer class="foot">
  <div class="container foot__in">
    <div class="foot__brand"><p class="foot__mark">Silk Road</p><p class="foot__line">{t['brand_line']}</p></div>
    <ul class="foot__links">{links}</ul>
    <ul class="foot__meta"><li><a href="{other_url or './'}" hreflang="{t['other']}" lang="{t['other']}">{t['other_label']}</a></li><li><a href="{home}credits.html">{t['credits']}</a></li></ul>
  </div>
</footer>
<script>window.SR = {{ lang: "{t['lang']}", more: "{t['more']}", noPhoto: "{t['no_photo']}", asset: "{asset}" }};</script>
{scripts}</body>
</html>
"""


def band(t, home, asset):
    return f"""<section class="band" style="--band-photo: url('{asset}img/registan-3.jpg')">
  <div class="container band__in">
    <h2>{e(t['band_h'])}</h2>
    <p class="band__line">Silk Road — {t['brand_line']}.</p>
    <a class="btn btn--light" href="{home}contacts.html#form">{e(t['cta'])}</a>
  </div>
</section>"""


def seg_cities(t, cls, with_all=False):
    b = (f'<button type="button" class="seg__b {cls}" data-city="all" aria-pressed="true">{t["all"]}</button>' if with_all else "")
    b += "".join(f'<button type="button" class="seg__b {cls}" data-city="{k}" aria-pressed="{str(not with_all and k == "bukhara").lower()}">{c[t["lang"]]}</button>'
                 for k, c in CITIES.items())
    return f'<div class="seg" role="group" aria-label="{t["cities_label"]}">{b}</div>'


def seg_kinds(t):
    return (f'<div class="seg" role="group" aria-label="{t["list_h"]}">'
            f'<button type="button" class="seg__b" data-filter="all" aria-pressed="true">{t["all"]}</button>'
            f'<button type="button" class="seg__b" data-filter="object" aria-pressed="false">{t["objects"]}</button>'
            f'<button type="button" class="seg__b" data-filter="landmark" aria-pressed="false">{t["landmarks"]}</button></div>')


def build(t):
    lang = t["lang"]
    root = SITE if lang == "en" else SITE / "ru"
    a0 = "" if lang == "en" else "../"           # путь до общих файлов со страниц корня языка
    (root / "objects").mkdir(parents=True, exist_ok=True)
    for old in (root / "objects").glob("*.html"):
        old.unlink()

    # ---------- главная ----------
    rows, tiles = "", ""
    for p in PLACES:
        d, ph = p[lang], shots(p)
        city = CITIES[p["city"]][lang]
        kind = t["kind"][p["kind"]]
        attrs = (f'data-slug="{p["slug"]}" data-pin data-kind="{p["kind"]}" data-city="{p["city"]}" '
                 f'data-lng="{p["lng"]}" data-lat="{p["lat"]}"' + (f' data-photo="{a0}{ph[0]}"' if ph else ""))
        rows += (f'      <li class="row" {attrs}>\n        <span class="row__kind">{kind} · {city}</span>\n'
                 f'        <h3><a class="row__go" href="objects/{p["slug"]}.html">{e(d["name"])}</a></h3>\n'
                 f'        {dl(facts(p, t))}\n        <button type="button" class="row__map">{t["on_map"]}</button>\n      </li>\n')
        pic = (f'<div class="tile__photo" data-slot="photo"><img src="{a0}{ph[0]}" alt="{e(d["name"])}" loading="lazy"></div>' if ph
               else f'<div class="tile__photo tile__photo--empty">{t["no_photo"]}</div>')
        tiles += (f'      <li class="tile" data-kind="{p["kind"]}" data-city="{p["city"]}">\n        {pic}\n        <div class="tile__body">\n'
                  f'          <span class="tile__kind">{kind} · {city}</span>\n'
                  f'          <h2><a class="tile__go" href="objects/{p["slug"]}.html">{e(d["name"])}</a></h2>\n'
                  f'          {dl(facts(p, t))}\n'
                  f'          <a class="tile__map" href="./#pin={p["slug"]}">{t["on_map"]}</a>\n        </div>\n      </li>\n')

    services = "".join(f'<li><h3>{e(h)}</h3><p>{e(x)}</p></li>' for h, x in t["services"])
    steps = "".join(f'<li><h3>{e(h)}</h3><p>{e(x)}</p></li>' for h, x in t["steps"])
    cities = "".join(
        f'<li class="city"><button type="button" class="city__go" data-city="{k}">'
        f'<span class="city__photo" data-slot="photo"><img src="{a0}{c["photo"]}" alt="" loading="lazy"></span>'
        f'<span class="city__cap"><span class="city__name">{c[lang]}</span><span class="city__map">{t["on_map"]}</span></span></button><p>{e(t["city_text"][k])}</p></li>'
        for k, c in CITIES.items())
    cities_js = json.dumps({k: {x: c[x] for x in ("flat", "tilt", "zoom", "bounds")} for k, c in CITIES.items()})
    index = f"""<main id="top">
<section class="hero" id="hero" aria-labelledby="h-hero">
  <div class="hero__stage">
    <div class="hero__copy" id="hero-copy">
      <p class="hero__eyebrow">Silk Road — {t['brand_line']}</p>
      <h1 id="h-hero">{e(t['h1'])}</h1>
      <p class="lead">{e(t['lead'])}</p>
      <div class="hero__actions">
        {seg_cities(t, 'city-b')}
        <a class="btn btn--primary" href="#index">{e(t['see'])}</a>
      </div>
    </div>
    <div class="hero__map" id="map" role="application" aria-label="{e(t['map_label'])}">
      <noscript><p class="hero__nojs">{e(t['nojs'])}</p></noscript>
    </div>
  </div>
</section>

<section class="sec" id="services" aria-labelledby="h-services">
  <div class="container services">
    <div class="services__head">
      <h2 id="h-services">{e(t['services_h'])}</h2>
      <p class="services__lead">{e(t['services_lead'])}</p>
      <a class="btn btn--primary" href="contacts.html#form">{e(t['cta'])}</a>
    </div>
    <ul class="services__list">{services}</ul>
  </div>
</section>

<section class="sec sec--sand" aria-labelledby="h-steps">
  <div class="container">
    <h2 id="h-steps">{e(t['steps_h'])}</h2>
    <ol class="steps">{steps}</ol>
  </div>
</section>

<section class="sec" aria-labelledby="h-cities">
  <div class="container">
    <h2 id="h-cities">{e(t['cities_h'])}</h2>
    <ul class="cities">{cities}</ul>
  </div>
</section>

<section class="index" id="index" aria-labelledby="h-index">
  <div class="container">
    <div class="index__head">
      <h2 id="h-index">{e(t['list_h'])}</h2>
      <div class="page__tools">
        <form class="field-search" role="search" id="search"><label class="visually-hidden" for="q">{t['search']}</label><input id="q" type="search" placeholder="{t['search']}" autocomplete="off"></form>
        {seg_cities(t, 'city-b')}
        {seg_kinds(t)}
      </div>
    </div>
    <!-- Метки карты строятся из этих строк. Правьте данные в tools/content.py, не здесь. -->
    <ul class="rows" id="rows">
{rows}    </ul>
    <p class="rows__empty" id="rows-empty" hidden>{t['empty']}</p>
  </div>
</section>
</main>
""" + band(t, "", a0)
    (root / "index.html").write_text(shell(t, "index.html", t["title"], index, desc=t["desc"],
        head=f'<link rel="stylesheet" href="{MAPLIBRE}.css">\n',
        scripts=f'<script>window.SR_CITIES = {cities_js};</script>\n<script src="{MAPLIBRE}.js"></script>\n<script src="{a0}app.js"></script>\n'))

    # ---------- страницы объектов ----------
    for p in PLACES:
        d, ph = p[lang], shots(p)
        o = "../" + a0
        if len(ph) > 1:
            thumbs = '<div class="thumbs">' + "".join(
                f'<a href="{o}{g}"{" aria-current" if i == 0 else ""}><img src="{o}{g}" alt="{e(d["name"])}, {t["photo"].lower()} {i + 1}" loading="lazy"></a>'
                for i, g in enumerate(ph)) + "</div>"
        elif not ph:
            thumbs = '<div class="thumbs">' + f'<span class="thumbs__empty">{t["photo"]}</span>' * 4 + "</div>"
        else:
            thumbs = ""
        photo = (f'<div class="obj__photo" data-slot="photo" id="photo"><img src="{o}{ph[0]}" alt="{e(d["name"])}"></div>' if ph
                 else f'<div class="obj__photo obj__photo--empty" id="photo">{t["no_photo"]}</div>')
        desc = (f'<p class="obj__desc">{e(d["desc"])}</p>' if d["desc"] else f'<p class="obj__desc obj__desc--empty">{t["no_desc"]}</p>')
        info = [(t["city"], CITIES[p["city"]][lang])] + facts(p, t) + [(t["coords"], f'{p["lat"]}, {p["lng"]}')]
        body = f"""<main class="obj">
  <div class="container obj__in">
    <div class="obj__media">{photo}{thumbs}</div>
    <div class="obj__info">
      <p class="obj__kind">{t['kind'][p['kind']]}</p>
      <h1>{e(d['name'])}</h1>
      {desc}
      {dl(info, ' class="facts"')}
      <div class="obj__actions">
        <a class="btn btn--primary" href="../#pin={p['slug']}">{t['show_map']}</a>
        <a class="btn" href="../catalog.html">{t['all_props']}</a>
      </div>
    </div>
  </div>
</main>"""
        (root / "objects" / f"{p['slug']}.html").write_text(shell(t, f"objects/{p['slug']}.html", f"{d['name']} | Silk Road", body,
            desc=d["desc"][:160], scripts=f'<script src="{o}gallery.js"></script>\n'))

    # ---------- каталог ----------
    catalog = f"""<main class="page">
  <div class="container">
    <div class="page__head page__head--row">
      <h1>{t['catalog_h']}</h1>
      <div class="page__tools">
        <form class="field-search" role="search" id="search"><label class="visually-hidden" for="q">{t['search']}</label><input id="q" type="search" placeholder="{t['search']}" autocomplete="off"></form>
        {seg_cities(t, 'city-f', with_all=True)}
        {seg_kinds(t)}
      </div>
    </div>
    <ul class="tiles" id="tiles">
{tiles}    </ul>
    <p class="rows__empty" id="tiles-empty" hidden>{t['empty']}</p>
  </div>
</main>
""" + band(t, "", a0)
    (root / "catalog.html").write_text(shell(t, "catalog.html", t["catalog_title"], catalog, desc=t["catalog_desc"],
                                             scripts=f'<script src="{a0}catalog.js"></script>\n'))

    # ---------- о компании ----------
    paras = "".join(f"<p>{e(x)}</p>" for x in t["about_p"])
    about = f"""<main class="page">
  <div class="container">
    <div class="about">
      <div class="about__text">
        <h1>{t['about_h']}</h1>
        <p class="lead">{e(t['about_lead'])}</p>
        {paras}
      </div>
      <div class="about__photo">{t['about_photo']}</div>
    </div>
    <section class="company" aria-labelledby="h-company">
      <h2 id="h-company">{t['company_h']}</h2>
      {dl([(s, t['tbc']) for s in t['stats']], ' class="facts"')}
    </section>
    <section class="how" aria-labelledby="h-how">
      <h2 id="h-how">{e(t['steps_h'])}</h2>
      <ol class="steps">{steps}</ol>
    </section>
  </div>
</main>
""" + band(t, "", a0)
    (root / "about.html").write_text(shell(t, "about.html", t["about_title"], about, desc=t["about_lead"]))

    # ---------- контакты ----------
    city_opts = f'<option value="">{t["f_city_any"]}</option>' + "".join(f"<option>{c[lang]}</option>" for c in CITIES.values())
    needs = "".join(f"<option>{x}</option>" for x in t["f_needs"])
    contacts = f"""<main class="page">
  <div class="container">
    <div class="contacts">
      <div class="contacts__info">
        <h1>{t['contact_h']}</h1>
        {dl([(s, t['tbc']) for s in t['contact_facts']], ' class="facts"')}
      </div>
      <form class="form" id="form" novalidate data-err="{e(t['f_err'])}" data-ok="{e(t['f_ok'])}">
        <h2>{t['form_h']}</h2>
        <label class="form__f"><span>{t['f_name']}</span><input type="text" name="name" autocomplete="name" required></label>
        <label class="form__f"><span>{t['f_email']}</span><input type="email" name="email" autocomplete="email"></label>
        <label class="form__f"><span>{t['f_phone']}</span><input type="tel" name="phone" autocomplete="tel" inputmode="tel"></label>
        <label class="form__f"><span>{t['f_city']}</span><select name="city">{city_opts}</select></label>
        <label class="form__f"><span>{t['f_need']}</span><select name="need">{needs}</select></label>
        <label class="form__f"><span>{t['f_msg']}</span><textarea name="note" rows="3"></textarea></label>
        <button type="submit" class="btn btn--primary">{t['f_send']}</button>
        <p class="form__note" id="form-note" role="status" hidden></p>
      </form>
    </div>
  </div>
</main>"""
    (root / "contacts.html").write_text(shell(t, "contacts.html", t["contact_title"], contacts, desc=t["about_lead"],
                                              scripts=f'<script src="{a0}contacts.js"></script>\n'))

    # ---------- авторы фото ----------
    names = {p["slug"]: p[lang]["name"] for p in PLACES}
    rows = ""
    for key, c in credits.items():
        owner = names.get(key) or names.get(key.rsplit("-", 1)[0]) or key
        rows += (f'<li class="row"><span class="row__kind">{e(owner)}</span><h3>{e(c["author"])}</h3>'
                 f'<dl><div><dt>{t["license"]}</dt><dd>{e(c["license"])}</dd></div>'
                 f'<div><dt>{t["source"]}</dt><dd><a href="{e(c["page"])}">Wikimedia Commons</a></dd></div></dl></li>\n')
    cr = f"""<main><section class="index"><div class="container">
<div class="index__head"><h1>{t['credits_h']}</h1></div>
<ul class="rows rows--credits">
{rows}</ul>
<p class="rows__empty">{t['credits_map']}</p>
</div></section></main>"""
    (root / "credits.html").write_text(shell(t, "credits.html", t["credits_title"], cr, robots='<meta name="robots" content="noindex">\n'))
    return len(PLACES)


# фото без строки в credits.json не публикуем
missing = [g for p in PLACES for g in shots(p) if Path(g).stem not in credits or not (SITE / g).exists()]
if missing:
    sys.exit(f"нет фото или автора: {missing}")
for t in UI.values():
    n = build(t)
    print(f"{t['lang']}: {n} объектов и ориентиров + index, catalog, about, contacts, credits")
