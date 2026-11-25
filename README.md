# CV – Charles Delepelaire

**Technicien support et exploitation informatique junior – Paris**

👉 En ligne : https://grosfaignan.github.io/CV/ (FR) · https://grosfaignan.github.io/CV/en/ (EN)

## Source unique : `cv.yaml`

Tout le contenu du CV (français et anglais) est dans **un seul fichier, `cv.yaml`**.
Tout le reste est généré à partir de lui : ne modifiez pas les fichiers générés à la main.

| Généré | Fichier(s) |
|---|---|
| Pages web | `index.html`, `en/index.html` (gabarit `templates/page.html.j2`, frise calculée depuis les dates) |
| PDF mis en page | `CV_Charles_Delepelaire.pdf`, `en/Resume_Charles_Delepelaire_EN.pdf` |
| Pochettes de téléchargement | `downloads/<langue>/` : PDF ATS, Word, Markdown, vCard, `resume.json` (JSON Resume) |

Écriture dans `cv.yaml` : un texte identique dans les deux langues s'écrit tel quel, sinon
`{fr: "…", en: "…"}`. Dates `AAAA` ou `AAAA-MM` ; pas de date de fin = « aujourd'hui ».
Niveaux de compétence : `p` pratique, `i` initiation, `n` notions.

## Mise à jour

**Automatique** : modifiez `cv.yaml` (même depuis l'interface web de GitHub) et envoyez.
L'action « Régénérer le CV » (`.github/workflows/build-cv.yml`) reconstruit tout et l'enregistre dans la branche.

**En local** :

```bash
pip install -r requirements.txt && python -m playwright install chromium
npm install
python3 tools/build.py              # tout
python3 tools/build.py --pages-only # pages web seulement (rapide)
```

Après une modification de `style.css` ou `pile.js`, incrémentez `site.asset_version` dans `cv.yaml`
pour que les navigateurs rechargent les fichiers.

## Organisation

- `cv.yaml` : contenu (source unique)
- `templates/page.html.j2` : structure HTML des pages
- `style.css`, `pile.js`, `fonts/` : apparence et animation de la pile de pochettes
- `tools/cvdata.py` : lecture de `cv.yaml`, pages web, JSON Resume
- `tools/build.py` : génération complète (PDF, PDF ATS, Markdown, vCard) ; `tools/docx.js` : Word
