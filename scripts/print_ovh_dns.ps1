# Enregistrements DNS OVH pour GitHub Pages — editions-particulieres.fr
# Zone DNS : Manager OVH → Noms de domaine → editions-particulieres.fr → Zone DNS

Write-Host @"

=== DNS OVH (editions-particulieres.fr) ===

1) Sous-domaine WWW
   Type  : CNAME
   Sous-domaine : www
   Cible : cabpechard-wq.github.io.
   TTL   : 3600 (ou par défaut)

2) Racine @ (editions-particulieres.fr sans www)
   Supprimer l'enregistrement A actuel vers 213.186.33.5 (parking OVH)
   Ajouter 4 enregistrements A vers GitHub Pages :
   Type A → 185.199.108.153
   Type A → 185.199.109.153
   Type A → 185.199.110.153
   Type A → 185.199.111.153

3) GitHub (déjà fait)
   Pages → Custom domain : www.editions-particulieres.fr
   Fichier CNAME généré au build.

4) Après propagation DNS (quelques minutes à 24 h)
   - Vérifier : https://www.editions-particulieres.fr/
   - GitHub → Pages → cocher « Enforce HTTPS »
   - Stripe Payment Links → redirect :
     https://www.editions-particulieres.fr/merci/?session_id={CHECKOUT_SESSION_ID}
   - Worker auth : wrangler deploy (SITE_BASE mis à jour)

Propagation : nslookup www.editions-particulieres.fr
  doit répondre cabpechard-wq.github.io ou les IP GitHub.

"@
