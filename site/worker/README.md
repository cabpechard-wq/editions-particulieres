# Flipcards Auth Worker

## Setup (une fois)

```bash
cd site/worker
npm i -g wrangler
wrangler login
wrangler kv namespace create USERS
wrangler kv namespace create USERS --preview
```

Mettre les `id` / `preview_id` dans `wrangler.toml`.

```bash
wrangler secret put STRIPE_SECRET_KEY
wrangler secret put RESEND_API_KEY
wrangler secret put AUTH_SECRET
```

`AUTH_SECRET` = longue chaîne aléatoire (ex. `openssl rand -hex 32`).

Optionnel : éditer `RESEND_FROM` et `SITE_BASE` dans `wrangler.toml`.

```bash
wrangler deploy
```

Copier l’URL `https://flipcards-auth.<compte>.workers.dev` dans
`site/config.json` → `auth.api_url`, puis :

```bash
python site/build_assets.py
# deploy host-repo (auth.js, merci, membre, flipcards)
```

## Migrer un compte existant (abonnes.json)

```bash
curl -X POST https://flipcards-auth.XXX.workers.dev/api/admin-migrate \
  -H "Content-Type: application/json" \
  -d "{\"admin_secret\":\"$AUTH_SECRET\",\"email\":\"antonin.pechard@gmail.com\",\"password\":\"test1234\",\"status\":\"actif\"}"
```

## Stripe Payment Links

After payment redirect URL **exacte** :

```
https://cabpechard-wq.github.io/editions-particulieres/merci/?session_id={CHECKOUT_SESSION_ID}
```

(Le `{CHECKOUT_SESSION_ID}` est remplacé par Stripe.)
