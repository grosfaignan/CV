# CV – Charles Delepelaire

**Technicien support et exploitation informatique junior – Paris**

👉 Version en ligne : https://grosfaignan.github.io/CV/
📄 Version PDF : [CV_Charles_Delepelaire.pdf](CV_Charles_Delepelaire.pdf)

En reconversion vers le support et l'exploitation informatique, avec l'administration de systèmes Linux pour horizon. Recherche une première expérience en support et exploitation informatique, ou en administration Linux junior.

- **Systèmes** : Debian, Ubuntu, Fedora, Windows
- **Automatisation** : Bash, Git, GitHub Actions
- **Virtualisation** : Docker, KVM
- **Supervision** : Grafana, Prometheus, Loki
- **Formation en cours** : CNAM – réseau, sécurité informatique et mathématiques

## Fichiers téléchargeables

Source unique : `data/resume.fr.json` et `data/resume.en.json` (format [JSON Resume](https://jsonresume.org/schema)).
Après toute modification, régénérer les fichiers de `downloads/` :

```bash
pip install python-docx playwright && playwright install chromium
python3 tools/build.py
```

Formats produits pour chaque langue : PDF compatible ATS, fiche contact vCard, Word, Markdown, JSON Resume.
La page web (`index.html`, `en/index.html`) reste à mettre à jour à la main.
