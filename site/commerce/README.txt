Flipcards — commercialisation (abo étudiants)
==============================================

Stack
-----
- Stripe     : Payment Links (redirect avec session_id)
- Auth       : Cloudflare Worker + KV + Resend (commerce/worker/)
- Front      : https://cabpechard-wq.github.io/editions-particulieres/
               /          accueil
               /checkout/ abonnements
               /merci/    claim Stripe + choix mdp (min 4)
               /membre/   login, forgot, reset, compte
               /flipcards/ flipcards (token Bearer + /api/me)
- abonnes.json : legacy / migration vers KV (migrate_abonnes_to_kv.py)

Parcours
--------
1) /checkout/ → Stripe
2) Redirect : /merci/?session_id={CHECKOUT_SESSION_ID}
3) Choisir un mot de passe → token → /flipcards/app.html
4) Reconnexion : /membre/ (email + mdp)
5) Oubli : /membre/forgot/ → e-mail Resend → /membre/reset/
6) Modifier : /membre/compte/ (connecté)

Setup auth (obligatoire)
------------------------
Voir commerce/worker/README.md
Puis auth.api_url dans config.json + build_assets + deploy host.

Stripe After payment
--------------------
https://cabpechard-wq.github.io/editions-particulieres/merci/?session_id={CHECKOUT_SESSION_ID}
Details : commerce/stripe_post_payment.txt

Scripts
-------
python commerce/build_assets.py
python commerce/export_manuel.py   # Notion -> docx (notion_to_word) -> HTML -> /manuel/ (APRES build_assets.py)
python commerce/migrate_abonnes_to_kv.py
python commerce/test_e2e_access.py
python commerce/verify_flow.py   # après deploy + api_url réel

Manuel (/manuel/)
-----------------
Source : page/base Notion (voir config.json -> manuel.notion_database_url).
Chaîne : notion_to_word (.venv, --format docx) -> pandoc (docx -> html) -> gabarits
templates/manuel-sommaire.html + templates/manuel-page.html -> dist/site/manuel/.
Arborescence URL = référencement DP-XXX (chaque chiffre = un niveau), ex. /manuel/dp-000/dp-300/dp-310/dp-311/.
Fiches DP-XXX/X (actualité) : mises de côté dans /manuel/_aside/ (hors sommaire / menu).
Options : --reuse (sans rappeler Notion), --limit N.
Relancer python commerce/export_manuel.py chaque fois que le Manuel change dans Notion
(build_assets.py recrée dist/site en entier, donc TOUJOURS après lui).
Prérequis : pandoc sur le PATH, notion_to_word cloné avec .venv + NOTION_TOKEN (.env).

Securite /merci/
----------------
Sans session_id Stripe payé → pas d’accès (plus d’unlock gratuit).
