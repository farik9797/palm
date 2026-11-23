#!/usr/bin/env python3
"""Собирает страницы объектов site/objects/<slug>.html из строк списка в site/index.html.

Запуск из корня проекта:  python3 tools/build_pages.py
Одна строка <li class="row" data-pin ...> = одна метка на карте = одна страница.
Необязательное описание объекта: <p class="row__desc" hidden>текст</p> внутри строки.
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

PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} | Palm</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../styles.css">
</head>
<body>
<header class="nav">
  <div class="container nav__in">
    <a class="nav__mark" href="../">Palm</a>
    <a class="nav__back" href="../#index">Все объекты</a>
    <a class="btn btn--primary" href="../#contact">Записаться на показ</a>
  </div>
</header>
<main class="obj">
  <div class="container obj__in">
    <div class="obj__photo{empty}"{slot}>{photo}</div>
    <div class="obj__info">
      <p class="obj__kind">{kind}</p>
      <h1>{name}</h1>
{desc}      <dl class="facts">
{facts}      </dl>
      <div class="obj__actions">
        <a class="btn btn--primary" href="../#pin={slug}">Показать на карте</a>
        <a class="btn" href="../#index">Все объекты</a>
      </div>
{credit}    </div>
  </div>
</main>
</body>
</html>
"""

out = SITE / "objects"
out.mkdir(exist_ok=True)
for old in out.glob("*.html"):
    old.unlink()
n = 0
for m in ROW.finditer(index):
    attrs, body = m["attrs"], m["body"]
    slug, photo, kind = attr(attrs, "data-slug"), attr(attrs, "data-photo"), attr(attrs, "data-kind")
    name = re.search(r'class="row__go"[^>]*>(.*?)</a>', body, re.S)[1].strip()
    label = re.search(r'class="row__kind">(.*?)</span>', body, re.S)[1].strip()
    facts = "".join(f"        <div><dt>{dt}</dt><dd>{dd}</dd></div>\n"
                    for dt, dd in re.findall(r"<dt>(.*?)</dt><dd[^>]*>(.*?)</dd>", body, re.S))
    facts += f'        <div><dt>Координаты</dt><dd>{attr(attrs, "data-lat")}, {attr(attrs, "data-lng")}</dd></div>\n'
    d = re.search(r'class="row__desc"[^>]*>(.*?)</p>', body, re.S)
    desc = f'      <p class="obj__desc">{d[1].strip()}</p>\n' if d and d[1].strip() else ""
    c = credits.get(slug)
    credit = (f'      <p class="obj__credit">Фото: {html.escape(c["author"])}, {html.escape(c["license"])}, '
              f'<a href="{html.escape(c["page"])}">Wikimedia Commons</a></p>\n') if c and photo else ""
    (out / f"{slug}.html").write_text(PAGE.format(
        name=name, kind=label, slug=slug, facts=facts, desc=desc, credit=credit,
        empty="" if photo else " obj__photo--empty", slot=' data-slot="photo"' if photo else "",
        photo=f'<img src="../{photo}" alt="{html.escape(name)}">' if photo else "Здесь будет фото объекта"))
    n += 1
print(f"страниц: {n} → {out}")
