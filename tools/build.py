#!/usr/bin/env python3
"""Génère les fichiers téléchargeables du CV à partir de data/resume.{fr,en}.json.

Sorties (downloads/<langue>/) : PDF compatible ATS, fiche contact vCard,
Word (.docx), Markdown (.md) et JSON Resume (resume.json).

Dépendances : playwright (+ un Chrome/Chromium), Node.js avec le paquet npm « docx ».
    pip install playwright && playwright install chromium && npm install docx
Usage : python3 tools/build.py            (depuis la racine du dépôt)
"""
import html, json, os, shutil, subprocess, sys
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
def build_ats_html(r, t):
    b = r["basics"]
    e = html.escape
    font = (ROOT / "fonts").as_uri()
    H = [f'<!doctype html><html lang="{r["meta"]["language"]}"><head><meta charset="utf-8">',
         f'<title>{e(b["name"])} – {e(b["label"])}</title><style>',
         f"@font-face{{font-family:IS;font-weight:400;src:url({font}/InstrumentSans-400.woff2)}}",
         f"@font-face{{font-family:IS;font-weight:600;src:url({font}/InstrumentSans-600.woff2)}}",
         f"@font-face{{font-family:IS;font-weight:400;font-style:italic;src:url({font}/InstrumentSans-400-italic.woff2)}}",
         "@page{size:A4;margin:16mm 18mm}body{font:10pt/1.45 IS,Arial,sans-serif;color:#222}",
         "h1{font-size:20pt;margin:0}p,li{text-align:left;hyphens:manual}.label{font-weight:600;font-size:11.5pt;margin:2px 0 4px}",
         ".contact{margin:0 0 6px;color:#444}h2{font-size:12pt;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid #999;margin:14px 0 6px;padding-bottom:2px;break-after:avoid}",
         "h3{font-size:10.5pt;margin:8px 0 0;break-after:avoid}.date{font-style:italic;color:#555;margin:0}ul{margin:3px 0 0 16px;padding:0}li{margin:1px 0}",
         ".item{break-inside:avoid}p{margin:3px 0}</style></head><body>",
         f'<h1>{e(b["name"])}</h1><p class="label">{e(b["label"])}</p><p class="contact">{" | ".join(e(x) for x in contact_line(b))}</p>']
    for title, items in sections(r, t):
        H.append(f"<h2>{e(title)}</h2>")
        inline = [it for it in items if it.get("inline")]
        if inline:
            H.append("<ul>" + "".join(f'<li><b>{e(it["text"])}</b>{e(it["after"])}</li>' for it in inline) + "</ul>")
            continue
        for it in items:
            if "text" in it:
                H.append(f'<p>{e(it["text"])}</p>')
                continue
            H.append(f'<div class="item"><h3>{e(it["title"])}</h3><p class="date">{e(it["date"])}</p>')
            if it.get("summary"):
                H.append(f'<p>{e(it["summary"])}</p>')
            if it.get("bullets"):
                H.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in it["bullets"]) + "</ul>")
            H.append("</div>")
    H.append("</body></html>")
    return "".join(H)


def build_pdf(html_str, path, browser):
    tmp = path.with_suffix(".tmp.html")
    tmp.write_text(html_str, encoding="utf-8")
    page = browser.new_page()
    page.goto(tmp.as_uri()); page.wait_for_timeout(300)
    page.pdf(path=str(path), format="A4", prefer_css_page_size=True, print_background=False)
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
