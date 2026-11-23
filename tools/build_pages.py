#!/usr/bin/env python3
"""Собирает из строк списка в site/index.html страницы объектов site/objects/<slug>.html,
каталог catalog.html, а также about.html, contacts.html и credits.html с общей шапкой и подвалом.

Запуск из корня проекта:  python3 tools/build_pages.py
Одна строка <li class="row" data-pin ...> = одна метка на карте = одна страница.
Описание объекта: <p class="row__desc" hidden>текст</p> внутри строки.
Галерея: data-gallery="img/a.jpg,img/b.jpg" у строки (главное фото — data-photo).
Авторы фото берутся из site/img/credits.json и выводятся только на site/credits.html.
"""
import html, json, re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
index = (SITE / "index.html").read_text()
credits = json.loads((SITE / "img" / "credits.json").read_text())

ROW = re.compile(r'<li class="row"(?P<attrs>[^>]*)>(?P<body>.*?)</li>', re.S)
attr = lambda attrs, name: (re.search(rf'{name}="([^"]*)"', attrs) or [None, ""])[1]
count = {"object": 0}

def upgrade(m):
    """Добавляет строке data-slug, ссылку на страницу и кнопку «На карте» (повторный запуск ничего не меняет)."""
    attrs, body = m["attrs"], m["body"]
    kind, photo, slug = attr(attrs, "data-kind"), attr(attrs, "data-photo"), attr(attrs, "data-slug")
    if kind == "object":
        count["object"] += 1
    if not slug:
        slug = Path(photo).stem if photo else f"obekt-{count['object']}"
        attrs = f' data-slug="{slug}"' + attrs
    body = re.sub(r'<button type="button" class="row__go">(.*?)</button>',
                  rf'<a class="row__go" href="objects/{slug}.html">\1</a>', body)
    if "row__map" not in body:
        body = body.rstrip() + '\n        <button type="button" class="row__map">На карте</button>\n      '
    return f'<li class="row"{attrs}>{body}</li>'

index = ROW.sub(upgrade, index)
(SITE / "index.html").write_text(index)

MENU = [("Карта", ""), ("Объекты", "catalog.html"), ("О компании", "about.html"), ("Контакты", "contacts.html")]

def shell(title, body, root="", current="", scripts="", head="", desc=""):
    """Общая шапка и подвал всех внутренних страниц. root — путь до корня сайта ("" или "../")."""
    links = "".join(f'<li><a href="{root}{href or "./"}"{" aria-current=page" if href == current else ""}>{name}</a></li>'
                    for name, href in MENU)
    meta = f'<meta name="description" content="{desc}">\n' if desc else ""
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{meta}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
{head}<link rel="stylesheet" href="{root}styles.css">
</head>
<body>
<header class="nav">
  <div class="container nav__in">
    <a class="nav__mark" href="{root or "./"}">Palm</a>
    <ul class="nav__links">{links}</ul>
    <details class="nav__menu"><summary>Меню</summary><ul>{links}</ul></details>
    <a class="btn btn--primary" href="{root}contacts.html#show">Записаться на показ</a>
  </div>
</header>
{body}
<footer class="foot">
  <div class="container foot__in">
    <p class="foot__mark">Palm</p>
    <ul class="foot__links">{links}<li><a href="{root}credits.html">Авторы фото</a></li></ul>
  </div>
</footer>
{scripts}</body>
</html>
"""

BAND = """<section class="band">
  <div class="container band__in">
    <h2>Покажем любой дом на месте</h2>
    <a class="btn btn--light" href="{root}contacts.html#show">Записаться на показ</a>
  </div>
</section>"""

PAGE = """<main class="obj">
  <div class="container obj__in">
    <div class="obj__media">
      <div class="obj__photo{empty}"{slot} id="photo">{photo}</div>
{thumbs}    </div>
    <div class="obj__info">
      <p class="obj__kind">{kind}</p>
      <h1>{name}</h1>
{desc}      <dl class="facts">
{facts}      </dl>
      <div class="obj__actions">
        <a class="btn btn--primary" href="../#pin={slug}">Показать на карте</a>
        <a class="btn" href="../catalog.html">Все объекты</a>
      </div>
    </div>
  </div>
