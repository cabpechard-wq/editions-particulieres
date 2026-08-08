# Historique détaillé — Éditions Particulières

Document de traçabilité unique. Période couverte : **~1er août 2026 → 8 août 2026** (consolidation), avec antécédents collecteurs / Notion.

Sources : commits git du monorepo, dépôts Desktop `notion_to_word` et `flipcards-jp`, conversations Cursor indexées dans `CONVERSATIONS.md`, README / commandes des anciens projets, structure actuelle du code.

---

## 0. Contexte métier

**Éditions Particulières** (enseigne / éditeur) publie un parcours pédagogique de **droit public et administratif** :

| Produit | Contenu |
|---------|---------|
| **Cours** (ex. Manuel) | Base Notion « manuel » → chapitres HTML `/manuel/` |
| **Dictionnaire** | Base Index / glossaire → `/dictionnaire/` |
| **Arrêts** | Base Jurisprudence (~975 fiches) → fiches HTML `/arrets/` + flipcards |
| **Flipcards** | Recto/verso Nom/Verso (+ Faits, Enjeu, Solution, Perspective) → démo publique + pack membres |
| **Word / PDF** | Exports impression / révision (GUI Tkinter) |
| **App mobile** | Expo, étude offline des flipcards |

Sources de vérité éditoriales : bases Notion.  
Sorties binaires : Google Drive `G:\Mon Drive\Editions Particulieres\`.  
Code : monorepo GitHub `cabpechard-wq/editions-particulieres`.

---

## 1. Antécédents (avant le chantier d’août 2026)

### 1.1 Collecteurs et scripts isolés

Sur le Bureau / projets Cursor antérieurs :

- `nonoff-collecteur`, `off-collecteur`, `rgdd-collecteur` — collectes / protocoles (dont RGDD), modèles de `commandes.txt` repris ensuite dans `notion_to_word`.
- `notion_md_to_revision_docx_v18.py` (Desktop) — conversion Markdown Notion → Word de révision (précurseur logique du pipeline Word).
- `chantier-jurisprudence-mode-cursor.md` + `Install-ChantierJurisprudence.ps1` — protocole agent pour enrichir la base Jurisprudence via MCP Notion (lots de fiches, nomenclature éditoriale).

Ces outils ne font **pas** partie du monorepo ; ils ont alimenté la base Notion et les conventions de commandes.

### 1.2 Objectif initial d’extraction

Besoin exprimé (~1er août) : transformer des pages Notion (méthodologie, fiches, cours…) en **fichiers Word exploitables pour impression / révision**, plutôt que Markdown seul ou PDF brut.

Choix retenus progressivement :

1. Connexion API Notion (token + IDs de bases).
2. Génération `.docx` via python-docx + modèle `.dotx`.
3. PDF via **Microsoft Word COM** (pywin32), pas un moteur PDF indépendant.
4. GUI Windows (Tkinter) pour les non-CLI.

---

## 2. Phase extraction — dépôt `notion_to_word` (≈ 1–7 août 2026)

**Emplacement historique :** `C:\Users\anton\Desktop\notion_to_word`  
**GitHub (privé) :** `https://github.com/cabpechard-wq/notion_to_word` (poussé ~7 août — conversation « GitHub program transfer »)  
**Commit d’archive locale :** `bafe2af` — *Initial commit: Notion → Word/HTML export tool with GUI* (2026-08-07)

### 2.1 Architecture par registres

Chaque registre Notion avait le même schéma de package :

```
manuel/ | fiches/ | methodo/ | formule/ | index/ | arrets/
  converter.py, cli.py, __main__.py, templates…
shared/   # pipeline, liens, styles, postlink, writers
gui/      # interface Tkinter
```

| Registre | Rôle | Particularités |
|----------|------|----------------|
| `manuel` | Cours | Blocs Notion live → Paragraph/Table ; numérotation titres ; colonnes aplaties verticalement |
| `fiches` | Fiches thématiques | Même famille « corps Notion » |
| `methodo` | Méthodologie | Idem |
| `formule` | Formules | Idem |
| `index` | Glossaire | Convertisseur dédié |
| `arrets` | Jurisprudence | Matrice propriétés + corps ; formats A4/A5 ; fit 1 page via Word COM |

Facades CLI : `python -m export <registre>`, `python -m <registre>`, `python export_<registre>.py`, `Export-Notion.ps1`.

### 2.2 Chronologie fonctionnelle (extraction)

