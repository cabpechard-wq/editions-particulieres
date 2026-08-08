# Traçabilité — Éditions Particulières

**Norme du projet depuis le 8 août 2026.**  
Tout historique utile (extractions, site, décisions, migrations, nettoyages) vit ici. Les conversations Cursor du chantier sont archivées hors repo (voir `CONVERSATIONS.md`).

## Contenu de ce répertoire

| Fichier | Rôle |
|---------|------|
| [`HISTORIQUE.md`](HISTORIQUE.md) | Chronologie détaillée : quoi, quand, comment (extraction → site → monorepo) |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | État actuel du programme (chemins live, pipelines, hébergement) |
| [`CONVERSATIONS.md`](CONVERSATIONS.md) | Index des conversations Cursor à archiver |
| [`NETTOYAGE.md`](NETTOYAGE.md) | Archives purgées / à archiver hors machine de travail |
| [`NORME.md`](NORME.md) | Règles pour tenir à jour cette traçabilité |

## Point d’entrée produit

- Code : monorepo `editions-particulieres` (`C:\Users\anton\Projects\editions-particulieres`)
- Site live : `https://www.editions-particulieres.fr`
- Sorties binaires : `G:\Mon Drive\Editions Particulieres\`
- Anciens dépôts (archives Desktop, ne plus modifier) : `notion_to_word`, `flipcards-jp`

## Comment mettre à jour

Après toute session significative : ajouter une entrée datée dans `HISTORIQUE.md`, lister les conversations dans `CONVERSATIONS.md`, noter les suppressions dans `NETTOYAGE.md`. Détail : `NORME.md`.
