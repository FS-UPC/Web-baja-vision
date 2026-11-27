#!/usr/bin/env python3
"""Generador estàtic de la web «Baixa visió en xarxa».

Només fa servir la biblioteca estàndard de Python (3.8+), sense dependències.

    python3 build.py                 # genera el lloc a dist/
    BASE_URL=https://exemple.cat python3 build.py
                                     # a més, URL absolutes (hreflang/canonical), sitemap.xml
                                     # i codis QR que apunten al domini definitiu
    STAGING=1 python3 build.py       # entorn de proves (REQ-12): avís visible, noindex,
                                     # robots.txt que bloqueja els cercadors
    FEEDBACK_ENDPOINT=https://...    # (opcional) adreça que rep el formulari de validació (POST)
    FEEDBACK_EMAIL=adreca@upc.edu    # (opcional) correu alternatiu per al formulari de validació

Estructura:
    src/templates/layout.html   plantilla comuna (capçalera, panell d'accessibilitat, peu)
    src/pages/<idioma>/<clau>.html  contingut de cada pàgina (fragment HTML)
    src/data/team.json          fitxes de l'equip (trilingües)
    src/data/glossary.json      termes del glossari (trilingües)
    src/data/resources.json     fitxes del generador de recursos per a la consulta (PDF + QR)
    src/data/assistant.json     regles de l'assistent de recursos (perfils, necessitats, respostes)
    src/data/simulator.json     textos del simulador de visió (descripcions redactades a mà)
    src/data/testimonials.json  repositori de testimonis en vídeo (amb transcripció obligatòria)
    src/i18n.json               textos de la interfície i noms de fitxer per idioma
    src/assets/                 CSS, JS, tipografia i imatges

Marcadors que es poden fer servir dins dels fragments:
    {{href:clau}}   enllaç a una altra pàgina en el mateix idioma (p. ex. {{href:patients}})
    {{nav:clau}}    nom de la pàgina al menú
    {{ui:clau}}     text de la interfície
    {{icon:nom}}    icona SVG decorativa
    {{team}} {{glossary}} {{logo}} {{hero_art}} {{year}} {{root}}
    {{zone_cards}}    targetes de les tres àrees amb els enllaços a les subseccions (portada)
    {{subpages}}      targetes de les subseccions d'una àrea (pàgina d'àrea)
    {{assistant}}     assistent de recursos (cercador tancat sobre els continguts validats)
    {{simulator}}     simulador de visió   {{testimonials}}  repositori de testimonis
    {{resource_picker}} {{resource_sheets}} {{qr_box}}  generador i paquet de recursos
    {{feedback_action}} {{feedback_email}}  configuració del formulari de validació
"""
import datetime
import html
import json
import os
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
STAGING = os.environ.get("STAGING", "") not in ("", "0", "false", "no")
FEEDBACK_ENDPOINT = os.environ.get("FEEDBACK_ENDPOINT", "").strip()
FEEDBACK_EMAIL = os.environ.get("FEEDBACK_EMAIL", "").strip()
YEAR = str(datetime.date.today().year)

# --------------------------------------------------------------------------
# Icones (traç simple, 24×24). Sempre decoratives: el text que les acompanya
# és el que transmet la informació.
# --------------------------------------------------------------------------
ICONS = {
    "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "person": '<circle cx="12" cy="7.5" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>',
    "pro": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M12 10.5v6M9 13.5h6"/>',
    "family": '<circle cx="9" cy="7.5" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5"/><circle cx="17.5" cy="9" r="2.5"/><path d="M16.5 13.6c2.9.2 5 2.6 5 5.9"/>',
    "heart": '<path d="M12 20s-7.5-4.6-7.5-10.2A4.2 4.2 0 0 1 12 7.3a4.2 4.2 0 0 1 7.5 2.5C19.5 15.4 12 20 12 20z"/>',
    "alert": '<path d="M12 3 2 21h20L12 3z"/><path d="M12 10v5"/><circle cx="12" cy="18" r=".8" fill="currentColor"/>',
    "info": '<circle cx="12" cy="12" r="9.5"/><path d="M12 11v6"/><circle cx="12" cy="7.5" r=".8" fill="currentColor"/>',
    "a11y": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="6.8" r="1.4" fill="currentColor"/><path d="M6.5 9.5 12 10.5l5.5-1M12 10.5v4l-2.5 4.5M12 14.5l2.5 4.5"/>',
    "home": '<path d="M3 11 12 4l9 7"/><path d="M5.5 9.5V20h13V9.5"/><path d="M10 20v-5h4v5"/>',
    "book": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5v-15"/><path d="M8 7h8"/>',
    "bulb": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
    "phone": '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18h2"/>',
    "network": '<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="18" r="2.5"/><circle cx="19" cy="18" r="2.5"/><path d="M10.8 7.2 6.2 15.8M13.2 7.2l4.6 8.6M7.5 18h9"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "speaker": '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/>',
    "play": '<path d="M7 4.5v15l12.5-7.5z" fill="currentColor"/>',
    "pause": '<path d="M8 5v14M16 5v14"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" fill="currentColor"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4V5z"/><path d="M8 9.5h8M8 12.5h5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "school": '<path d="m2 9 10-5 10 5-10 5z"/><path d="M6 11v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/>',
    "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "walk": '<circle cx="13.5" cy="4" r="2"/><path d="m10 21 2.5-6.5L10 12l1.2-4.3L15 10.5l3 1M8.5 13.5 7 21"/>',
    "ear": '<path d="M7 9a5 5 0 0 1 10 0c0 3-3 4-3 7a3 3 0 0 1-5.6 1.5"/><path d="M10 9.2a2 2 0 0 1 4 0"/>',
    "light": '<path d="M12 2v2M4.9 4.9l1.4 1.4M2 12h2M19.1 4.9l-1.4 1.4M22 12h-2"/><path d="M8 14a4 4 0 1 1 8 0c0 1.2-.6 2-1.3 2.7-.5.5-.7 1-.7 1.6V19h-4v-.7c0-.6-.2-1.1-.7-1.6C8.6 16 8 15.2 8 14z"/><path d="M10 22h4"/>',
    "contrast": '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/>',
    "text": '<path d="M4 7V5h11v2M9.5 5v14M7 19h5"/><path d="M14 13v-1.5h7V13M17.5 11.5V19M16 19h3"/>',
    "check": '<path d="m4 12.5 5 5L20 6.5"/>',
    "leaf": '<path d="M5 19c0-8 5-13 15-14-1 10-6 15-14 15"/><path d="M5 19c3-4 6-7 10-9"/>',
    "scale": '<path d="M12 3v18M7 21h10M4 7h16"/><path d="m4 7-2.5 6a3 3 0 0 0 5 0zM20 7l-2.5 6a3 3 0 0 0 5 0z"/>',
    "lang": '<path d="M3 5h10M8 3v2M5 5c.6 3.5 3 6.5 6.5 8M11 5c-.8 4-3.6 7.3-7.5 9"/><path d="m12.5 21 4.5-10 4.5 10M14 17.5h6"/>',
    "users": '<circle cx="8" cy="8" r="3"/><circle cx="16" cy="8" r="3"/><path d="M2.5 19c0-3 2.5-5.5 5.5-5.5s5.5 2.5 5.5 5.5M13.5 13.6a5.5 5.5 0 0 1 8 5.4"/>',
    "mic": '<rect x="9" y="2.5" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7"/>',
    "print": '<path d="M7 9V3h10v6"/><rect x="3" y="9" width="18" height="8" rx="1.5"/><path d="M7 14h10v7H7z"/>',
    "qr": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM18 18h3v3h-3zM14 20h2M20 14v2"/>',
    "video": '<rect x="2.5" y="6" width="13" height="12" rx="2"/><path d="m15.5 10.5 6-3.5v10l-6-3.5"/>',
    "cane": '<path d="M9 3.5a3 3 0 0 1 6 0V21"/><path d="M15 9.5v2M15 14v2" stroke-width="3.2"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
}


