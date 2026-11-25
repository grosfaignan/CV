#!/usr/bin/env python3
"""Génère les fichiers téléchargeables du CV à partir de data/resume.{fr,en}.json.

Sorties (downloads/<langue>/) : PDF compatible ATS, fiche contact vCard,
Word (.docx), Markdown (.md) et JSON Resume (resume.json).

Dépendances : playwright (+ un Chrome/Chromium), Node.js avec le paquet npm « docx ».
    pip install playwright && playwright install chromium && npm install docx
Usage : python3 tools/build.py            (depuis la racine du dépôt)
"""
import html, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "downloads"

T = {
    "fr": {
        "files": {"pdf": "Charles_Delepelaire_CV_ATS.pdf", "docx": "Charles_Delepelaire_CV.docx",
                  "md": "Charles_Delepelaire_CV.md", "vcf": "Charles_Delepelaire.vcf", "json": "resume.json"},
        "profile": "Profil", "skills": "Compétences", "work": "Expérience professionnelle",
        "volunteer": "Bénévolat", "projects": "Projets personnels", "education": "Formation",
        "languages": "Langues", "interests": "Centres d’intérêt", "present": "aujourd’hui",
        "online": "CV en ligne",
        "months": None,
    },
    "en": {
        "files": {"pdf": "Charles_Delepelaire_Resume_ATS.pdf", "docx": "Charles_Delepelaire_Resume.docx",
                  "md": "Charles_Delepelaire_Resume.md", "vcf": "Charles_Delepelaire.vcf", "json": "resume.json"},
        "profile": "Profile", "skills": "Skills", "work": "Work experience",
        "volunteer": "Volunteering", "projects": "Personal projects", "education": "Education",
        "languages": "Languages", "interests": "Interests", "present": "present",
        "online": "Online resume",
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    },
}


def fmt_date(d, t):
    if not d:
        return t["present"]
    p = d.split("-")
    if len(p) == 1:
        return p[0]
    if t["months"]:
        return f'{t["months"][int(p[1]) - 1]} {p[0]}'
    return f"{p[1]}/{p[0]}"


def period(item, t):
    s = fmt_date(item.get("startDate"), t)
    return f'{s} – {fmt_date(item.get("endDate"), t)}'


def contact_line(b):
    loc = b["location"]
    return [f'{loc["city"]}, {loc["region"]}', b["phone"], b["email"], b["url"],
            b["profiles"][0]["url"].replace("https://", "")]


def sections(r, t):
    """Structure neutre partagée par les gabarits : (titre, [entrées])."""
    b = r["basics"]
    out = [(t["profile"], [{"text": b["summary"]}])]
    out.append((t["skills"], [{"text": f'{s["name"]} : ' if r["meta"]["language"] == "fr" else f'{s["name"]}: ',
                               "after": ", ".join(s["keywords"]), "inline": True} for s in r["skills"]]))
    out.append((t["work"], [{"title": f'{w["position"]} – {w["name"]}' + (f', {w["location"]}' if w.get("location") else ""),
                             "date": period(w, t), "summary": w.get("summary"), "bullets": w.get("highlights", [])}
                            for w in r["work"]]))
    out.append((t["volunteer"], [{"title": f'{v["position"]} – {v["organization"]}', "date": period(v, t),
                                  "bullets": v.get("highlights", [])} for v in r["volunteer"]]))
    out.append((t["projects"], [{"title": p["name"], "date": p["startDate"], "summary": p.get("description"),
                                 "bullets": p.get("highlights", [])} for p in r["projects"]]))
    out.append((t["education"], [{"title": f'{e["studyType"]} – {e["area"]}, {e["institution"]}', "date": period(e, t),
                                  "bullets": e.get("courses", [])} for e in r["education"]]))
    sep = " : " if r["meta"]["language"] == "fr" else ": "
    out.append((t["languages"], [{"text": f'{l["language"]}{sep}{l["fluency"]}'} for l in r["languages"]]))
    out.append((t["interests"], [{"text": ", ".join(i["name"] for i in r["interests"])}]))
    return out


# ---------- Markdown ----------
def build_md(r, t):
    b = r["basics"]
    L = [f'# {b["name"]}', "", f'**{b["label"]}**', "", " · ".join(contact_line(b)), ""]
    for title, items in sections(r, t):
        L += [f"## {title}", ""]
        for it in items:
            if it.get("inline"):
                L.append(f'- **{it["text"].rstrip(" :").rstrip(":")}** : {it["after"]}' if r["meta"]["language"] == "fr"
                         else f'- **{it["text"].rstrip(": ")}**: {it["after"]}')
                continue
            if "text" in it:
                L += [it["text"], ""]
                continue
            L += [f'### {it["title"]}', f'*{it["date"]}*', ""]
            if it.get("summary"):
                L += [it["summary"], ""]
            L += [f"- {x}" for x in it.get("bullets", [])]
            if it.get("bullets"):
                L.append("")
        if items and items[0].get("inline"):
            L.append("")
    return "\n".join(L).rstrip() + "\n"