| Date (approx.) | Quoi | Comment |
|----------------|------|---------|
| **2026-08-01** | Naissance GUI + styles Word | Modèle `Notion_Revision.dotx` / styles Éditions ; `commandes.txt` ; venv + `.env` (`NOTION_TOKEN`) |
| **2026-08-01** | Lien styles `.dotx` | Copie des styles au moment de la génération (fichier autonome ensuite) |
| **2026-08-01–02** | Jurisprudence : mapping propriétés | Juridiction, Date, Référence, Formation, Titre, Nom, liens officiels ; parse Légifrance / CE / Cass. / Cons. constit. |
| **2026-08-02** | Matrice CSV + refresh Notion | Auto-refresh avant export ; 975 pages ; filtre « Word » corrigé ; `--limit` / `--page` sans recharger toute la base |
| **2026-08-02** | Fit 1 page A5 puis A4 | `word_fit` via COM Word : mesure → réduction 0,5 pt jusqu’à 1 page ; export séquentiel (pas de multi-thread Word) |
| **2026-08-02** | Incident processus Word | Une instance Word par fiche → runaway (~37 process) ; correction : **réutiliser une seule session Word** |
| **2026-08-02–03** | Corrections rendu Word (plusieurs sessions) | Focus rendu (titres, callouts, colonnes, encadrés) **sans** toucher la logique d’extraction du contenu |
| **2026-08-03** | Portabilité Google Drive | Chemins de sortie externalisables ; contrainte Windows+Word documentée |
| **2026-08-03–04** | Audit / passe générale | Architecture 4–6 registres + pipeline + manifeste ; canvas d’audit |
| **2026-08-05–06** | Enrichissement éditorial Jurisprudence | Agents MCP Notion (lots 16→160) : Importance #2, Thème #2, Notions #2 ; nomenclature éditoriale ; incident Esdras (champs #2 réécrits par erreur) |
| **2026-08-06** | Extension HTML | Sorties `.html` examinées ; pont vers `flipcards-jp/commerce` (gabarits site) |
| **2026-08-06** | `flipcards_site_export` | Dossier dans notion_to_word pour chaîner Notion → docx → pandoc → gabarits site (chemin **legacy** ensuite remplacé) |
| **2026-08-07** | Dépôt GitHub + README | Projet portable ; token jamais versionné |

### 2.3 Décisions techniques figées (extraction Word)

- Colonnes Notion (`column_list`) → **flux vertical** gauche→droite (pas de table côte à côte en défaut final).
- Callouts / toggles → Corps + contenu.
- « Encadré Fiche » = jurisprudence uniquement.
- Noms de fichiers : `AAAAMMJJhhmmss - Nom.docx`.
- `NOTION_SSL_VERIFY=0` recommandé sous Windows/AV.
- Manifeste cross-liens : `output/manifest.json`.

### 2.4 Ce qui a été migré vers le monorepo

Tout le code utile → `extract/` (surtout `extract/word/`, `extract/html/`, `extract/pull/`) + `gui/` + `packages/ep_core/`.  
Les packages vides `extract/manuel|fiches|…` dans le monorepo étaient des **coquilles de migration** (0 octet) — purgées le 8 août 2026 (voir `NETTOYAGE.md`).

---

## 3. Phase flipcards + commerce — dépôt `flipcards-jp` (≈ 3–7 août 2026)

**Emplacement historique :** `C:\Users\anton\Desktop\flipcards-jp`  
**Commit d’archive :** `f686a27` — *Initial flipcards project with GAJA 2026* (2026-08-04)  
Note : marque produit = **GADA** (Grands Arrêts du Droit public et Administratif), jamais « GAJA ».

### 3.1 Flipcards

| Date | Quoi | Comment |
|------|------|---------|
| **2026-08-03** | Extraction flipcards depuis Notion | `python -m flipcards` ; **975 pages** ; matrice `flipcards_matrice.csv` + `.json` ; HTML Quizlet-like |
| **2026-08-03–04** | Projet autonome | Séparé de notion_to_word ; CLI `export_flipcards.py` / `python -m flipcards` / `--offline` |
| **2026-08-04** | App mobile Expo | Thèmes / Notions → Étudier ; sync JSON ; autoplay ; chips Notion |
| **2026-08-04** | Build HTML lourd | Ex. `GADA-2026.html` (~2 Mo) dans le dossier projet |

Propriétés clés matrice : Nom (recto), Verso, Thème, Notions, Importance, + champs fiche (Faits, Enjeu, Solution, Perspective) lus depuis Notion.

### 3.2 Site commerce (sous-dossier `commerce/`)

Évolution hébergement / monétisation :

| Étape | Solution | Statut final |
|-------|----------|--------------|
| 1 | Site Notion `droit-public.notion.site` | Vitrine / parcours temporaire |
| 2 | Lemon Squeezy | Exploré puis abandonné |
| 3 | Sotion (paywall Notion Sites) | Exploré puis abandonné |
| 4 | Netlify / surge (scripts) | Exploré puis abandonné |
| 5 | **GitHub Pages** (`flipcards-host`) | Retenu |
| 6 | **Stripe Payment Links** + **Cloudflare Worker** (KV + Resend) | Retenu |
| 7 | Domaine **OVH** `www.editions-particulieres.fr` | Retenu (8 août) |