def icon(name):
    body = ICONS[name]
    return ('<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            + body + "</svg>")


LOGO = (
    '<svg class="brand__logo" viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
    '<path d="M5 32C12 19.5 21.5 13 32 13s20 6.5 27 19c-7 12.5-16.5 19-27 19S12 44.5 5 32z" '
    'fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/>'
    '<circle cx="32" cy="32" r="10.5" fill="currentColor"/>'
    '<circle cx="32" cy="32" r="4" fill="none" stroke="var(--bg)" stroke-width="2.5"/>'
    '<circle cx="5" cy="32" r="4.5" fill="currentColor"/><circle cx="59" cy="32" r="4.5" fill="currentColor"/>'
    '<circle cx="32" cy="13" r="4.5" fill="currentColor"/><circle cx="32" cy="51" r="4.5" fill="currentColor"/>'
    '</svg>'
)

HERO_ART = (
    '<svg class="hero__art" viewBox="0 0 320 240" aria-hidden="true" focusable="false">'
    '<g fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">'
    '<path d="M20 120C60 55 105 30 160 30s100 25 140 90c-40 65-85 90-140 90S60 185 20 120z" stroke-width="7" stroke-linejoin="round"/>'
    '<path d="M160 120 70 70M160 120l90-50M160 120 70 170M160 120l90 50M160 120 20 120M160 120h140M160 120V30M160 120v90" opacity=".45"/>'
    '</g>'
    '<circle cx="160" cy="120" r="42" fill="currentColor"/>'
    '<circle cx="160" cy="120" r="17" fill="none" stroke="var(--surface)" stroke-width="7"/>'
    '<g fill="currentColor">'
    '<circle cx="20" cy="120" r="11"/><circle cx="300" cy="120" r="11"/><circle cx="160" cy="30" r="11"/><circle cx="160" cy="210" r="11"/>'
    '<circle cx="70" cy="70" r="8"/><circle cx="250" cy="70" r="8"/><circle cx="70" cy="170" r="8"/><circle cx="250" cy="170" r="8"/>'
    '</g></svg>'
)

# Banderes del selector d'idioma (decoratives: el nom de l'idioma ja és el text de l'enllaç).
# Totes en proporció 3:2 perquè quedin alineades.
FLAGS = {
    "ca": ('<rect width="30" height="20" fill="#FCDD09"/>'
           '<g fill="#DA121A"><rect y="2.222" width="30" height="2.222"/><rect y="6.667" width="30" height="2.222"/>'
           '<rect y="11.111" width="30" height="2.222"/><rect y="15.556" width="30" height="2.222"/></g>'),
    "es": '<rect width="30" height="20" fill="#AA151B"/><rect y="5" width="30" height="10" fill="#F1BF00"/>',
    "en": ('<rect width="30" height="20" fill="#FFFFFF"/>'
           '<g fill="#CE1124"><rect x="13" width="4" height="20"/><rect y="8" width="30" height="4"/></g>'),
}


def flag(lang):
    return ('<svg class="flag" viewBox="0 0 30 20" aria-hidden="true" focusable="false">'
            + FLAGS[lang] + "</svg>")


# Logotips institucionals (fitxers oficials a src/assets/img/logos/). Es mostren sempre sobre
# una peça blanca perquè conservin els colors oficials en tots els temes de contrast.
LOGOS = {
    "upc": {"file": "upc.svg", "w": 279, "h": 61,
            "name": "Universitat Politècnica de Catalunya · BarcelonaTech",
            "url": {"ca": "https://www.upc.edu/ca", "es": "https://www.upc.edu/es", "en": "https://www.upc.edu/en"}},
    "b1b2b3": {"file": "b1b2b3.jpg", "w": 469, "h": 66,
               "name": "Associació Discapacitat Visual Catalunya: B1+B2+B3", "url": "https://b1b2b3.org/"},
    "agaur": {"file": "agaur.png", "w": 600, "h": 160,
              "name": "Agència de Gestió d'Ajuts Universitaris i de Recerca (AGAUR)",
              "url": {"ca": "https://agaur.gencat.cat/ca/inici/", "es": "https://agaur.gencat.cat/es/inici/",
                      "en": "https://agaur.gencat.cat/en/inici/"}},
    "generalitat": {"file": "generalitat.png", "w": 600, "h": 151, "name": "Generalitat de Catalunya",
                    "url": {"ca": "https://web.gencat.cat/ca/inici", "es": "https://web.gencat.cat/es/inici",
                            "en": "https://web.gencat.cat/en/inici"}},
    # Fundació Punt de Vista: logotip de la capçalera de pdvista.org (és l'única versió publicada, 118×90 px)
    "puntdevista": {"file": "puntdevista.jpg", "w": 118, "h": 90, "name": "Fundació Punt de Vista",
                    "url": "https://pdvista.org/"},
    # COOOC: logotip oficial de coooc.cat (PNG original de 1988×635, reduït a 600 px)
    "coooc": {"file": "coooc.png", "w": 600, "h": 192,
              "name": "Col·legi Oficial d'Òptics Optometristes de Catalunya (COOOC)", "url": "https://coooc.cat/"},
}


def logo_img(key, alt):
    lg = LOGOS[key]
    return (f'<img class="logo--{key}" src="../assets/img/logos/{lg["file"]}" alt="{esc(alt)}" width="{lg["w"]}" '
            f'height="{lg["h"]}" loading="lazy" decoding="async">')


def logo_tile(key):
    """Peça de logotip per a una targeta que ja té el nom com a encapçalament (decorativa)."""
    lg = LOGOS[key]
    if "text" in lg:
        # Sense logotip verificat: icona neutra (no simula cap logotip) i el nom ja és a l'encapçalament.
        return f'<div class="logo-tile logo-tile--card logo-tile--icon" aria-hidden="true">{icon("a11y")}</div>'
    return f'<div class="logo-tile logo-tile--card">{logo_img(key, "")}</div>'


def logo_link(key, lang):
    lg = LOGOS[key]
    if "text" in lg:
        return f'<li><span class="logo-tile logo-tile--text">{esc(lg["text"])}</span></li>'
    url = lg["url"] if isinstance(lg["url"], str) else lg["url"][lang]
    return f'<li><a class="logo-tile" href="{url}">{logo_img(key, lg["name"])}</a></li>'


def render_logo_band(lang):
    ui = I18N["ui"][lang]
    groups = [("logo_coord", ["upc"], ui["logo_coord_note"]),
              ("logo_collab", ["b1b2b3", "puntdevista", "coooc"], ""),
              ("logo_call", ["agaur", "generalitat"], "")]
    out = ['<section class="logo-band" aria-labelledby="f-logos">',
           f'<h2 id="f-logos" class="visually-hidden">{ui["logos_title"]}</h2>', '<div class="logo-groups">']
    for label, keys, note in groups:
        out.append(f'<div class="logo-group"><p class="logo-group__label">{ui[label]}</p><ul class="logo-list">')
        out += [logo_link(k, lang) for k in keys]
        out.append("</ul>")
        if note:
            out.append(f'<p class="logo-group__note">{note}</p>')
        out.append("</div>")
    out.append("</div></section>")
    return "\n".join(out)


FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#0a3a6b"/>'
    '<path d="M7 32C13.5 21 22 15.5 32 15.5S50.5 21 57 32c-6.5 11-15 16.5-25 16.5S13.5 43 7 32z" fill="none" stroke="#fff" stroke-width="4.5" stroke-linejoin="round"/>'
    '<circle cx="32" cy="32" r="9.5" fill="#ffd31a"/></svg>'
)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


