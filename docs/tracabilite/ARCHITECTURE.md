# Architecture actuelle (référence opérationnelle)

État au **8 août 2026**. Complète `HISTORIQUE.md` (le « pourquoi ») par le « comment lancer ».

---

## 1. Arborescence monorepo

```
editions-particulieres/
├── packages/ep_core/     # Config, chemins Drive, registres, client Notion
├── extract/
│   ├── word/             # Pipeline .docx / PDF (live)
│   ├── html/             # Pipeline site manuel / dictionnaire / arrêts (live)
│   ├── pull/             # JSON caches Drive (manuel, jurisprudence, index)
│   └── templates/        # .dotx (généré, souvent gitignored)
├── gui/                  # Tkinter — python -m gui / Lancer-GUI.bat
├── flipcards/            # Matrice + générateur HTML/JSON
├── site/
│   ├── templates/        # Gabarits + CSS + JS (nav, thème, TTS, auth)
│   ├── themes/           # Chartes live (sous templates/themes/)
│   ├── worker/           # Cloudflare Auth
│   ├── dist/site/        # Build local (gitignored)
│   └── host-repo/        # Miroir optionnel Pages (gitignored contenu)
├── mobile/               # Expo flipcards offline
├── config/               # paths.json, notion.json (+ .example)
├── scripts/              # PowerShell / Python ops
├── export_html.py
├── export_dictionnaire.py
├── export_arrets.py
└── docs/tracabilite/     # Norme d’historique (ce dossier)
```

---

## 2. Registres Notion

| Clé | Label site / GUI | DB config |
|-----|------------------|-----------|
| `manuel` | Cours | `databases.manuel` |
| `fiches` | Fiches | `databases.fiches` |
| `methodo` | Méthode | `databases.methodo` |
| `formule` | Formule | `databases.formule` |
| `index` | Dictionnaire / glossaire | `databases.index` |
| `arrets` | Jurisprudence / Arrêts | `databases.jurisprudence` |

Résolution : `config/notion.json` → variables d’environnement → fallbacks code.

---

## 3. Commandes usuelles

```powershell
# Environnement
copy .env.example .env
copy config\paths.json.example config\paths.json
copy config\notion.json.example config\notion.json
.\scripts\setup_output_dirs.ps1
.\.venv\Scripts\activate
pip install -r requirements.txt

# Extraction Word (GUI)
python -m gui

# Pull JSON Drive
python -m extract manuel
python -m extract jurisprudence
python -m extract index

# HTML site
python export_html.py
python export_dictionnaire.py
python export_arrets.py

# Flipcards
python -m flipcards.export_matrice
python -m flipcards

# Assemblage site local
.\scripts\build_site.ps1
.\scripts\serve_site.ps1

# Mobile
cd mobile; npm install; npm run sync-data; npm start
```

CI : `.github/workflows/deploy-pages.yml` sur `main`.

---

## 4. Site publié

| Élément | Valeur |
|---------|--------|
| Domaine canonique | `https://www.editions-particulieres.fr` |
| Pages fallback | `https://cabpechard-wq.github.io/editions-particulieres/` |
| Auth API | Worker `flipcards-auth` (URL dans `site/config.json`) |
| Paiement | Stripe Payment Links (mensuel / semestriel) |
| Contenu pédagogique | `/manuel/`, `/dictionnaire/`, `/arrets/`, `/flipcards/`, `/demo/` |

### Parcours abonné

1. `/checkout/` → Stripe  
2. `/merci/?session_id=…` → mot de passe  
3. `/flipcards/` avec Bearer  
4. Reconnexion `/membre/`

---

## 5. Config à ne pas committer

- `.env` (Notion, Stripe, Resend, AUTH)
- `config/paths.json`, `config/notion.json`
- `site/config.json`
- `site/abonnes.json`, secrets Worker

Toujours partir des `.example`.

---

## 6. Scripts `scripts/` (rôle)

| Script | Rôle |
|--------|------|
| `setup_output_dirs.ps1` | Crée l’arborescence Drive |
| `refresh_extraction.ps1` | `python -m extract` |
| `refresh_flipcards.ps1` | Matrice flipcards |
| `build_site.ps1` | build_assets + merges + gate membre |
| `merge_*_site.ps1` | Copie Drive `export_site` → `dist` |
| `fix_legacy_crumbs.py` | Nettoie fils d’Ariane legacy |
| `patch_site_scripts.py` | Injecte TTS |
| `sync_host_repo.ps1` | Miroir `host-repo` |
| `serve_site.ps1` | HTTP local |
| `print_ovh_dns.ps1` | Checklist DNS OVH |
| `migrate_account_to_kv.ps1` | Compte → KV Worker |

---

## 7. Entrées obsolètes (ne plus utiliser)

Documentées pour éviter les régressions — détail dans `NETTOYAGE.md` / `HISTORIQUE.md` :

- `site/export_manuel.py` (pandoc)
- Lemon Squeezy / Sotion / Netlify setup
- Packages `extract/manuel|fiches|…` vides (supprimés)
- Développer dans `Desktop/notion_to_word` ou `Desktop/flipcards-jp`
