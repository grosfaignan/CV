"""Lecture de cv.yaml (source unique) et production :
- des pages web (gabarit templates/page.html.j2),
- du CV au format JSON Resume pour chaque langue (base des autres formats).
"""
import calendar
import datetime as dt
import json
import re
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("fr", "en")

FLAGS = {
    "fr": '<svg class="flag" viewBox="0 0 3 2" aria-hidden="true" focusable="false"><rect width="1" height="2" fill="#002654"/>'
          '<rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#CE1126"/></svg>',
    "en": '<svg class="flag" viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
          '<clipPath id="gbc"><path d="M30,15h30v15zv15h-30zh-30v-15zv-15h30z"/></clipPath><path d="M0,0v30h60v-30z" fill="#012169"/>'
          '<path d="M0,0 60,30M60,0 0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 60,30M60,0 0,30" clip-path="url(#gbc)" stroke="#C8102E" stroke-width="4"/>'
          '<path d="M30,0v30M0,15h60" stroke="#fff" stroke-width="10"/><path d="M30,0v30M0,15h60" stroke="#C8102E" stroke-width="6"/></svg>',
}
# Couleurs des pochettes, du bas vers le haut : (tranche gauche, tranche droite, dessus)
SLABS = [("#E6D0E9", "#BE95C6", "#FFFFFF"), ("#E6D0E9", "#BE95C6", "#FFFFFF"), ("#007E92", "#006075", "#00A8BE"),
         ("#E6D0E9", "#BE95C6", "#FFFFFF"), ("#F2AE00", "#C48A00", "#FFC83D")]


def load():
    return yaml.safe_load((ROOT / "cv.yaml").read_text(encoding="utf-8"))


def loc(x, lang):
    """Résout récursivement les valeurs {fr: …, en: …} pour une langue."""
    if isinstance(x, dict):
        if set(x) <= set(LANGS) and x:
            return x.get(lang, x.get("fr"))
        return {k: loc(v, lang) for k, v in x.items()}
    if isinstance(x, list):
        return [loc(v, lang) for v in x]
    return x


def plain(s):
    """Texte HTML de la page → texte brut (fichiers téléchargeables)."""
    return re.sub(r"<[^>]+>", "", s or "").replace("&nbsp;", " ").replace("&amp;", "&")


def h(s):
    """Échappe & < > " sans toucher aux entités déjà présentes (&nbsp;…)."""
    s = re.sub(r"&(?!#?\w+;)", "&amp;", str(s))
    return s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def ym(d):
    d = str(d)
    return (int(d), None) if "-" not in d else tuple(int(x) for x in d.split("-"))


def show(d, present):
    if d is None:
        return present
    y, m = ym(d)
    return f"{y}" if m is None else f"{m:02d}/{y}"


def frac(d, end, now):
    """Position d'une date sur l'axe (années décimales) ; une fin de mois va jusqu'à la fin du mois."""
    if d is None:
        return now
    y, m = ym(d)
    if m is None:
        return float(y)
    return y + (m if end else m - 1) / 12


def now_frac(today):
    dim = calendar.monthrange(today.year, today.month)[1]
    return today.year + (today.month - 1 + (today.day - 1) / dim) / 12


def timeline(cv, lang, today):
    T = cv["timeline"]
    span = T["end"] - T["start"]
    pct = lambda v: f"{(v - T['start']) / span * 100:.2f}"
    rows = list(T["rows"])
    now = now_frac(today)
    bars = []
    for x in cv["experience"]:
        bars.append({"cls": x["row"], "row": rows.index(x["row"]), "s": frac(x.get("start"), False, now),
                     "e": frac(x.get("end"), True, now), "title": loc(x.get("bar") or x["title"], lang)})
    for x in cv["education"]:
        b = x.get("bar")
        if not b:
            continue
        cls = b.get("class", "form")
        bars.append({"cls": cls, "row": rows.index("form"), "s": frac(b.get("start", x.get("start")), False, now),
                     "e": frac(b.get("end", x.get("end")), True, now), "title": loc(b.get("title"), lang)})
    for b in bars:
        b["left"], b["width"] = pct(b["s"]), f"{(b['e'] - b['s']) / span * 100:.2f}"
        b["title"] = plain(b["title"]).replace('"', "&quot;")
    return {"bands": [0, 2, 4], "now": pct(now), "ticks": [{"year": t, "left": pct(t)} for t in T["ticks"]],
            "caps": [loc(T["rows"][r], lang) for r in rows], "bars": bars}


def jsonld(cv, lang, url):
    p = cv["person"]
    d = {"@context": "https://schema.org", "@type": "Person", "name": f'{p["first_name"]} {p["last_name"]}',
         "jobTitle": loc(cv["label"], lang), "url": url, "sameAs": [f'https://github.com/{p["github"]}'],
         "address": {"@type": "PostalAddress", "addressLocality": p["city"], "addressCountry": p["country_code"]},
         "knowsAbout": loc(cv["seo"]["knows_about"], lang)}
    return json.dumps(d, ensure_ascii=False)