I18N = load_json(SRC / "i18n.json")
LANGS = list(I18N["languages"].keys())
PAGES = I18N["pages"]


def filename(key, lang):
    return PAGES[key][lang] + ".html"


def esc(s):
    return html.escape(s, quote=True)


# --------------------------------------------------------------------------
# Blocs generats a partir de dades
# --------------------------------------------------------------------------
def initials(name):
    parts = [p for p in re.split(r"\s+", name) if p and p[0].isupper() and not p.endswith(".")]
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper() if parts else "·"


def render_team(lang):
    data = load_json(SRC / "data" / "team.json")
    out = []
    for group in data["groups"]:
        gid = group["id"]
        out.append(f'<section class="team-group" aria-labelledby="g-{gid}">')
        out.append(f'<h2 id="g-{gid}">{esc(group["title"][lang])}</h2>')
        if group.get("intro"):
            out.append(f'<p>{esc(group["intro"][lang])}</p>')
        out.append('<ul class="team-grid">')
        for m in group["members"]:
            name = m["name"] if isinstance(m["name"], str) else m["name"][lang]
            hid = "p-" + re.sub(r"[^a-z0-9]+", "-", name.lower().encode("ascii", "ignore").decode()).strip("-")
            if m.get("photo"):
                # La foto acompanya el nom (que ja és l'encapçalament), per això alt="".
                avatar = (f'<img class="avatar avatar--photo" src="../assets/img/team/{esc(m["photo"])}" '
                          f'alt="" width="160" height="160" loading="lazy" decoding="async">')
            else:
                avatar = f'<span class="avatar" aria-hidden="true">{esc(m.get("avatar") or initials(name))}</span>'
            out.append('<li><article class="person" aria-labelledby="%s">' % hid)
            out.append(f'<div class="person__head">{avatar}'
                       f'<div><h3 id="{hid}">{esc(name)}</h3>'
                       f'<p class="person__role">{esc(m["role"][lang])}</p></div></div>')
            if m.get("org"):
                out.append(f'<p class="person__org">{esc(m["org"][lang])}</p>')
            if m.get("bio"):
                out.append(f'<p class="person__bio">{esc(m["bio"][lang])}</p>')
            links = m.get("links", [])
            if links:
                out.append(f'<ul class="person__links" aria-label="{esc(data["links_label"][lang])} {esc(name)}">')
                for l in links:
                    label = l["label"] if isinstance(l["label"], str) else l["label"][lang]
                    url = l["url"] if isinstance(l["url"], str) else l["url"][lang]
                    out.append(f'<li><a href="{esc(url)}">{esc(label)}</a></li>')
                out.append("</ul>")
            out.append("</article></li>")
        out.append("</ul></section>")
    return "\n".join(out)


def sort_key(s):
    # ordenació alfabètica sense tenir en compte accents
    table = str.maketrans("àáâäèéêëìíîïòóôöùúûüçñŀ·", "aaaaeeeeiiiioooouuuucnl ")
    return s.lower().translate(table)


