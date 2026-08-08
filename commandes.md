# Éditions Particulières — commandes.md

Fiche opérationnelle locale. Historique détaillé : `docs/tracabilite/`.

---

## 1. Architecture (vue rapide)

```
Notion (bases éditoriales)
    │
    ├─► extract/word + GUI ──► Word / PDF ──► Google Drive /export/
    ├─► extract/pull ────────► JSON caches ──► Drive
    ├─► extract/html ────────► HTML Cours / Dictionnaire / Arrêts
    └─► flipcards ───────────► matrice + HTML/JSON
                                    │
                                    ▼
                         site/build_assets + merges
                                    │
                                    ▼
                    site/dist/site  →  GitHub Pages
                    www.editions-particulieres.fr
                                    │
                    Stripe + Worker auth → /flipcards/ (membres)
                    mobile/ (Expo, offline)
```


| Couche                                       | Rôle                                    |
| -------------------------------------------- | --------------------------------------- |
| `packages/ep_core`                           | Chemins Drive, registres, client Notion |
| `extract/`                                   | Extraction (`word/`, `html/`, `pull/`)  |
| `gui/`                                       | Interface Windows (Word / PDF)          |
| `flipcards/`                                 | Matrice + générateur cartes             |
| `site/`                                      | Templates, build, Worker auth           |
| `mobile/`                                    | App Expo                                |
| `config/` + `.env`                           | Secrets et IDs (jamais committer)       |
| `scripts/`                                   | Orchestration PowerShell                |
| Drive `G:\Mon Drive\Editions Particulieres\` | Sorties binaires                        |


**Site live :** `https://www.editions-particulieres.fr`  
**CI :** push `main` → `.github/workflows/deploy-pages.yml`

---

## 2. Structures programme ↔ site

### Registres Notion → sorties


| Registre               | Programme                                                        | Sortie Drive / site                   |
| ---------------------- | ---------------------------------------------------------------- | ------------------------------------- |
| Manuel (Cours)         | GUI Word · `export_html.py` · `extract pull manuel`              | `/manuel/`                            |
| Index (Dictionnaire)   | GUI Word · `export_dictionnaire.py` · `pull index`               | `/dictionnaire/`                      |
| Arrêts (Jurisprudence) | GUI Word · `export_arrets.py` · `pull jurisprudence` · flipcards | `/arrets/` + `/flipcards/` + `/demo/` |
| Fiches                 | GUI Word seulement                                               | pas encore de section site            |
| Méthode                | GUI Word seulement                                               | « À venir » sur l’accueil             |
| Formule                | GUI Word seulement                                               | pas de section site dédiée            |


### Routes site ↔ modules


| URL                                           | Source programme                                  |
| --------------------------------------------- | ------------------------------------------------- |
| `/`                                           | `site/templates/home.html` via `build_assets.py`  |
| `/manuel/`                                    | `extract/html` → merge Drive `export_site/manuel` |
| `/dictionnaire/`                              | idem glossaire                                    |
| `/arrets/`                                    | idem arrêts                                       |
| `/demo/`                                      | 8 cartes publiques (`build_assets` + matrice)     |
| `/flipcards/`                                 | pack membres + gate Worker                        |
| `/checkout/` `/merci/` `/membre/`             | commerce Stripe + auth                            |
| `/bibliotheque/` `/ressources/` `/exercices/` | pages marketing templates                         |
| `/cgv/` `/mentions-legales/`                  | `site/legal/`                                     |


### Config


| Fichier              | Usage                                               |
| -------------------- | --------------------------------------------------- |
| `.env`               | `EP_OUTPUT_ROOT`, `NOTION_*`, secrets Stripe/Resend |
| `config/paths.json`  | Dossiers Drive                                      |
| `config/notion.json` | URLs / IDs des 6 bases                              |
| `site/config.json`   | URLs site, Stripe links, `auth.api_url`             |


---

## 3. Commandes PowerShell

Toujours depuis la racine du monorepo, venv activé :

```powershell
cd C:\Users\anton\Projects\editions-particulieres
.\.venv\Scripts\Activate.ps1
```

