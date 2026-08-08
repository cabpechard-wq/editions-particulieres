# Éditions Particulières — monorepo V1

Extraction Notion → Google Drive → flipcards → site internet.

## Structure

```
editions-particulieres/
├── packages/ep_core/     # Config + chemins (Google Drive)
├── extract/              # Extraction Notion → Word/PDF/HTML (ex notion_to_word)
├── flipcards/            # Flipcards jurisprudence
├── site/
│   ├── templates/        # Gabarits HTML + scripts de build
│   ├── worker/           # Auth Cloudflare
│   └── host-repo/        # Déploiement GitHub Pages
├── mobile/               # App Expo flipcards (npm start dans mobile/)
├── config/               # Chemins, Notion, site (.example → copier)
└── scripts/              # Pipelines PowerShell
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
.\scripts\setup_output_dirs.ps1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### GUI

Double-clic `Lancer-GUI.bat` ou `python -m gui`.

Interface identique à l'ancien `notion_to_word` : registres (Manuel, Fiches, Méthode, Formule, Glossaire, Jurisprudence), mode fiches, combiner, export Word, post-traitement PDF, postlink, attacher styles.

- **Word (.docx)** : format principal pour « Générer ».
- **PDF** : post-traitement des `.docx` via Microsoft Word (pywin32) — case « Générer aussi PDF » ou bouton « Convertir en PDF ».
- **HTML** : option visible, non branchée.
- **Attacher styles** : opérationnel (`Editions_Particulieres.dotx`).
- **Actualiser la liste** : charge les fiches depuis Notion (bases `config/notion.json`).

Conversion PDF en ligne de commande :

```powershell
python -m extract.word.convert_pdf --out "G:\Mon Drive\Editions Particulieres\export"
```

## Anciens dépôts

- `notion_to_word` → `extract/`
- `flipcards-jp` → `flipcards/` + `site/` + `mobile/`