def render_glossary(lang):
    data = load_json(SRC / "data" / "glossary.json")
    terms = sorted(data["terms"], key=lambda t: sort_key(t["term"][lang]))
    groups = {}
    for t in terms:
        letter = sort_key(t["term"][lang])[0].upper()
        groups.setdefault(letter, []).append(t)
    out = [f'<nav aria-label="{esc(data["index_label"][lang])}"><ul class="alpha-index">']
    for letter in groups:
        out.append(f'<li><a href="#lletra-{letter}">{letter}</a></li>')
    out.append("</ul></nav>")
    out.append('<div class="glossary">')
    for letter, items in groups.items():
        out.append(f'<h2 class="letter" id="lletra-{letter}">{letter}</h2><dl>')
        for t in items:
            slug = re.sub(r"[^a-z0-9]+", "-", sort_key(t["term"][lang])).strip("-")
            out.append(f'<dt id="{slug}">{esc(t["term"][lang])}</dt><dd>{esc(t["def"][lang])}</dd>')
        out.append("</dl>")
    out.append("</div>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Plantilla
# --------------------------------------------------------------------------
META_RE = re.compile(r"^\s*<!--\s*meta\s*(\{.*?\})\s*-->\s*", re.S)


def read_page(lang, key):
    path = SRC / "pages" / lang / f"{key}.html"
    raw = path.read_text(encoding="utf-8")
    m = META_RE.match(raw)
    if not m:
        sys.exit(f"Falta el bloc <!-- meta {{...}} --> a {path}")
    return json.loads(m.group(1)), raw[m.end():]


def substitute(text, lang, root, extra):
    ui = I18N["ui"][lang]
    nav = I18N["nav"][lang]

    def repl(m):
        kind, _, arg = m.group(1).partition(":")
        if kind == "ui":
            return ui[arg]
        if kind == "nav":
            return nav[arg]
        if kind == "href":
            return filename(arg, lang)
        if kind == "icon":
            return icon(arg)
        if kind == "logo_tile":
            return logo_tile(arg)
        if kind in extra:
            return extra[kind]
        raise KeyError(f"Marcador desconegut: {{{{{m.group(1)}}}}}")

    return re.sub(r"\{\{\s*([a-z_]+(?::[a-z_0-9-]+)?)\s*\}\}", repl, text)


def page_url(lang, key):
    return f"{BASE_URL}/{lang}/{filename(key, lang)}"


# --------------------------------------------------------------------------
# Arquitectura de la informació: àrees, subseccions i navegació
# --------------------------------------------------------------------------
def children(key):
    return [k for k, v in PAGES.items() if v.get("parent") == key]


def ancestors(key):
    out, k = [], PAGES[key].get("parent")
    while k:
        out.insert(0, k)
        k = PAGES[k].get("parent")
    return out


def area_of(key):
    chain = ancestors(key) + [key]
    for k in chain:
        if PAGES[k].get("area"):
            return k
    return None


META_CACHE = {}


def page_meta(lang, key):
    if (lang, key) not in META_CACHE:
        META_CACHE[(lang, key)] = read_page(lang, key)[0]
    return META_CACHE[(lang, key)]


def render_zone_cards(lang):
    """Targetes de la portada: cada àrea amb enllaç directe a totes les subseccions (regla dels 2 clics)."""
    nav, ui = I18N["nav"][lang], I18N["ui"][lang]
    icons = {"patients": "person", "families": "family", "professionals": "pro"}
    out = ['<ul class="zone-cards">']
    for i, k in enumerate([k for k in I18N["nav_order"] if PAGES[k].get("area")], 1):
        z = PAGES[k]["zone"]
        out.append(f'<li><article class="zone-card" data-zone="{z}" aria-labelledby="zc-{k}">')
        out.append(f'<div class="zone-card__head">{icon(icons[k])}<span class="zone-card__label">{i}</span></div>')
        out.append('<div class="zone-card__body">')
        out.append(f'<h3 id="zc-{k}"><a href="{filename(k, lang)}">{esc(nav[k])}</a></h3>')
        out.append(f'<p class="zone-card__tag">{esc(ui["area_tag_" + k])}</p>')
        out.append(f'<ul class="zone-card__links" aria-label="{esc(nav[k])}">')
        for c in children(k):
            out.append(f'<li><a href="{filename(c, lang)}">{icon(PAGES[c].get("icon", "arrow"))}<span>{esc(nav[c])}</span></a></li>')
        out.append("</ul>")
        out.append(f'<a class="btn btn--zone" href="{filename(k, lang)}">{icon("arrow")}<span>{esc(ui["zone_enter"])}'
                   f'<span class="visually-hidden">: {esc(nav[k])}</span></span></a>')
        out.append("</div></article></li>")
    out.append("</ul>")
    return "\n".join(out)


def render_subpages(lang, key):
    nav = I18N["nav"][lang]
    out = ['<ol class="subpage-cards">']
    for c in children(key):
        out.append(f'<li class="card"><h3>{icon(PAGES[c].get("icon", "arrow"))}'
                   f'<a href="{filename(c, lang)}">{esc(nav[c])}</a></h3>'
                   f'<p>{esc(page_meta(lang, c)["description"])}</p></li>')
    out.append("</ol>")
    return "\n".join(out)


def render_local_nav(lang, key):
    """Navegació entre les subseccions d'una àrea, al final de cada subsecció."""
    parent = PAGES[key].get("parent")
    if not parent or not PAGES[parent].get("area"):
        return ""
    nav, ui = I18N["nav"][lang], I18N["ui"][lang]
    sib = children(parent)
    i = sib.index(key)
    out = [f'<nav class="local-nav container" aria-labelledby="ln-title"><h2 id="ln-title">{esc(ui["section_nav"])}: {esc(nav[parent])}</h2><ol>']
    for k in sib:
        cur = ' aria-current="page"' if k == key else ""
        out.append(f'<li><a href="{filename(k, lang)}"{cur}>{esc(nav[k])}</a></li>')
    out.append("</ol>")
    pn = []
    if i > 0:
        pn.append(f'<a class="btn btn--ghost" href="{filename(sib[i-1], lang)}" rel="prev">'
                  f'<span>{esc(ui["prev"])}: {esc(nav[sib[i-1]])}</span></a>')
    if i < len(sib) - 1:
        pn.append(f'<a class="btn btn--ghost" href="{filename(sib[i+1], lang)}" rel="next">'
                  f'<span>{esc(ui["next"])}: {esc(nav[sib[i+1]])}</span>{icon("arrow")}</a>')
    if pn:
        out.append('<div class="btn-row local-nav__pn">' + "".join(pn) + "</div>")
    out.append("</nav>")
    return "\n".join(out)


def render_footer_lists(lang):
    nav = I18N["nav"][lang]
    zones = []
    for k in [k for k in I18N["nav_order"] if PAGES[k].get("area")]:
        zones.append(f'<li><a href="{filename(k, lang)}">{esc(nav[k])}</a></li>')
    project = [f'<li><a href="{filename(k, lang)}">{esc(nav[k])}</a></li>'
               for k in ["assistant", "about", "project", "team", "glossary", "accessibility", "validation"]]
    return "\n".join(zones), "\n".join(project)


# --------------------------------------------------------------------------
# Eines: assistent, simulador, testimonis, generador de recursos
# --------------------------------------------------------------------------
def render_assistant(lang):
    a = load_json(SRC / "data" / "assistant.json")[lang]
    ex = "".join(f'<li><button type="button" class="chip" data-example>{esc(e)}</button></li>' for e in a["examples"])
    prof = "".join(
        f'<label class="seg"><input type="radio" name="as-profile" value="{p}"{" checked" if p == "auto" else ""}>'
        f'<span>{esc(a["profiles"][p]["label"])}</span></label>' for p in ["auto", "patient", "family", "pro"])
    return f'''<div class="assistant" data-assistant>
  <form class="assistant__form" role="search" aria-labelledby="as-title" novalidate>
    <h2 id="as-title">{icon("chat")} {esc(a["title"])}</h2>
    <p class="assistant__intro">{esc(a["intro"])}</p>
    <fieldset class="segmented"><legend>{esc(a["profile_legend"])}</legend>{prof}</fieldset>
    <label class="assistant__label" for="as-q">{esc(a["label"])}</label>
    <div class="assistant__row">
      <input type="search" id="as-q" name="q" autocomplete="off" spellcheck="true" aria-describedby="as-hint">
      <button type="button" class="btn btn--ghost" id="as-mic" hidden aria-pressed="false">{icon("mic")}<span>{esc(a["mic"])}</span></button>
      <button type="submit" class="btn">{icon("search")}<span>{esc(a["submit"])}</span></button>
    </div>
    <p class="note" id="as-hint">{esc(a["hint"])}</p>
    <p class="assistant__examples-label" id="as-ex">{esc(a["examples_label"])}</p>
    <ul class="chips" aria-labelledby="as-ex">{ex}</ul>
  </form>
  <div class="assistant__answer" id="as-answer" tabindex="-1" aria-live="polite"></div>
  <noscript><p class="note">{esc(a["noscript"])}</p></noscript>
</div>'''


def render_simulator(lang):
    d = load_json(SRC / "data" / "simulator.json")
    t = d["ui"][lang]
    opts = []
    for i, m in enumerate(d["modes"]):
        opts.append(f'<label class="choice"><input type="radio" name="sim-mode" value="{m["id"]}"'
                    f'{" checked" if i == 0 else ""} data-desc="{esc(m["desc"][lang])}"> '
                    f'<span class="choice__text">{esc(m["label"][lang])}</span></label>')
    first = d["modes"][0]["desc"][lang]
    s = t["scene"]
    scene = f'''<svg class="sim__scene" viewBox="0 0 640 400" aria-hidden="true" focusable="false">
  <rect width="640" height="400" fill="#dfe8f1"/>
  <rect x="0" y="250" width="640" height="150" fill="#b98d5f"/>
  <rect x="40" y="40" width="190" height="200" fill="#ffffff" stroke="#333" stroke-width="6"/>
  <path d="M135 40v200M40 140h190" stroke="#333" stroke-width="5"/>
  <circle cx="520" cy="95" r="58" fill="#fff" stroke="#222" stroke-width="7"/>
  <path d="M520 95V58M520 95l26 16" stroke="#222" stroke-width="7" stroke-linecap="round"/>
  <rect x="248" y="58" width="190" height="78" rx="8" fill="#0a3a6b"/>
  <text x="343" y="110" text-anchor="middle" font-family="Arial, sans-serif" font-size="38" font-weight="700" fill="#fff">{esc(s["sign"])}</text>
  <rect x="300" y="300" width="300" height="22" fill="#6b4a2b"/>
  <path d="M330 322v70M570 322v70" stroke="#6b4a2b" stroke-width="16"/>
  <path d="M390 300c0-36 18-52 40-52s40 16 40 52z" fill="#d23c3c"/>
  <rect x="490" y="262" width="60" height="38" rx="4" fill="#f5f5f5" stroke="#333" stroke-width="4"/>
  <text x="520" y="288" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#111">{esc(s["label"])}</text>
  <circle cx="120" cy="300" r="34" fill="#f2c94c"/>
  <path d="M0 360h260v40H0z" fill="#8c6a45"/><path d="M0 360h260" stroke="#ffd31a" stroke-width="8"/>
  <circle cx="180" cy="215" r="24" fill="#e8b48f"/><path d="M150 250c0-18 14-28 30-28s30 10 30 28v20h-60z" fill="#2f6f4e"/>
</svg>'''
    return f'''<div class="sim" data-simulator>
  <fieldset class="sim__controls"><legend>{esc(t["legend"])}</legend>{"".join(opts)}</fieldset>
  <figure class="sim__figure">
    <div class="sim__view" data-mode="normal" role="img" aria-labelledby="sim-cap sim-desc">{scene}<div class="sim__overlay" aria-hidden="true"></div></div>
    <figcaption><span id="sim-cap" class="visually-hidden">{esc(t["caption"])}: </span><span id="sim-desc" aria-live="polite">{esc(first)}</span></figcaption>
  </figure>
  <p class="note">{esc(t["note"])}</p>
</div>'''


def render_testimonials(lang):
    d = load_json(SRC / "data" / "testimonials.json")
    t = d["ui"][lang]
    items = d.get("items", [])
    if not items:
        return f'<div class="box empty-state">{icon("video")}<div><p><strong>{esc(t["empty_title"])}</strong></p><p>{esc(t["empty"])}</p></div></div>'
    paths = sorted({i["pathology"][lang] for i in items})
    ages = sorted({i["age"][lang] for i in items})
    sel = lambda name, label, vals: (f'<p><label for="tf-{name}">{esc(label)}</label> <select id="tf-{name}" data-filter="{name}">'
                                     f'<option value="">{esc(t["all"])}</option>'
                                     + "".join(f'<option>{esc(v)}</option>' for v in vals) + "</select></p>")
    out = [f'<div class="filters" data-testimonial-filters>{sel("pathology", t["by_pathology"], paths)}{sel("age", t["by_age"], ages)}</div>',
           '<ul class="testimonials" data-testimonials>']
    for it in items:
        tid = esc(it["id"])
        out.append(f'<li data-pathology="{esc(it["pathology"][lang])}" data-age="{esc(it["age"][lang])}">'
                   f'<article class="card testimonial" aria-labelledby="t-{tid}"><h3 id="t-{tid}">{esc(it["title"][lang])}</h3>'
                   f'<p class="person__role">{esc(it["pathology"][lang])} · {esc(it["age"][lang])}</p>'
                   f'<video controls preload="none" width="640" height="360">'
                   f'<source src="../assets/media/{esc(it["video"])}" type="video/mp4">'
                   f'<track kind="captions" src="../assets/media/{esc(it["captions"][lang])}" srclang="{lang}" label="{esc(t["captions"])}" default>'
                   f'<track kind="descriptions" src="../assets/media/{esc(it["descriptions"][lang])}" srclang="{lang}" label="{esc(t["descriptions"])}">'
                   f'</video>'
                   f'<details data-transcript><summary>{esc(t["transcript"])}</summary><div>{it["transcript"][lang]}</div></details>'
                   f'</article></li>')
    out.append("</ul>")
    return "\n".join(out)


def load_resources():
    return load_json(SRC / "data" / "resources.json")


def render_resource_picker(lang):
    d = load_resources()
    t = d["ui"][lang]
    out = []
    for cat in d["categories"]:
        out.append(f'<fieldset class="picker-group"><legend>{esc(cat["title"][lang])}</legend>')
        for it in [i for i in d["items"] if i["cat"] == cat["id"]]:
            rid = esc(it["id"])
            out.append(f'<label class="choice choice--block"><input type="checkbox" name="r" value="{rid}" aria-describedby="rd-{rid}">'
                       f'<span><span class="choice__text">{esc(it["title"][lang])}</span>'
                       f'<span class="choice__desc" id="rd-{rid}">{esc(it["summary"][lang])}</span></span></label>')
        out.append("</fieldset>")
    return "\n".join(out)


def render_resource_sheets(lang):
    d = load_resources()
    nav = I18N["nav"][lang]
    t = d["ui"][lang]
    out = []
    for it in d["items"]:
        rid = esc(it["id"])
        more = ""
        if it.get("more"):
            k, _, frag = it["more"].partition("#")
            href = filename(k, lang) + (f"#{frag}" if frag else "")
            more = f'<p class="sheet__more">{esc(t["more"])}: <a href="{href}">{esc(nav[k])}</a></p>'
        out.append(f'<article class="sheet" id="sheet-{rid}" data-sheet="{rid}" aria-labelledby="sh-{rid}">'
                   f'<h2 id="sh-{rid}">{esc(it["title"][lang])}</h2>{it["body"][lang]}{more}</article>')
    return "\n".join(out)


def render_qr_box(lang):
    t = load_resources()["ui"][lang]
    return (f'<div class="qr-box" data-qr data-base="{esc(BASE_URL)}" data-pack="{filename("pack", lang)}">'
            f'<div class="qr-box__code" data-qr-code role="img" aria-label="{esc(t["qr_alt"])}"></div>'
            f'<div><p class="qr-box__title">{icon("qr")} {esc(t["qr_title"])}</p>'
            f'<p class="qr-box__url"><a data-qr-link href="{filename("pack", lang)}">{filename("pack", lang)}</a></p>'
            f'<p class="note" data-qr-local hidden>{esc(t["qr_local"])}</p></div></div>')


def build_page(layout, lang, key):
    meta, body = read_page(lang, key)
    nav = I18N["nav"][lang]
    ui = I18N["ui"][lang]
    root = "../"
    zone = PAGES[key].get("zone")
    area = area_of(key)

    # Selector d'idioma: enllaça a la mateixa pàgina en l'altre idioma
    lang_links = []
    for l in LANGS:
        name = I18N["languages"][l]["name"]
        cur = ' aria-current="true"' if l == lang else ""
        href = f"../{l}/{filename(key, l)}"
        lang_links.append(f'          <li><a href="{href}" hreflang="{l}" lang="{l}"{cur}><span>{name}</span>{flag(l)}</a></li>')

    nav_links = []
    for k in I18N["nav_order"]:
        z = PAGES[k].get("zone")
        if k == key:
            cur = ' aria-current="page"'
        elif k == area:
            cur = ' aria-current="true"'
        else:
            cur = ""
        zattr = f' data-zone="{z}"' if z else ""
        dot = '<span class="dot" aria-hidden="true"></span>' if z else ""
        nav_links.append(f'        <li><a href="{filename(k, lang)}"{zattr}{cur}>{dot}<span>{nav[k]}</span></a></li>')

    header_links = []
    for k in I18N["header_links"]:
        cur = ' aria-current="page"' if k == key else (' aria-current="true"' if k in ancestors(key) else "")
        ic = {"assistant": "chat", "about": "users"}[k]
        header_links.append(f'<li><a class="tool-link" href="{filename(k, lang)}"{cur}>{icon(ic)}<span>{nav[k]}</span></a></li>')

    if key == "home":
        breadcrumbs = ""
    else:
        crumbs = [f'<li><a href="{filename("home", lang)}">{nav["home"]}</a></li>']
        crumbs += [f'<li><a href="{filename(a, lang)}">{nav[a]}</a></li>' for a in ancestors(key)]
        crumbs.append(f'<li><span aria-current="page">{nav[key]}</span></li>')
        breadcrumbs = (f'<nav class="breadcrumbs container" aria-label="{ui["breadcrumbs"]}"><ol>'
                       + "".join(crumbs) + '</ol></nav>')

    alternates = []
    if BASE_URL:
        alternates.append(f'<link rel="canonical" href="{page_url(lang, key)}">')
        for l in LANGS:
            alternates.append(f'<link rel="alternate" hreflang="{l}" href="{page_url(l, key)}">')
        alternates.append(f'<link rel="alternate" hreflang="x-default" href="{page_url("ca", key)}">')
    else:
        for l in LANGS:
            if l != lang:
                alternates.append(f'<link rel="alternate" hreflang="{l}" href="../{l}/{filename(key, l)}">')
    if STAGING or key == "pack":
        alternates.append('<meta name="robots" content="noindex, nofollow">')

    title = meta["title"]
    page_title = f"Baixa visió en xarxa · {ui['tagline']}" if key == "home" else f"{title} · Baixa visió en xarxa"

    scripts = []
    if "{{assistant}}" in body:
        scripts.append(f'<script src="{root}assets/js/index-{lang}.js" defer></script>')
        scripts.append(f'<script src="{root}assets/js/assistant.js" defer></script>')
    if "{{qr_box}}" in body:
        scripts.append(f'<script src="{root}assets/js/vendor/qrcode.js" defer></script>')

    staging = ""
    if STAGING:
        staging = (f'<div class="staging-banner" role="note">{icon("alert")}<p>{ui["staging_banner"]} '
                   f'<a href="{filename("validation", lang)}">{ui["staging_link"]}</a></p></div>')

    footer_zones, footer_project = render_footer_lists(lang)
    extra = {
        "lang": lang,
        "root": root,
        "year": YEAR,
        "logo": LOGO,
        "hero_art": HERO_ART,
        "page_title": esc(page_title),
        "description": esc(meta["description"]),
        "og_locale": I18N["languages"][lang]["og_locale"],
        "alternates": "\n".join(alternates),
        "lang_links": "\n".join(lang_links),
        "nav_links": "\n".join(nav_links),
        "header_links": "\n".join(header_links),
        "breadcrumbs": breadcrumbs,
        "home_current": ' aria-current="page"' if key == "home" else "",
        "logo_band": render_logo_band(lang),
        "js_strings": json.dumps(ui["js"], ensure_ascii=False).replace("</", "<\\/"),
        "page_scripts": "\n".join(scripts),
        "staging_banner": staging,
        "local_nav": render_local_nav(lang, key),
        "footer_zones": footer_zones,
        "footer_project": footer_project,
        "feedback_action": esc(FEEDBACK_ENDPOINT),
        "feedback_email": esc(FEEDBACK_EMAIL),
    }
    lazy = {
        "team": lambda: render_team(lang),
        "glossary": lambda: render_glossary(lang),
        "zone_cards": lambda: render_zone_cards(lang),
        "subpages": lambda: render_subpages(lang, key),
        "assistant": lambda: render_assistant(lang),
        "simulator": lambda: render_simulator(lang),
        "testimonials": lambda: render_testimonials(lang),
        "resource_picker": lambda: render_resource_picker(lang),
        "resource_sheets": lambda: render_resource_sheets(lang),
        "qr_box": lambda: render_qr_box(lang),
    }
    for name, fn in lazy.items():
        if "{{" + name + "}}" in body:
            extra[name] = fn()

    content = substitute(body, lang, root, extra)
    CONTENT[(lang, key)] = (meta, content)
    extra["content"] = content
    out = substitute(layout, lang, root, extra)
    classes = []
    if zone:
        classes.append(f"zone-{zone}")
    if meta.get("main_class"):
        classes.append(meta["main_class"])
    if classes:
        out = out.replace('<main id="main" tabindex="-1">', f'<main id="main" tabindex="-1" class="{" ".join(classes)}">', 1)
    return out


# --------------------------------------------------------------------------
# Índex de l'assistent de recursos: corpus tancat amb els continguts validats
# --------------------------------------------------------------------------
CONTENT = {}
NO_INDEX = {"home", "assistant", "pack", "validation"}


def strip_tags(h):
    h = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()


def build_index(lang):
    nav = I18N["nav"][lang]
    entries = []
    for key in PAGES:
        if key in NO_INDEX or (lang, key) not in CONTENT:
            continue
        meta, content = CONTENT[(lang, key)]
        content = re.sub(r'<nav class="toc".*?</nav>', " ", content, flags=re.S)
        z = PAGES[key].get("zone", "")
        kw = meta.get("keywords", "")
        entries.append({"u": filename(key, lang), "p": nav[key], "t": nav[key], "z": z, "k": key,
                        "s": meta["description"], "x": (meta["description"] + " " + kw)})
        parts = re.split(r'(<h2[^>]*\bid="[^"]+"[^>]*>.*?</h2>)', content, flags=re.S)
        for i in range(1, len(parts), 2):
            m = re.search(r'id="([^"]+)"', parts[i])
            title = strip_tags(parts[i])
            text = strip_tags(parts[i + 1] if i + 1 < len(parts) else "")
            if not text:
                continue
            snippet = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0][:220]
            entries.append({"u": f"{filename(key, lang)}#{m.group(1)}", "p": nav[key], "t": title, "z": z, "k": key,
                            "s": snippet, "x": (title + " " + text)[:1600] + " " + kw})
        # Targetes amb identificador propi (p. ex. cada patologia): fragments més precisos
        for m in re.finditer(r'<(li|div|article)[^>]*\bid="([^"]+)"[^>]*>\s*<h3[^>]*>(.*?)</h3>(.*?)</\1>', content, flags=re.S):
            title, text = strip_tags(m.group(3)), strip_tags(m.group(4))
            if text:
                snippet = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0][:220]
                entries.append({"u": f"{filename(key, lang)}#{m.group(2)}", "p": nav[key], "t": title, "z": z, "k": key,
                                "s": snippet, "x": (title + " " + title + " " + text)[:1600]})
    cfg = load_json(SRC / "data" / "assistant.json")[lang]
    pages = {k: filename(k, lang) for k in PAGES}
    data = ("window.BVX_INDEX=" + json.dumps(entries, ensure_ascii=False) + ";\n"
            "window.BVX_ASSISTANT=" + json.dumps({"cfg": cfg, "pages": pages, "nav": nav}, ensure_ascii=False) + ";\n")
    (DIST / "assets" / "js" / f"index-{lang}.js").write_text(data.replace("</", "<\\/"), encoding="utf-8")
    return len(entries)


