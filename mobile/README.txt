# Éditions Particulières — app mobile (Expo)

Flipcards jurisprudence (JSON local). Parcours : Accueil (Thèmes/Notions) → Étudier.

## Prérequis

Node.js 20+.

## Setup

```powershell
cd mobile
npm install
npm run sync-data
npm start
```

Ou : `.\Lancer.ps1`

`sync-data` copie le JSON flipcards le plus récent depuis :
- `$env:EP_OUTPUT_ROOT/flipcards/output`
- `G:/Mon Drive/Editions Particulieres/flipcards/output`
- `output/` à la racine du monorepo

Générer un JSON : `python -m flipcards --offline --format json`
