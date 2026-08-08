Éditions Particulières — site (commerce + contenu)
====================================================

Stack
-----
- Stripe     : Payment Links (redirect avec session_id)
- Auth       : Cloudflare Worker + KV + Resend (site/worker/)
- Front      : https://www.editions-particulieres.fr
               /              accueil
               /checkout/     abonnements
               /merci/        claim Stripe + choix mdp
               /membre/       login, forgot, reset, compte
               /manuel/       Cours
               /dictionnaire/ glossaire
               /arrets/       fiches jurisprudence
               /flipcards/    app membres (Bearer + /api/me)
               /demo/         8 cartes publiques

Parcours abonné
---------------
1) /checkout/ → Stripe
2) Redirect : /merci/?session_id={CHECKOUT_SESSION_ID}
3) Mot de passe → token → /flipcards/app.html
4) Reconnexion : /membre/
Détails Stripe : site/stripe_post_payment.txt
Auth Worker : site/worker/README.md

Build local
-----------
python site/build_assets.py
python export_html.py              # Cours → dist (via extract.html)
python export_dictionnaire.py
python export_arrets.py
.\scripts\build_site.ps1           # assemblage complet
# ou laisser la CI GitHub Actions déployer depuis main

Contenu pédagogique
-------------------
Source : bases Notion (config/notion.json).
Chaîne live : Notion API → extract/html → gabarits site/templates → dist/site/
Arborescence Cours = DP-XXX ; actualités → /manuel/_aside/
Ne plus utiliser l’ancienne chaîne pandoc / site/export_manuel.py (supprimée).

Traçabilité
-----------
docs/tracabilite/ — historique, architecture, norme, nettoyage.