Routes historiques (`flipcards-host`) :

| Route | Rôle |
|-------|------|
| `/` | Accueil collection |
| `/demo/` | 8 cartes publiques |
| `/checkout/` | Abonnements |
| `/merci/` | Claim Stripe + choix mot de passe |
| `/membre/` | Login / forgot / reset / compte |
| `/flipcards/` | App membres (Bearer + `/api/me`) — ex. `/gada/` renommé avec redirection |
| `/ressources/`, `/exercices/` | Pages éditoriales |

Auth Worker : nom `flipcards-auth` ; secrets Stripe / Resend / AUTH_SECRET ; KV `USERS`.

### 3.3 Export manuel site (chemin legacy)

Chaîne initiale documentée dans `commerce/README` / `site/export_manuel.py` :

```
Notion → notion_to_word (.docx) → pandoc (docx→html) → gabarits manuel-*.html → dist/site/manuel/
```

Arborescence URL = référencement **DP-XXX** (chaque chiffre = un niveau).  
Fiches actualité `DP-XXX/n` → `/manuel/_aside/`.

Ce chemin a été **remplacé** dans le monorepo par une conversion HTML directe Notion → gabarits (`extract/html/`), sans pandoc ni appel externe à notion_to_word.

---

## 4. Phase monorepo — `editions-particulieres` (7–8 août 2026)

**Emplacement :** `C:\Users\anton\Projects\editions-particulieres`  
**Branche :** `main` → `origin/main`

### 4.1 Fusion des dépôts

| Ancien | Nouveau dans le monorepo |
|--------|--------------------------|
| `notion_to_word` | `extract/` + `gui/` |
| `flipcards-jp/flipcards` | `flipcards/` |
| `flipcards-jp/commerce` | `site/` (d’abord `site/commerce/`, puis aplati) |
| `flipcards-jp/mobile` | `mobile/` |
| Chemins locaux | `packages/ep_core` + `config/` + `.env` → Drive |

Sorties Drive standardisées :

```
G:/Mon Drive/Editions Particulieres/
  export/          # Word, PDF, HTML par registre
  matrices/        # jurisprudence + flipcards
  flipcards/output/
  site-build/
```

### 4.2 Chronologie commits monorepo (git)

| Commit | Date | Contenu |
|--------|------|---------|
| `a9f5046` | 2026-08-07 | Import monorepo + déploiement Pages sous `/editions-particulieres` |
| `8d6e53c` | 2026-08-07 | Aplatir `site/commerce` → `site/` |
| `709a6d2`…`eed7146` | 2026-08-07 | Uploads / config (`wrangler.toml`, `config.json`, `.env`) |
| `6a62018` | 2026-08-07 | Build site monorepo + GitHub Actions → `dist/site` |
| `475d30e` | 2026-08-07 | Export HTML manuel + glossaire pour Pages |
| `0f92d08` | 2026-08-07 | Fix `auth.js` écrasé par export manuel (Failed to fetch) |
| `425ff67` | 2026-08-07 | Moins d’appels API Notion sur mentions introuvables |
| `70ac050` | 2026-08-08 | Styles manuel : quotes bordure, encadrés, underline export |
| `9dd0b7c` | 2026-08-08 | Stripe Payment Links dans le build CI checkout |
| `431694b` | 2026-08-08 | Seed manuel/dictionnaire depuis Pages live (évite rate-limit Notion) |
| `68c7ad3` | 2026-08-08 | Export HTML jurisprudence |
| `ee3a5af` | 2026-08-08 | Publier section Arrêts (liens home + CI) |
| `077adbf` | 2026-08-08 | Style arrêts colonne A4 ; retrait titre « Considérant de principe » |
| `97df873` | 2026-08-08 | Accueil : déconnexion, libellé Cours, lien BU |
| `5932b60` | 2026-08-08 | Flipcards : 4 propriétés Notion pour fiches de décision |
| `b121ed9` | 2026-08-08 | Manuel : liens glossaire discrets |
| `9a8ec3d` | 2026-08-08 | Flipcards : bulle fiche en ligne, scrollbar |
| `85d65f6`…`9760369` | 2026-08-08 | Typo manuel / arrêts, colonnes de lecture |
| `88bf769` | 2026-08-08 | Auth : repli Worker dans `auth.js` ; migration KV |
| `05c1464` | 2026-08-08 | CI : retirer segment « Éditions Particulières » des fils d’Ariane |
| `7a6c9ed`…`d8f8d03` | 2026-08-08 | Largeurs lecture 44,5 / 46 rem |
| `8ae2f5c` | 2026-08-08 | Pied de page aligné bords |
| `cee0983` | 2026-08-08 | Cours : renommer manuel côté site ; titres encadrés |
| `0b541f6` | 2026-08-08 | Domaine OVH `www.editions-particulieres.fr` + CNAME au build |
| `a60471c` | 2026-08-08 | Accueil : offre lancement, BU/Amphi, ordre rubriques |
| `625a353` | 2026-08-08 | Theme switcher live (Campus défaut) |
| `0168f18` | 2026-08-08 | TTS lecture à voix haute ; app mobile ; nettoyage dépôt |
| `f45cf37`…`64253ad` | 2026-08-08 | Chartes Amphithéâtre (lys, médias), CORS domaine, seed CI |
| `16d621e` | 2026-08-08 | Footer collé bas de page |
| `ffe814b` | 2026-08-08 | CI : rejeter seed manuel incomplet ; forcer export Notion |
| `4c3d748` | 2026-08-08 | Relier Cours / Dictionnaire / Arrêts |
| `86d8cde` | 2026-08-08 | Relations, navigation, UX pédagogique |