### 3.1 Première installation

```powershell
copy .env.example .env
copy config\paths.json.example config\paths.json
copy config\notion.json.example config\notion.json
# Éditer .env + config\notion.json (token + IDs)

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

.\scripts\setup_output_dirs.ps1   # crée l’arborescence Drive
```

### 3.2 Extraction Word / PDF / HTML (GUI)

**Word / PDF : uniquement en local** (Windows + Microsoft Word installé).  
Pas d’export Word/PDF via GitHub Actions (pas de Word COM sur les runners Linux).  
CI GitHub = site HTML Pages uniquement.

```powershell
python -m gui
# ou double-clic Lancer-GUI.bat
```

**Word** — format `Word (.docx)` → Générer (PDF optionnel via case / bouton).

**HTML site** — même UX :
1. Cocher Cours / Glossaire / Jurisprudence (ou fiches ciblées)
2. Format → `HTML (site)`
3. Bouton **Publier HTML** (dossier = Drive `export/site/` par défaut)
4. Case **Fusionner dans site/dist/site** (cochée par défaut) → copie vers le build local

Prérequis fusion : avoir déjà un `site\dist\site` (`.\scripts\build_site.ps1` une fois).  
Puis `.\scripts\serve_site.ps1` pour contrôler.

```powershell
# PDF en masse depuis un dossier d’export Word
python -m extract.word.convert_pdf --out "G:\Mon Drive\Editions Particulieres\export"
```

### 3.3 Caches JSON (Drive)

```powershell
.\scripts\refresh_extraction.ps1              # manuel + jurisprudence + index
.\scripts\refresh_extraction.ps1 -Register manuel -Limit 5   # test
python -m extract jurisprudence
python -m extract index
```

### 3.4 Contenu HTML du site

```powershell
python export_html.py                 # Cours → Drive export_site/manuel (+ dist si configuré)
python export_dictionnaire.py         # Dictionnaire
python export_arrets.py               # Arrêts
# Options utiles : --limit N
```

### 3.5 Flipcards

```powershell
.\scripts\refresh_flipcards.ps1       # matrice Notion → CSV/JSON
python -m flipcards                   # HTML + JSON (cartes)
python -m flipcards --offline         # sans rappeler Notion
python -m flipcards --limit 20
```

### 3.6 Pipeline unique (recommandé avant push)

Un seul geste : JSON Drive → HTML → flipcards → assemblage `dist/site`.

```powershell
.\scripts\build_all.ps1
.\scripts\build_all.ps1 -Limit 5              # test Notion (pull + HTML + flipcards)
.\scripts\build_all.ps1 -SkipPull             # saute les caches JSON
.\scripts\build_all.ps1 -SkipHtml             # saute Cours/Dico/Arrêts
.\scripts\build_all.ps1 -SkipFlipcards
.\scripts\build_all.ps1 -OfflineFlipcards     # cartes sans rappel Notion
.\scripts\serve_site.ps1                      # contrôler localement après
```

### 3.7 Assembler seulement (sans re-exporter Notion)

```powershell
.\scripts\build_site.ps1              # build_assets + merges + gate + index recherche
.\scripts\serve_site.ps1              # HTTP local sur site\dist\site
```

Champ **Rechercher** dans le bandeau (Cours + Dictionnaire + Arrêts).  
Régénérer l’index seul :

```powershell
python site/build_search_index.py
```

Merges seuls (si l’HTML Drive est déjà à jour) :

```powershell
.\scripts\merge_manuel_site.ps1
.\scripts\merge_dictionnaire_site.ps1
.\scripts\merge_arrets_site.ps1
python site/build_search_index.py
```

### 3.8 Déploiement

```powershell
git add -A
git commit -m "…"
git push origin main                  # déclenche Pages + smoke CI

# Refresh Notion forcé en CI (manuel + dico) :
gh workflow run deploy-pages.yml -f refresh_notion=true
```