def page(cv, lang, today=None):
    today = today or dt.date.today()
    L = loc(cv, lang)
    site = cv["site"]["url"]
    other = "en" if lang == "fr" else "fr"
    url = site if lang == "fr" else site + "en/"
    downloads = []
    for i, d in enumerate(L["downloads"]):
        downloads.append({**d, "y0": 180 - 40 * i, "colors": SLABS[i]})
    skills = []
    for s in L["skills"]:
        if s.get("page") is False:
            continue
        skills.append({**s, "items": [{"name": n, "level": lv} for n, lv in s["items"]]})
    jobs, old = [], []
    for x in L["experience"]:
        j = {**x, "from": show(x.get("start"), L["ui"]["present"]), "to": show(x.get("end"), L["ui"]["present"]),
             "points": x.get("points", [])}
        (old if x.get("compact") else jobs).append(j)
    edu = []
    for x in L["education"]:
        date = x.get("date") or f'{show(x.get("start"), "")} – {show(x.get("end"), L["ui"]["present"])}'
        edu.append({**x, "date": date})
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=False, keep_trailing_newline=True,
                      trim_blocks=False, lstrip_blocks=False)
    env.filters["h"] = h
    return env.get_template("page.html.j2").render(
        lang=lang, other=other, root="" if lang == "fr" else "../", other_href="en/" if lang == "fr" else "../",
        site=cv["site"], site_url=site, url=url, url_fr=site, url_en=site + "en/",
        locale="fr_FR" if lang == "fr" else "en_GB", locale_alt="en_GB" if lang == "fr" else "fr_FR",
        name=f'{L["person"]["first_name"]} {L["person"]["last_name"]}', p=L["person"],
        phone_display=L["person"]["phone"]["display_fr" if lang == "fr" else "display_intl"],
        seo=L["seo"], jsonld=jsonld(cv, lang, url), flag=FLAGS[lang], label=L["label"], role_lines=L["role_lines"],
        downloads=downloads, designed_pdf=L["designed_pdf"], ui=L["ui"], profile=L["profile"], skills=skills,
        projects=L["projects"], tl=timeline(cv, lang, today), jobs=jobs, old=old, education=edu, more=L["more"])


def date_iso(d):
    if d is None:
        return None
    y, m = ym(d)
    return f"{y}" if m is None else f"{y}-{m:02d}"


def resume(cv, lang):
    """CV au format JSON Resume (https://jsonresume.org/schema), dérivé de cv.yaml."""
    L = loc(cv, lang)
    p, ui = L["person"], L["ui"]
    site = cv["site"]["url"]
    url = site if lang == "fr" else site + "en/"
    lv = {k: ui["levels_sr"][k] for k in "pin"}

    def dates(x, d):
        if x.get("start"):
            d["startDate"] = date_iso(x["start"])
        if x.get("end"):
            d["endDate"] = date_iso(x["end"])
        return d

    work, volunteer = [], []
    for x in L["experience"]:
        c = x["cv"]
        pts = [plain(t) for t in x.get("points", [])]
        if x["kind"] == "volunteer":
            volunteer.append(dates(x, {"organization": c["org"], "position": c["position"], "highlights": pts}))
            continue
        w = {"name": c["org"], "position": c["position"]}
        if c.get("location"):
            w["location"] = c["location"]
        dates(x, w)
        if c.get("summary"):
            w["summary"] = pts[0] + "."
            w["highlights"] = []
        elif pts:
            w["highlights"] = pts
        work.append(w)
    status = {"live": "en cours" if lang == "fr" else "ongoing", "stop": "interrompu" if lang == "fr" else "on hold"}
    projects = [{"name": plain(x["title"]), "startDate": x["year"], "description": f'{plain(x["sub"])} ({status[x["status"]]}).',
                 "highlights": [plain(t) for t in x["points"]]} for x in L["projects"]]
    education = []
    for x in L["education"]:
        c = x["cv"]
        e = dates(x, {"institution": c["institution"], "area": c["area"], "studyType": c["type"]})
        if x.get("sub"):
            c0 = plain(x["sub"]).removeprefix("Dont une ").removeprefix("Including a ")
            e["courses"] = [c0[:1].upper() + c0[1:]]
        education.append(e)
    skills = [{"name": s["name"], "keywords": [f"{n} ({lv[l]})" for n, l in s["items"]]} for s in L["skills"]]
    return {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
        "basics": {"name": f'{p["first_name"]} {p["last_name"]}', "label": L["label"], "email": p["email"],
                   "phone": p["phone"]["display_intl"], "url": url, "summary": L["profile"]["summary"],
                   "location": {"city": p["city"], "region": p["region"], "countryCode": p["country_code"]},
                   "profiles": [{"network": "GitHub", "username": p["github"], "url": f'https://github.com/{p["github"]}'}]},
        "work": work, "volunteer": volunteer, "projects": projects, "education": education, "skills": skills,
        "languages": [{"language": x["language"], "fluency": x["fluency"]} for x in L["languages"]],
        "interests": [{"name": x} for x in L["interests"]],
        "meta": {"language": lang, "canonical": url},
    }