### 4.3 Décisions d’architecture monorepo

1. **Drive = source of truth des binaires** ; git = code + templates.
2. **HTML site** = `extract/html` + `export_html.py` / `export_dictionnaire.py` / `export_arrets.py` (plus pandoc).
3. **CI** seed manuel/dictionnaire depuis le site live sauf `workflow_dispatch.refresh_notion=true` ; arrêts toujours exportés.
4. **Auth** = Cloudflare Worker + Stripe (pas Lemon/Sotion).
5. **Domaine canonique** = `https://www.editions-particulieres.fr` (apex + github.io redirigent vers www).
6. **Charte** : plusieurs thèmes CSS (`site/templates/themes/`) ; défaut Campus ; Amphithéâtre (papier lys) affiné.
7. **TTS** : `site-tts.js` (Web Speech API fr-FR) injecté sur pages exportées.
8. **Relations cross-pages** : Cours ↔ Dictionnaire ↔ Arrêts via `site_links` / propriétés Notion.

### 4.4 Sessions Cursor monorepo (thèmes)

| Thème | IDs (voir CONVERSATIONS.md) | Apports |
|-------|----------------------------|---------|
| Project connection (×3+) | `dc5adce0`, `a5be22f4`, `1c30aa3f`, `1e459baa`, `d998d927` | Migration code, Word GUI, HTML direct, auth, TTS, domaine |
| Structure / marketing | `652a370e`, `b5236bf7`, `90a0dd57` | Cartographie site, pages Ressources/Exercices, audit accueil |
| Stripe | `de23d752` | Payment Links mensuel / semestriel |
| Chartes | `761930c0` | Propositions + switcher thèmes |
| Audit patches | `eb79d3f1` | CORS www, seed incomplet, relations, fond Campus |

---

## 5. État au 8 août 2026 (après consolidation)

### Pipelines live

```
Notion DBs
  ├─ GUI / extract.word ──► Drive export/*.docx (+ PDF COM)
  ├─ extract.pull ────────► Drive JSON (manuel, jurisprudence, index)
  ├─ extract.html ────────► /manuel /dictionnaire /arrets  (+ cross-links)
  └─ flipcards ───────────► matrice → HTML/JSON → site demo/members + mobile
                              site/build_assets → GitHub Pages (www)
                              Worker auth + Stripe → /flipcards/
```

### Ce qui n’est plus le chemin nominal

- Pandoc + `site/export_manuel.py`
- Lemon Squeezy / Sotion / Netlify
- Hébergement seul sous `…/flipcards-host/`
- Packages vides `extract/{manuel,fiches,…}` hérités de la migration
- Modification active de `Desktop/notion_to_word` ou `Desktop/flipcards-jp`

### Dettes / points de vigilance connus

- Seed CI peut empoisonner si DNS renvoie une page OVH « en construction » (garde-fous ajoutés).
- Comptes membres : migration `abonnes.json` → KV à vérifier après chaque déplacement de projet.
- Anciens dépôts Desktop (~5,4 Go) à archiver hors machine de travail (voir `NETTOYAGE.md`).
- Assemblage local : `.\scripts\build_site.ps1` (l’ancien `build_all.ps1` a été supprimé).

---

## 6. Journal des mises à jour de ce document

| Date | Auteur / session | Changement |
|------|------------------|------------|
| 2026-08-08 | Session « Project documentation and archiving » | Création initiale du répertoire `docs/tracabilite/` ; synthèse extraction + site + monorepo ; index conversations ; premier nettoyage monorepo |