# ---------- vCard ----------
def vesc(s):
    return s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def build_vcf(r, t):
    b = r["basics"]
    first, last = b["name"].split(" ", 1)
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"N:{vesc(last)};{vesc(first)};;;", f"FN:{vesc(b['name'])}",
             f"TITLE:{vesc(b['label'])}", f"TEL;TYPE=CELL:{b['phone'].replace(' ', '')}",
             f"EMAIL;TYPE=INTERNET:{b['email']}", f"URL:{b['url']}",
             f"X-SOCIALPROFILE;TYPE=github:{b['profiles'][0]['url']}",
             f"ADR;TYPE=HOME:;;;{vesc(b['location']['city'])};{vesc(b['location']['region'])};;France",
             f"NOTE:{vesc(t['online'] + ' : ' + b['url'] if r['meta']['language'] == 'fr' else t['online'] + ': ' + b['url'])}",
             "END:VCARD"]
    return "\r\n".join(lines) + "\r\n"


# ---------- Word : tools/docx.js (mise en page aux couleurs du site) ----------


# ---------- PDF compatible ATS (une colonne, texte réel) ----------
LEVELS = {"pratique": "p", "hands-on": "p", "bon": "p", "good": "p", "initiation": "i", "beginner": "i"}


def build_ats_html(r, t):
    """PDF compatible ATS, mis en page aux couleurs du site : une seule colonne, texte réel,
    ordre de lecture = ordre du document, aucun texte dans une image ni tableau."""
    b = r["basics"]
    e = html.escape
    fr = r["meta"]["language"] == "fr"
    font = (ROOT / "fonts").as_uri()
    css = (
        f"@font-face{{font-family:IS;font-weight:400;src:url({font}/InstrumentSans-400.woff2)}}"
        f"@font-face{{font-family:IS;font-weight:600;src:url({font}/InstrumentSans-600.woff2)}}"
        f"@font-face{{font-family:IS;font-weight:400;font-style:italic;src:url({font}/InstrumentSans-400-italic.woff2)}}"
        f"@font-face{{font-family:MR;font-weight:700;src:url({font}/Manrope-700.woff2)}}"
        f"@font-face{{font-family:UB;font-weight:600;src:url({font}/Unbounded-600.woff2)}}"
        "@page{size:A4;margin:11mm 14mm 11mm}"
        "*{box-sizing:border-box}body{margin:0;font:10pt/1.4 IS,Arial,sans-serif;color:#52565F}"
        "p,li{text-align:justify;hyphens:manual;margin:0}"
        ".hero{background:#84488C;color:#fff;border-radius:10px;padding:14px 22px 12px;margin-bottom:10px}"
        "h1{font:700 24pt/1.05 MR,Arial,sans-serif;margin:0 0 8px;letter-spacing:.005em}"
        ".label{display:inline-block;background:#FFC83D;color:#52565F;font:600 11pt/1.3 UB,Arial,sans-serif;padding:4px 10px;margin:0 0 9px;letter-spacing:-.01em}"
        ".contact{font-size:9pt;color:#fff;text-align:left}.contact a{color:#FFC83D;text-decoration:none;font-weight:600}"
        ".lede{border-left:5px solid #0091A6;background:#F3E9F4;padding:8px 12px;border-radius:0 8px 8px 0}"
        "h2{font:600 12pt/1.2 UB,Arial,sans-serif;color:#84488C;border-bottom:2.5px solid #FFC83D;margin:10px 0 6px;padding-bottom:2px;break-after:avoid;letter-spacing:-.01em}"
        ".legend{font-size:8.5pt;margin:0 0 5px}"
        ".sk{margin:0 0 3px;line-height:1.7;text-align:left}.sk b{color:#5A2A62;margin-right:4px}"
        ".pill{display:inline;padding:1px 5px;border-radius:4px;font-size:8.8pt;white-space:nowrap}"
        ".pill.p{background:#84488C;color:#fff;font-weight:600}.pill.i{background:#E9D7ED;color:#84488C;font-weight:600}.pill.n{color:#7A7E8B;font-style:italic}"
        ".pill small{font-size:7.5pt;font-weight:400;opacity:.85}"
        ".item{border-left:3.5px solid var(--a);padding:1px 0 1px 10px;margin:0 0 6px;break-inside:avoid}"
        ".head{display:flex;justify-content:space-between;gap:12px;align-items:baseline}"
        "h3{font:600 10.2pt/1.3 IS,Arial,sans-serif;color:#5A2A62;margin:0}"
        ".date{font-weight:600;color:#84488C;font-size:8.8pt;white-space:nowrap;margin:0}"
        ".sub{font-style:italic;color:#7A7E8B;font-size:9pt;margin:1px 0 2px;text-align:left}"
        "ul{margin:2px 0 0 15px;padding:0}li{margin:1px 0}li::marker{color:#0091A6}"
        ".short{margin:0 0 3px;text-align:left}.short b{color:#84488C}"
    )
    acc = {2: "#84488C", 3: "#E07A5F", 4: "#0091A6", 5: "#FFC83D"}
    contact = contact_line(b)
    H = [f'<!doctype html><html lang="{r["meta"]["language"]}"><head><meta charset="utf-8">',
         f'<title>{e(b["name"])} – {e(b["label"])}</title><style>{css}</style></head><body>',
         '<header class="hero">', f'<h1>{e(b["name"])}</h1>', f'<p class="label">{e(b["label"])}</p>',
         '<p class="contact">' + " · ".join(e(x) for x in contact[:3]) +
         f' · <a href="{e(b["url"])}">{e(b["url"].replace("https://", ""))}</a> · {e(contact[4])}</p>', "</header>"]
    for n, (title, items) in enumerate(sections(r, t)):
        if n == 6:   # langues et centres d'intérêt sous un seul titre
            title = f'{title} {"et" if fr else "and"} {t["interests"][0].lower() + t["interests"][1:]}'
        if n != 7:
            H.append(f"<h2>{e(title)}</h2>")
        if n == 7:
            H.append(f'<p class="short"><b>{e(t["interests"])}</b>{" : " if fr else ": "}{e(items[0]["text"])}</p>')
            continue
        if n == 0:
            H.append(f'<p class="lede">{e(items[0]["text"])}</p>')
            continue
        if n == 1:
            lv = ("Pratique", "Initiation", "Notions") if fr else ("Hands-on", "Beginner", "Basic knowledge")
            H.append('<p class="legend">' + " ".join(f'<span class="pill {c}">{e(x)}</span>' for c, x in zip("pin", lv)) + "</p>")
            for s in r["skills"]:
                pills = []
                for k in s["keywords"]:
                    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", k)
                    name, lvl = (m.group(1), m.group(2)) if m else (k, "")
                    c = next((v for key, v in LEVELS.items() if lvl.lower().startswith(key)), "n")
                    pills.append(f'<span class="pill {c}">{e(name)}' + (f' <small>({e(lvl)})</small>' if lvl else "") + "</span>")
                H.append(f'<p class="sk"><b>{e(s["name"])}</b> ' + " ".join(pills) + "</p>")
            continue
        if n >= 6:
            for it in items:
                k, _, v = it["text"].partition(" : " if fr else ": ")
                H.append(f'<p class="short"><b>{e(k)}</b>{" : " if fr else ": "}{e(v)}</p>' if v else f'<p class="short">{e(k)}</p>')
            continue
        for it in items:
            H.append(f'<div class="item" style="--a:{acc.get(n, "#84488C")}"><div class="head"><h3>{e(it["title"])}</h3>'
                     f'<p class="date">{e(it["date"])}</p></div>')
            if it.get("summary"):
                H.append(f'<p class="sub">{e(it["summary"])}</p>')
            if it.get("bullets"):
                H.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in it["bullets"]) + "</ul>")
            H.append("</div>")
    H.append("</body></html>")
    # Apostrophes droites : certains logiciels de tri lisent mal l'apostrophe typographique
    return "".join(H).replace("’", "'")


def build_pdf(html_str, path, browser):
    tmp = path.with_suffix(".tmp.html")
    tmp.write_text(html_str, encoding="utf-8")
    page = browser.new_page()
    page.goto(tmp.as_uri()); page.wait_for_timeout(300)
    page.pdf(path=str(path), format="A4", prefer_css_page_size=True, print_background=True, tagged=True, outline=True)
    page.close(); tmp.unlink()


def main():
    from playwright.sync_api import sync_playwright
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or None
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch()
        for lang, t in T.items():
            r = json.loads((ROOT / "data" / f"resume.{lang}.json").read_text(encoding="utf-8"))
            d = OUT / lang; d.mkdir(parents=True, exist_ok=True)
            f = t["files"]
            (d / f["json"]).write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (d / f["md"]).write_text(build_md(r, t), encoding="utf-8")
            (d / f["vcf"]).write_text(build_vcf(r, t), encoding="utf-8", newline="")
            subprocess.run(["node", str(ROOT / "tools" / "docx.js"), lang, str(d / f["docx"])], check=True, cwd=ROOT)
            build_pdf(build_ats_html(r, t), d / f["pdf"], browser)
            print(lang, "→", ", ".join(sorted(x.name for x in d.iterdir())))
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
