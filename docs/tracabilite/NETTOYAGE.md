# Journal de nettoyage / archives

## 2026-08-08 — Premier grand ménage monorepo

### Objectif

Rendre le programme **propre comme neuf** après fusion `notion_to_word` + `flipcards-jp`, tout en conservant l’historique dans `docs/tracabilite/`.

### Supprimé dans le monorepo (cette session)

#### Packages vides hérités de la migration (0 octet)

Logique déplacée vers `extract/word`, `extract/html`, `extract/pull` — plus aucun import.

- `extract/manuel/`
- `extract/fiches/`
- `extract/formule/`
- `extract/methodo/`
- `extract/index/`
- `extract/arrets/` (y compris `fiche_fields.json` = `{}` et `matrices/.gitkeep` obsolète)
- `extract/export/`
- `extract/shared/` (y compris stub `site_export.py` / `writers/html_writer.py`)

#### Chemins commerce abandonnés (documentés dans HISTORIQUE)

- `site/export_manuel.py` — chaîne pandoc + notion_to_word
- `site/setup_lemonsqueezy.py` + `site/lemonsqueezy_setup.txt`
- `site/setup_sotion.py` + `site/sotion_setup.txt`
- `site/deploy_netlify.py`
- `scripts/flipcards-host-redirect/`
- `scripts/build_all.ps1` (squelette non branché ; `build_site.ps1` suffit)

#### Config racine obsolète

- `config.json` à la racine (doublon / URLs `flipcards-host` / `pipeline_dir` → Desktop) — remplacé par `site/config.json` + `config/*.json`

### Conservé volontairement

| Élément | Raison |
|---------|--------|
| `site/templates/design-proposals/` | Sandbox chartes (~3 Mo) ; utile pour relecture visuelle locale (`serve_theme_proposals.ps1`) — peut être archivé plus tard sur Drive |
| `site/dist/`, `output/`, `site/host-repo/*` | Artefacts de build (déjà gitignored) |
| `site/stripe_post_payment.txt`, legal | Encore valides (Stripe) |
| `site/test_commerce.py` | Mis à jour pour ne plus exiger Lemon/Netlify |

### Hors monorepo — à archiver par l’utilisateur (ne pas supprimer à l’aveugle)

| Chemin | Taille approx. | Action recommandée |
|--------|----------------|--------------------|
| `C:\Users\anton\Desktop\notion_to_word` | ~4 Go | ZIP vers Drive `_archives\repos\notion_to_word-2026-08.zip` puis supprimer Desktop (code déjà dans monorepo ; outputs régénérables) |
| `C:\Users\anton\Desktop\flipcards-jp` | ~1,4 Go | Idem `_archives\repos\flipcards-jp-2026-08.zip` |
| `C:\Users\anton\Desktop\chantier-jurisprudence-mode-cursor.md` | petit | Copier dans `_archives\editorial\` |
| Transcripts Cursor (voir CONVERSATIONS.md) | variable | Copier vers `_archives\conversations-cursor\2026-08\` |

**Ne pas supprimer** tant que le ZIP Drive n’est pas vérifié (ouvrir le monorepo, lancer GUI + un export HTML test).

### Vérifications post-nettoyage

```powershell
python -c "import extract.html, extract.word, flipcards, gui; print('ok')"
# optionnel : python -m gui  /  python export_html.py --help
```

---

## Modèle pour les prochains nettoyages

```markdown
### YYYY-MM-DD — Titre

- Supprimé : …
- Conservé : …
- Archivé vers : …
- Raison : …
```