</main>"""

out = SITE / "objects"
out.mkdir(exist_ok=True)
for old in out.glob("*.html"):
    old.unlink()
n = 0
tiles, options = "", ""
for m in ROW.finditer(index):
    attrs, body = m["attrs"], m["body"]
    slug, photo, kind = attr(attrs, "data-slug"), attr(attrs, "data-photo"), attr(attrs, "data-kind")
    name = re.search(r'class="row__go"[^>]*>(.*?)</a>', body, re.S)[1].strip()
    label = re.search(r'class="row__kind">(.*?)</span>', body, re.S)[1].strip()
    facts = "".join(f"        <div><dt>{dt}</dt><dd>{dd}</dd></div>\n"
                    for dt, dd in re.findall(r"<dt>(.*?)</dt><dd[^>]*>(.*?)</dd>", body, re.S))
    facts += f'        <div><dt>Координаты</dt><dd>{attr(attrs, "data-lat")}, {attr(attrs, "data-lng")}</dd></div>\n'
    d = re.search(r'class="row__desc"[^>]*>(.*?)</p>', body, re.S)
    desc = (f'      <p class="obj__desc">{d[1].strip()}</p>\n' if d and d[1].strip()
            else '      <p class="obj__desc obj__desc--empty">Здесь будет описание объекта</p>\n')
    shots = ([photo] if photo else []) + [g for g in attr(attrs, "data-gallery").split(",") if g]
    if len(shots) > 1:
        thumbs = '      <div class="thumbs">\n' + "".join(
            f'        <a href="../{g}"{" aria-current" if i == 0 else ""}><img src="../{g}" alt="{html.escape(name)}, фото {i + 1}" loading="lazy"></a>\n'
            for i, g in enumerate(shots)) + "      </div>\n"
    elif not shots:
        thumbs = '      <div class="thumbs">\n' + '        <span class="thumbs__empty">Фото</span>\n' * 4 + "      </div>\n"
    else:
        thumbs = ""
    page = PAGE.format(
        name=name, kind=label, slug=slug, facts=facts, desc=desc, thumbs=thumbs,
        empty="" if photo else " obj__photo--empty", slot=' data-slot="photo"' if photo else "",
        photo=f'<img src="../{photo}" alt="{html.escape(name)}">' if photo else "Здесь будет фото объекта")
    (out / f"{slug}.html").write_text(shell(f"{name} | Palm", page, root="../", current="catalog.html",
                                             scripts='<script src="../gallery.js"></script>\n'))
    pic = (f'<div class="tile__photo" data-slot="photo"><img src="{photo}" alt="{html.escape(name)}" loading="lazy"></div>' if photo
           else '<div class="tile__photo tile__photo--empty">Здесь будет фото объекта</div>')
    short = "".join(f"<div><dt>{dt}</dt><dd>{dd}</dd></div>"
                    for dt, dd in re.findall(r"<dt>(.*?)</dt><dd[^>]*>(.*?)</dd>", body, re.S))
    tiles += (f'      <li class="tile" data-kind="{kind}">\n        {pic}\n        <div class="tile__body">\n'
              f'          <span class="tile__kind">{label}</span>\n'
              f'          <h2><a class="tile__go" href="objects/{slug}.html">{name}</a></h2>\n'
              f'          <dl>{short}</dl>\n'
              f'          <a class="tile__map" href="./#pin={slug}">На карте</a>\n        </div>\n      </li>\n')
    if kind == "object":
        options += f"            <option>{name}</option>\n"
    n += 1

# страница «Авторы фото»: все снимки из credits.json, сгруппированные по объекту
names = {attr(m["attrs"], "data-slug"): re.search(r'class="row__go"[^>]*>(.*?)</a>', m["body"], re.S)[1].strip() for m in ROW.finditer(index)}
rows = ""
for key, c in credits.items():
    owner = names.get(key) or names.get(re.sub(r"-\d+$", "", key), key)
    rows += (f'      <li class="row"><span class="row__kind">{owner}</span><h3>{html.escape(c["author"])}</h3>'
             f'<dl><div><dt>Лицензия</dt><dd>{html.escape(c["license"])}</dd></div>'
             f'<div><dt>Источник</dt><dd><a href="{html.escape(c["page"])}">Wikimedia Commons</a></dd></div></dl></li>\n')
(SITE / "credits.html").write_text(shell("Palm: авторы фото и данные карты", f"""<main>
<section class="index">
  <div class="container">
    <div class="index__head"><h1>Авторы фото</h1></div>
    <ul class="rows rows--credits">
{rows}    </ul>
    <p class="rows__empty">Данные карты: участники <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, тайлы <a href="https://openfreemap.org">OpenFreeMap</a>.</p>
  </div>