def build_root_pages():
    names = I18N["languages"]
    homes = {l: f"{l}/{filename('home', l)}" for l in LANGS}
    titles = {"ca": "Tria l'idioma", "es": "Elige el idioma", "en": "Choose your language"}
    items = "\n".join(
        f'      <li><a class="btn btn--ghost" href="{homes[l]}" hreflang="{l}" lang="{l}"><span>{names[l]["name"]}</span>{flag(l)}</a></li>' for l in LANGS)
    script = (
        "(function(){var s=['ca','es','en'],l=null;try{l=localStorage.getItem('bvx-lang')}catch(e){}"
        "if(s.indexOf(l)<0){var n=(navigator.languages||[navigator.language||'ca']);"
        "for(var i=0;i<n.length&&!l;i++){var c=String(n[i]).slice(0,2).toLowerCase();if(s.indexOf(c)>=0)l=c;}"
        "if(s.indexOf(l)<0)l='ca';}"
        "location.replace(l+'/index.html');})();"
    )
    index = f"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Baixa visió en xarxa</title>
<meta name="description" content="Plataforma digital accessible sobre baixa visió · Plataforma digital accesible sobre baja visión · Accessible digital platform on low vision">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/fonts/fonts.css">
<link rel="stylesheet" href="assets/css/site.css">
<script>{script}</script>
</head>
<body>
<main class="lang-chooser">
  <div>
    {LOGO.replace('class="brand__logo"', 'class="brand__logo" style="width:6rem;height:6rem;color:var(--primary)"')}
    <h1>Baixa visió en xarxa</h1>
    <p><span lang="ca">{titles['ca']}</span> · <span lang="es">{titles['es']}</span> · <span lang="en">{titles['en']}</span></p>
    <ul>
{items}
    </ul>
  </div>