Garde-fous CI :
1. **Pré-upload** : `python site/smoke_artifact.py` (artefact dist)
2. **Post-deploy** : `python site/smoke_live.py` (curl www + fallback)
3. Local : `python site/test_commerce.py` (artefact + URLs config)

```powershell
python site/smoke_artifact.py
python site/smoke_live.py --retries 3
python site/test_commerce.py
```

Miroir optionnel `host-repo` :

```powershell
.\scripts\sync_host_repo.ps1
```

### 3.9 Auth / comptes / DNS

```powershell
.\scripts\migrate_account_to_kv.ps1   # migrer un abonné vers le Worker KV
.\scripts\print_ovh_dns.ps1           # checklist DNS OVH → GitHub Pages

cd site\worker
npx wrangler secret put STRIPE_SECRET_KEY
npx wrangler secret put RESEND_API_KEY
npx wrangler secret put AUTH_SECRET
npx wrangler deploy
```

### 3.10 App mobile

```powershell
cd mobile
npm install
npm start                             # sync-data auto (prestart) puis Expo
# ou : ..\mobile\Lancer.ps1
npm run sync-data                     # sync manuel seul
```

Filtres alignés web : **1 thème** (choix unique) · **Notions** (multi) · **Importance ★** (multi).  
`sync-data` copie le dernier JSON flipcards + complète `importance_level` si manquant.

### 3.11 Lab chartes (hors prod)

```powershell
.\scripts\serve_theme_proposals.ps1   # localhost:8777 — design-proposals/
```

### 3.12 Enchaînement typique « j’ai modifié Notion »

```powershell
.\.venv\Scripts\Activate.ps1
.\scripts\build_all.ps1               # tout le pipeline local
.\scripts\serve_site.ps1              # contrôler
git push origin main                  # publier
```

---

## 4. Développements attendus

Travaux déjà annoncés / amorcés (accueil « À venir », registres prêts côté Word, dettes connues).


| Priorité | Sujet                                         | Attendu                                                                                                                     |
| -------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **A1**   | **Fiches thématiques** sur le site            | Export HTML + section `/…` + débloquer la tuile accueil (registre `fiches` déjà en GUI)                                     |
| **A2**   | **Méthode / exercices**                       | Publier méthodo (et outils type frises / trames) depuis Notion → pages site                                                 |
| **A3**   | **Formules**                                  | Brancher le registre `formule` au site ou à une rubrique Amphi / BU                                                         |
| **A4**   | **Pull JSON** pour fiches / methodo / formule | Aujourd’hui seuls manuel, jurisprudence, index ont `extract.pull`                                                           |
| **A5**   | **Sécurité secrets**                          | Rotation Notion + Stripe (clés déjà passées par l’historique git) ; vérifier qu’aucun secret n’est re-commit                |
| **A6**   | **Archives Desktop**                          | ZIP Drive puis suppression `notion_to_word` + `flipcards-jp` ; archiver conversations (`docs/tracabilite/CONVERSATIONS.md`) |
| **A7**   | **Comptes membres**                           | Vérifier migration KV après déplacements ; parcours Stripe → `/merci/` → `/flipcards/` stable                               |


---

## 5. Développements suggérés

Améliorations utiles, non bloquantes pour la V1 live.


| Idée                                                                    | Intérêt                                        |
| ----------------------------------------------------------------------- | ---------------------------------------------- |
| **Chartes abonnés** (Lab `design-proposals` → thèmes live)              | Expérience différenciée par offre / préférence |
| **Index croisé renforcé** (Notions ↔ arrêts ↔ chapitres)                | Déjà amorcé via `site_links` — à enrichir      |
| **TTS cloud** (option)                                                  | Voix plus stables que Web Speech API           |
| **Purge Lemon/Sotion résiduel** dans `site/config` / `build_assets`     | Config 100 % Stripe                            |


---

## 6. Rappels

- Ne plus utiliser pandoc / `site/export_manuel.py` / Lemon / Sotion / Netlify.
- Ne plus développer dans `Desktop\notion_to_word` ni `Desktop\flipcards-jp`.
- Après une session majeure : mettre à jour `docs/tracabilite/` (`NORME.md`).