</section>
</main>""", head='<meta name="robots" content="noindex">\n'))

# каталог: все строки списка плитками с фото
(SITE / "catalog.html").write_text(shell("Объекты на карте Бухары | Palm", f"""<main class="page">
  <div class="container">
    <div class="page__head page__head--row">
      <h1>Объекты</h1>
      <div class="page__tools">
        <form class="field-search" role="search" id="search">
          <label class="visually-hidden" for="q">Поиск по объектам</label>
          <input id="q" type="search" placeholder="Найти дом или ориентир" autocomplete="off">
        </form>
        <div class="seg" role="group" aria-label="Что показывать">
          <button type="button" class="seg__b" data-filter="all" aria-pressed="true">Всё</button>
          <button type="button" class="seg__b" data-filter="object" aria-pressed="false">Объекты</button>
          <button type="button" class="seg__b" data-filter="landmark" aria-pressed="false">Ориентиры</button>
        </div>
      </div>
    </div>
    <ul class="tiles" id="tiles">
{tiles}    </ul>
    <p class="rows__empty" id="tiles-empty" hidden>Ничего не нашлось. Измените запрос.</p>
  </div>
</main>
""" + BAND.format(root=""), current="catalog.html", scripts='<script src="catalog.js"></script>\n',
    desc="Все объекты и городские ориентиры с карты Бухары: фото, краткие сведения, переход на карту."))

# о компании: текстов от клиента пока нет, вместо фактов стоят пометки
SLOT = "[уточнить]"
(SITE / "about.html").write_text(shell("О компании | Palm", f"""<main class="page">
  <div class="container">
    <div class="about">
      <div class="about__text">
        <h1>О компании</h1>
        <p class="lead slot-text">Здесь будет рассказ о застройщике: кто строит, с какого года работает в Бухаре, какие дома уже сданы.</p>
      </div>
      <div class="about__photo">Здесь будет фото офиса или команды</div>
    </div>
    <dl class="stats">
      <div><dt>Год основания</dt><dd>{SLOT}</dd></div>
      <div><dt>Сдано домов</dt><dd>{SLOT}</dd></div>
      <div><dt>Строится сейчас</dt><dd>{SLOT}</dd></div>
      <div><dt>Лицензия</dt><dd>{SLOT}</dd></div>
    </dl>
    <section class="how" aria-labelledby="h-how">
      <h2 id="h-how">Как выбрать дом на сайте</h2>
      <ol class="how__steps">
        <li><h3>Найдите дом на карте</h3><p>Метки стоят прямо на зданиях. Наведите на метку, и появится карточка с фото и основными сведениями.</p></li>
        <li><h3>Откройте страницу объекта</h3><p>Там галерея, описание, адрес, срок сдачи и цена. Город вокруг виден на той же карте: что рядом, далеко ли до центра.</p></li>
        <li><h3>Запишитесь на показ</h3><p>Оставьте телефон на странице контактов. Менеджер перезвонит и договорится о времени.</p></li>
      </ol>
      <div class="obj__actions">
        <a class="btn btn--primary" href="./">Открыть карту</a>
        <a class="btn" href="catalog.html">Все объекты</a>
      </div>
    </section>
  </div>
</main>
""" + BAND.format(root=""), current="about.html",
    desc="О застройщике Palm и о том, как выбрать дом на 3D-карте Бухары."))

# контакты: данные клиента пока не получены
(SITE / "contacts.html").write_text(shell("Контакты | Palm", f"""<main class="page">
  <div class="container">
    <div class="contacts">
      <div class="contacts__info">
        <h1>Контакты</h1>
        <dl class="facts">
          <div><dt>Телефон отдела продаж</dt><dd>{SLOT}</dd></div>
          <div><dt>Офис в Бухаре</dt><dd>{SLOT}</dd></div>
          <div><dt>Режим работы</dt><dd>{SLOT}</dd></div>
          <div><dt>Почта</dt><dd>{SLOT}</dd></div>
        </dl>
      </div>
      <form class="form" id="show" novalidate>
        <h2>Записаться на показ</h2>
        <label class="form__f"><span>Имя</span><input type="text" name="name" autocomplete="name" required></label>
        <label class="form__f"><span>Телефон</span><input type="tel" name="phone" autocomplete="tel" inputmode="tel" placeholder="+998" required></label>
        <label class="form__f"><span>Объект</span>
          <select name="object">
            <option value="">Пока не выбрал</option>
{options}          </select>
        </label>
        <label class="form__f"><span>Комментарий</span><textarea name="note" rows="3"></textarea></label>
        <button type="submit" class="btn btn--primary">Отправить заявку</button>
        <p class="form__note" id="form-note" role="status" hidden></p>
      </form>
    </div>
    <div class="cmap" id="cmap" role="application" aria-label="Карта Бухары"></div>
    <p class="cmap__note">Метка офиса появится на карте, когда будет известен адрес.</p>
  </div>
</main>
""", current="contacts.html",
    head='<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css">\n',
    scripts='<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>\n<script src="contacts.js"></script>\n',
    desc="Контакты отдела продаж Palm в Бухаре и запись на показ дома."))
print(f"страниц: {n} → {out}; авторов фото: {len(credits)}")