</main>
</body>
</html>
"""
    (DIST / "index.html").write_text(index, encoding="utf-8")

    notfound = f"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 · Baixa visió en xarxa</title>
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<main class="lang-chooser">
  <div>
    <h1>404</h1>
    <p lang="ca">No hem trobat aquesta pàgina.</p>
    <p lang="es">No hemos encontrado esta página.</p>
    <p lang="en">We could not find this page.</p>
    <ul>
{items.replace('href="', 'href="/')}
    </ul>
  </div>
</main>
</body>
</html>
"""
    (DIST / "404.html").write_text(notfound, encoding="utf-8")


def build_sitemap():
    if STAGING:
        # Entorn de proves: que cap cercador l'indexi.
        (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
        return
    if not BASE_URL:
        return
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for key in PAGES:
        if key == "pack":
            continue
        for lang in LANGS:
            rows.append(f"  <url><loc>{page_url(lang, key)}</loc>")
            for l in LANGS:
                rows.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{page_url(l, key)}"/>')
            rows.append("  </url>")
    rows.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Comprovacions bàsiques: enllaços interns, ancoratges, ids duplicats, alt
# --------------------------------------------------------------------------
class Checker(HTMLParser):
    """Comprovacions automàtiques de cada pàgina generada (REQ-01 i REQ-03):
    enllaços i ancoratges, ids duplicats, imatges sense alt, jerarquia d'encapçalaments
    dins de <main> (un sol h1, sense salts, fins a h3) i vídeos sense subtítols ni transcripció."""

    def __init__(self):
        super().__init__()
        self.links, self.ids, self.dups, self.problems = [], set(), [], []
        self.in_main = 0
        self.headings = []
        self.video = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.dups.append(a["id"])
            self.ids.add(a["id"])
        for attr in ("href", "src", "action"):
            if attr in a and a[attr]:
                self.links.append(a[attr])
        if tag == "img" and "alt" not in a:
            self.problems.append("img sense alt")
        if tag == "a" and "target" in a:
            self.problems.append("enllaç amb target (evitem obrir finestres noves)")
        if tag == "main":
            self.in_main += 1
        if self.in_main and re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "video":
            self.video = {"captions": False}
        if tag == "track" and self.video is not None and a.get("kind") == "captions":
            self.video["captions"] = True
        if tag == "details" and "data-transcript" in a and self.problems and self.problems[-1] == "PENDING_TRANSCRIPT":
            self.problems.pop()

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main -= 1
        if tag == "video" and self.video is not None:
            if not self.video["captions"]:
                self.problems.append("vídeo sense subtítols (<track kind=captions>)")
            self.problems.append("PENDING_TRANSCRIPT")
            self.video = None

    def close(self):
        super().close()
        if "PENDING_TRANSCRIPT" in self.problems:
            self.problems = [p for p in self.problems if p != "PENDING_TRANSCRIPT"]
            self.problems.append("vídeo sense transcripció (<details data-transcript>)")
        h = self.headings
        if h:
            if h.count(1) != 1 or h[0] != 1:
                self.problems.append(f"cal exactament un h1 al principi de <main> (trobats: {h.count(1)})")
            for prev, cur in zip(h, h[1:]):
                if cur > prev + 1:
                    self.problems.append(f"salt d'encapçalament h{prev} → h{cur}")
                    break
            if max(h) > 3:
                self.problems.append("encapçalament més enllà d'h3 (la jerarquia acordada és h1-h3)")


def check_site():
    errors = []
    parsed = {}
    for f in DIST.rglob("*.html"):
        c = Checker()
        text = f.read_text(encoding="utf-8")
        c.feed(text)
        c.close()
        parsed[f] = c
        if "{{" in text:
            errors.append(f"{f.relative_to(DIST)}: marcador sense substituir")
        for d in c.dups:
            errors.append(f"{f.relative_to(DIST)}: id duplicat «{d}»")
        for p in c.problems:
            errors.append(f"{f.relative_to(DIST)}: {p}")
    for f, c in parsed.items():
        if f.name == "404.html":
            continue
        for link in c.links:
            if re.match(r"^(https?:|mailto:|tel:|data:)", link) or link.startswith("{"):
                continue
            path, _, frag = link.partition("#")
            target = (f.parent / path).resolve() if path else f
            if not target.exists():
                errors.append(f"{f.relative_to(DIST)}: enllaç trencat → {link}")
            elif frag and target.suffix == ".html":
                tc = parsed.get(target)
                if tc and frag not in tc.ids:
                    errors.append(f"{f.relative_to(DIST)}: ancoratge inexistent → {link}")
    return errors


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC / "assets", DIST / "assets")
    (DIST / "assets" / "img").mkdir(parents=True, exist_ok=True)
    (DIST / "assets" / "img" / "favicon.svg").write_text(FAVICON, encoding="utf-8")

    layout = (SRC / "templates" / "layout.html").read_text(encoding="utf-8")
    count = 0
    for lang in LANGS:
        (DIST / lang).mkdir(parents=True, exist_ok=True)
        for key in PAGES:
            out = build_page(layout, lang, key)
            (DIST / lang / filename(key, lang)).write_text(out, encoding="utf-8")
            count += 1
    indexed = sum(build_index(lang) for lang in LANGS)
    build_root_pages()
    build_sitemap()

    errors = check_site()
    print(f"Generades {count} pàgines a {DIST.relative_to(ROOT)}/ ({', '.join(LANGS)})"
          + (" · ENTORN DE PROVES (staging)" if STAGING else ""))
    print(f"Índex de l'assistent: {indexed} fragments de contingut validat")
    if errors:
        print("\nProblemes detectats:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("Comprovació d'enllaços i identificadors: correcta.")


if __name__ == "__main__":
    main()
