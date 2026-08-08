# Éditions Particulières — monorepo V1

Extraction Notion → Google Drive → flipcards → site internet.

**Traçabilité (norme) :** [`docs/tracabilite/`](docs/tracabilite/) — historique détaillé, architecture, index des conversations, journal de nettoyage.

## Structure

```
editions-particulieres/
├── packages/ep_core/     # Config + chemins (Google Drive)
├── extract/              # Extraction Notion → Word/PDF/HTML
│   ├── word/             # Pipeline .docx / PDF
│   ├── html/             # Pipeline site (manuel, dictionnaire, arrêts)
│   └── pull/             # Caches JSON Drive
├── flipcards/            # Flipcards jurisprudence
├── site/
│   ├── templates/        # Gabarits HTML + scripts de build
│   ├── worker/           # Auth Cloudflare
│   └── host-repo/        # Miroir optionnel GitHub Pages
├── mobile/               # App Expo flipcards
├── config/               # Chemins, Notion (.example → copier)
├── scripts/              # Pipelines PowerShell
└── docs/tracabilite/     # Mémoire officielle du chantier
```

## App mobile

```powershell
cd mobile
npm install
npm run sync-data   # JSON depuis EP_OUTPUT_ROOT / Drive / output/
npm start
```

Ou `mobile\Lancer.ps1`.

## Sorties (Google Drive)

Par défaut : `G:/Mon Drive/Editions Particulieres/`

| Dossier | Contenu |
|---------|---------|
| `export/` | Word, PDF, HTML par registre |
| `matrices/` | CSV/JSON jurisprudence + flipcards |
| `flipcards/output/` | HTML/JSON flipcards générés |
| `site-build/` | Staging avant publication |

Configurer via `.env` (`EP_OUTPUT_ROOT`) ou `config/paths.json`.

## Démarrage

```powershell
copy .env.example .env
copy config\paths.json.example config\paths.json
copy config\notion.json.example config\notion.json
.\scripts\setup_output_dirs.ps1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### GUI

Double-clic `Lancer-GUI.bat` ou `python -m gui`.

Registres : Manuel, Fiches, Méthode, Formule, Glossaire, Jurisprudence — Word, PDF, postlink, attacher styles.

- **Word (.docx)** : format principal pour « Générer ».
- **PDF** : post-traitement via Microsoft Word (pywin32).
- **HTML site** : `python export_html.py` / `export_dictionnaire.py` / `export_arrets.py` (aussi CI).
- **Attacher styles** : `Editions_Particulieres.dotx`.

```powershell
python -m extract.word.convert_pdf --out "G:\Mon Drive\Editions Particulieres\export"
.\scripts\build_site.ps1
```

Site live : `https://www.editions-particulieres.fr`

## Anciens dépôts (archives)

Ne plus modifier. À zipper sur Drive puis retirer du Bureau — détail : `docs/tracabilite/NETTOYAGE.md`.

- `notion_to_word` → `extract/` + `gui/`
- `flipcards-jp` → `flipcards/` + `site/` + `mobile/`
