# Norme de traçabilité

Applicable à tout travail sur le monorepo **éditions-particulieres** à partir du **8 août 2026**.

---

## 1. Principe

Le répertoire `docs/tracabilite/` est la **mémoire officielle** du programme :

- ce qui a été fait,
- quand,
- comment (fichiers, commandes, décisions),
- ce qui a été jeté ou archivé.

Les conversations Cursor sont des **brouillons de travail**. Elles sont archivées hors repo après consolidation ; elles ne remplacent pas ce dossier.

---

## 2. Quand mettre à jour

Mettre à jour la traçabilité dès qu’une session :

- ajoute / retire un pipeline,
- change l’hébergement, l’auth, le paiement, le domaine,
- migre du code ou des données,
- corrige un bug structurel (pas un typo CSS isolé),
- nettoie des archives,
- change une convention d’export Notion.

Pour un micro-fix CSS : une ligne dans le journal de `HISTORIQUE.md` suffit, ou rien si déjà couvert par le message de commit.

---

## 3. Où écrire quoi

| Changement | Fichier |
|------------|---------|
| Récit chronologique, décision, incident | `HISTORIQUE.md` (section journal + corps si majeur) |
| Nouveau mode d’emploi / commande live | `ARCHITECTURE.md` |
| Nouvelle conversation à conserver | `CONVERSATIONS.md` |
| Suppression / déplacement d’archives | `NETTOYAGE.md` |
| Évolution de la règle elle-même | `NORME.md` + entrée journal |

---

## 4. Format d’une entrée historique

```markdown
### YYYY-MM-DD — Titre court

- **Contexte :** …
- **Fait :** …
- **Comment :** fichiers / commandes / commits `abcdef1`
- **Décision :** …
- **Conversations :** [titre](uuid)
```

---

## 5. Programme « comme neuf »

Le dépôt de code doit rester **exécutable et lisible** :

- pas de packages vides hérités d’une migration,
- pas de chemins Desktop hardcodés dans la config commitée,
- pas de double pipeline documenté comme « officiel » (legacy → `NETTOYAGE` / `HISTORIQUE` seulement),
- README racine = démarrage actuel uniquement,
- détail vivant = `docs/tracabilite/`.

Les sorties (`site/dist`, `output`, Drive) ne sont pas l’historique : ce sont des artefacts régénérables.

---

## 6. Archives hors monorepo

| Élément | Emplacement cible suggéré |
|---------|---------------------------|
| Conversations Cursor | `G:\Mon Drive\Editions Particulieres\_archives\conversations-cursor\` |
| Anciens dépôts Desktop | ZIP sur Drive puis suppression locale (après vérif monorepo) |
| Design proposals jetées | `_archives\design\` si besoin de relecture |

Ne jamais committer les transcripts bruts ni les `.env` des anciens projets.

---

## 7. Checklist fin de session majeure

- [ ] Entrée datée dans `HISTORIQUE.md`
- [ ] `ARCHITECTURE.md` à jour si commandes / chemins changés
- [ ] ID conversation ajouté dans `CONVERSATIONS.md`
- [ ] Suppressions listées dans `NETTOYAGE.md`
- [ ] README racine toujours aligné sur le chemin live
- [ ] Commit message git = le « pourquoi » ; la traçabilité = le « comment détaillé »
