# Migre un compte abonnes.json → Worker KV (admin-migrate).
# Usage :
#   .\scripts\migrate_account_to_kv.ps1
#   .\scripts\migrate_account_to_kv.ps1 -Email you@example.com -Password secret

param(
    [string]$Email = "antonin.pechard@gmail.com",
    [string]$Password = "",
    [string]$Api = "https://flipcards-auth.cab-pechard.workers.dev"
)

$ErrorActionPreference = "Stop"

if (-not $Password) {
    $secure = Read-Host "Mot de passe du compte (abonnes.json)" -AsSecureString
    $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    )
}

$secretSecure = Read-Host "AUTH_SECRET du Worker (valeur secrète, PAS le mot 'AUTH_SECRET')" -AsSecureString
$AdminSecret = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretSecure)
)

if (-not $AdminSecret -or $AdminSecret -eq "AUTH_SECRET" -or $AdminSecret -eq "VOTRE_AUTH_SECRET") {
    Write-Error "Vous devez saisir la vraie valeur du secret Cloudflare, pas le nom de la variable."
}

$body = @{
    admin_secret = $AdminSecret
    email        = $Email.Trim().ToLower()
    password     = $Password
    status       = "actif"
} | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri "$Api/api/admin-migrate" -Method POST -ContentType "application/json" -Body $body
    Write-Host "OK : $($resp | ConvertTo-Json -Compress)"
    Write-Host "Connexion : https://cabpechard-wq.github.io/editions-particulieres/membre/"
} catch {
    $detail = $_.ErrorDetails.Message
    if ($detail) { Write-Error $detail } else { throw }
}
