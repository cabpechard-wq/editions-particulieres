/**
 * Flipcards auth API — Cloudflare Worker
 * Endpoints: /api/claim /api/set-password /api/login /api/change-password
 *            /api/forgot /api/reset /api/me /api/admin-migrate
 */

const MIN_PASSWORD = 4;
const SESSION_TTL_SEC = 60 * 60 * 24 * 30; // 30 days
const CLAIM_TTL_SEC = 60 * 30; // 30 min
const RESET_TTL_SEC = 60 * 60; // 1 h
// Workers free : budget CPU très bas — 100k itérations = timeout → "Erreur serveur"
const PBKDF2_ITERS = 8000;
const CGV_VERSION = "2026-08-05";
const CGV_FIELD_KEY = "cgv_accept";

/**
 * Lit l'acceptation CGV sur la session Stripe Checkout.
 * - accepted true/false si un champ / consent est présent
 * - required false pour les anciennes sessions sans case (rétrocompat)
 */
function readCgvAcceptance(session) {
  const fields = Array.isArray(session.custom_fields) ? session.custom_fields : [];
  const field = fields.find(
    (f) => f && (f.key === CGV_FIELD_KEY || f.key === "accept_cgv")
  );
  if (field) {
    const ok =
      field.type === "checkbox" &&
      field.checkbox &&
      field.checkbox.value === true;
    return { accepted: ok, required: true, source: "stripe_custom_field" };
  }
  if (session.consent && session.consent.terms_of_service === "accepted") {
    return { accepted: true, required: true, source: "stripe_tos_consent" };
  }
  if (session.consent && session.consent.terms_of_service === "declined") {
    return { accepted: false, required: true, source: "stripe_tos_consent" };
  }
  // Paiements antérieurs à l'ajout de la case
  return { accepted: null, required: false, source: null };
}

export default {
  async fetch(request, env, ctx) {
    try {
      return await handle(request, env, ctx);
    } catch (err) {
      console.error(err);
      const msg = (err && err.message) || "Erreur serveur";
      // Message utile côté client pendant la mise au point
      return json({ error: msg }, 500, request, env);
    }
  },
};

async function handle(request, env, ctx) {
  const url = new URL(request.url);
  if (request.method === "OPTIONS") {
    return cors(new Response(null, { status: 204 }), request, env);
  }

  const path = url.pathname.replace(/\/+$/, "") || "/";
  if (request.method === "GET" && (path === "/" || path === "/api")) {
    return json({ ok: true, service: "flipcards-auth" }, 200, request, env);
  }

  if (path === "/api/me" && request.method === "GET") {
    return cors(await me(request, env), request, env);
  }
  if (path === "/api/claim" && request.method === "POST") {
    return cors(await claim(request, env), request, env);
  }
  if (path === "/api/set-password" && request.method === "POST") {
    return cors(await setPassword(request, env), request, env);
  }
  if (path === "/api/login" && request.method === "POST") {
    return cors(await login(request, env), request, env);
  }
  if (path === "/api/change-password" && request.method === "POST") {
    return cors(await changePassword(request, env), request, env);
  }
  if (path === "/api/forgot" && request.method === "POST") {
    return cors(await forgot(request, env, ctx), request, env);
  }
  if (path === "/api/reset" && request.method === "POST") {
    return cors(await resetPassword(request, env), request, env);
  }
  if (path === "/api/admin-migrate" && request.method === "POST") {
    return cors(await adminMigrate(request, env), request, env);
  }

  return json({ error: "Not found" }, 404, request, env);
}

/* ---------- handlers ---------- */

async function claim(request, env) {
  const body = await readJson(request);
  const sessionId = String(body.session_id || "").trim();
  if (!sessionId.startsWith("cs_")) {
    return json({ error: "session_id Stripe manquant ou invalide" }, 400);
  }
  if (!env.STRIPE_SECRET_KEY) {
    return json({ error: "STRIPE_SECRET_KEY non configuré" }, 503);
  }

  const session = await stripeGet(env, `/checkout/sessions/${encodeURIComponent(sessionId)}`);
  if (!session || session.error) {
    return json({ error: "Session Stripe introuvable" }, 400);
  }

  const paid =
    session.payment_status === "paid" ||
    session.status === "complete" ||
    session.payment_status === "no_payment_required";
  if (!paid) {
    return json({ error: "Paiement non confirmé" }, 402);
  }

  const email = (
    session.customer_details?.email ||
    session.customer_email ||
    ""
  )
    .trim()
    .toLowerCase();
  if (!email || !email.includes("@")) {
    return json({ error: "E-mail Stripe introuvable sur la session" }, 400);
  }

  const cgv = readCgvAcceptance(session);
  if (cgv.required && !cgv.accepted) {
    return json(
      {
        error:
          "Acceptation des CGV / mentions légales manquante sur le paiement Stripe",
      },
      400
    );
  }

  const existing = await getUser(env, email);
  const needsPassword = !existing || !existing.hash;
  const claimToken = await signToken(
    env,
    { typ: "claim", email, sid: sessionId },
    CLAIM_TTL_SEC
  );

  const now = new Date().toISOString();
  const cgvRecord = {
    accepted: cgv.accepted === true,
    acceptedAt: cgv.accepted ? now : null,
    version: CGV_VERSION,
    source: cgv.source || null,
    stripeSessionId: sessionId,
  };

  if (!existing) {
    await putUser(env, email, {
      hash: null,
      salt: null,
      status: "actif",
      stripeCustomerId: session.customer || null,
      stripeSessionId: sessionId,
      createdAt: now,
      cgv: cgvRecord,
    });
  } else {
    existing.stripeSessionId = sessionId;
    if (session.customer) existing.stripeCustomerId = session.customer;
    // Ne pas écraser une acceptation déjà enregistrée par un false
    if (cgv.accepted === true || !existing.cgv?.accepted) {
      existing.cgv = cgvRecord;
    }
    await putUser(env, email, existing);
  }

  return json({
    email,
    needs_password: needsPassword,
    claim_token: claimToken,
    has_account: Boolean(existing && existing.hash),
    cgv_accepted: cgv.accepted === true,
  });
}

async function setPassword(request, env) {
  const body = await readJson(request);
  const claimToken = String(body.claim_token || "").trim();
  const password = String(body.password || "");
  if (password.length < MIN_PASSWORD) {
    return json({ error: `Mot de passe : ${MIN_PASSWORD} caractères minimum` }, 400);
  }
  const payload = await verifyToken(env, claimToken);
  if (!payload || payload.typ !== "claim" || !payload.email) {
    return json({ error: "Lien / jeton expiré — refais le paiement ou reconnecte-toi" }, 401);
  }
  const email = String(payload.email).toLowerCase();
  const user = (await getUser(env, email)) || {
    status: "actif",
    createdAt: new Date().toISOString(),
  };
  // Claim Stripe permet de (re)définir le mdp après paiement vérifié
  const { hash, salt, iterations } = await hashPassword(password);
  user.hash = hash;
  user.salt = salt;
  user.iterations = iterations;
  user.status = user.status || "actif";
  user.updatedAt = new Date().toISOString();
  await putUser(env, email, user);

  const token = await signToken(env, { typ: "session", email }, SESSION_TTL_SEC);
  return json({ token, email });
}

async function login(request, env) {
  const body = await readJson(request);
  const email = String(body.email || "")
    .trim()
    .toLowerCase();
  const password = String(body.password || "");
  if (!email.includes("@") || password.length < 1) {
    return json({ error: "E-mail et mot de passe requis" }, 400);
  }
  const user = await getUser(env, email);
  if (!user || !user.hash || !["actif", "essai"].includes(user.status || "actif")) {
    return json({ error: "Identifiants incorrects ou abonnement inactif" }, 401);
  }
  const ok = await verifyPassword(
    password,
    user.salt,
    user.hash,
    user.iterations || PBKDF2_ITERS
  );
  if (!ok) {
    return json({ error: "Identifiants incorrects ou abonnement inactif" }, 401);
  }
  const token = await signToken(env, { typ: "session", email }, SESSION_TTL_SEC);
  return json({ token, email });
}

async function changePassword(request, env) {
  const auth = await requireSession(request, env);
  if (auth.error) return auth.error;
  const body = await readJson(request);
  const oldPw = String(body.old_password || "");
  const newPw = String(body.new_password || "");
  if (newPw.length < MIN_PASSWORD) {
    return json({ error: `Nouveau mot de passe : ${MIN_PASSWORD} caractères minimum` }, 400);
  }
  const user = await getUser(env, auth.email);
  if (!user || !user.hash) {
    return json({ error: "Compte introuvable" }, 404);
  }
  if (!(await verifyPassword(oldPw, user.salt, user.hash, user.iterations || PBKDF2_ITERS))) {
    return json({ error: "Ancien mot de passe incorrect" }, 401);
  }
  const { hash, salt, iterations } = await hashPassword(newPw);
  user.hash = hash;
  user.salt = salt;
  user.iterations = iterations;
  user.updatedAt = new Date().toISOString();
  await putUser(env, auth.email, user);
  const token = await signToken(env, { typ: "session", email: auth.email }, SESSION_TTL_SEC);
  return json({ ok: true, token, email: auth.email });
}

async function forgot(request, env, ctx) {
  const body = await readJson(request);
  const email = String(body.email || "")
    .trim()
    .toLowerCase();
  // Always OK (no email enumeration)
  const respond = json({
    ok: true,
    message: "Si un compte existe, un e-mail de réinitialisation a été envoyé.",
  });

  if (!email.includes("@") || !env.RESEND_API_KEY) {
    return respond;
  }
  const user = await getUser(env, email);
  if (!user || !user.hash) {
    return respond;
  }

  const resetToken = await signToken(env, { typ: "reset", email }, RESET_TTL_SEC);
  const base = (env.SITE_BASE || "").replace(/\/$/, "");
  const link = `${base}/membre/reset/?token=${encodeURIComponent(resetToken)}`;

  ctx.waitUntil(
    sendResend(env, {
      to: email,
      subject: "Réinitialisation mot de passe — Flipcards",
      html: `<p>Bonjour,</p>
<p>Pour choisir un nouveau mot de passe Flipcards (min. ${MIN_PASSWORD} caractères), ouvre ce lien (valable 1 h) :</p>
<p><a href="${link}">${link}</a></p>
<p>Si tu n’as pas demandé cette réinitialisation, ignore ce message.</p>`,
    }).catch((e) => console.error("resend", e))
  );

  return respond;
}

async function resetPassword(request, env) {
  const body = await readJson(request);
  const resetToken = String(body.token || "").trim();
  const password = String(body.password || "");
  if (password.length < MIN_PASSWORD) {
    return json({ error: `Mot de passe : ${MIN_PASSWORD} caractères minimum` }, 400);
  }
  const payload = await verifyToken(env, resetToken);
  if (!payload || payload.typ !== "reset" || !payload.email) {
    return json({ error: "Lien expiré ou invalide" }, 401);
  }
  const email = String(payload.email).toLowerCase();
  const user = await getUser(env, email);
  if (!user) {
    return json({ error: "Compte introuvable" }, 404);
  }
  const { hash, salt, iterations } = await hashPassword(password);
  user.hash = hash;
  user.salt = salt;
  user.iterations = iterations;
  user.updatedAt = new Date().toISOString();
  await putUser(env, email, user);
  const token = await signToken(env, { typ: "session", email }, SESSION_TTL_SEC);
  return json({ token, email });
}

async function me(request, env) {
  const auth = await requireSession(request, env);
  if (auth.error) return auth.error;
  const user = await getUser(env, auth.email);
  if (!user || !["actif", "essai"].includes(user.status || "actif")) {
    return json({ error: "Session invalide" }, 401);
  }
  return json({
    email: auth.email,
    status: user.status || "actif",
    has_password: Boolean(user.hash),
    cgv: user.cgv || null,
  });
}

async function adminMigrate(request, env) {
  const body = await readJson(request);
  const secret = String(body.admin_secret || "").trim();
  const expected = String(env.AUTH_SECRET || "").trim();
  if (!expected || secret !== expected) {
    return json({ error: "Non autorisé" }, 403);
  }
  const email = String(body.email || "")
    .trim()
    .toLowerCase();
  const password = String(body.password || "");
  if (!email.includes("@") || password.length < MIN_PASSWORD) {
    return json({ error: "email + password (min 4) requis" }, 400);
  }
  const { hash, salt, iterations } = await hashPassword(password);
  await putUser(env, email, {
    hash,
    salt,
    iterations,
    status: body.status || "actif",
    createdAt: new Date().toISOString(),
    migrated: true,
  });
  return json({ ok: true, email });
}

/* ---------- crypto / kv / stripe / mail ---------- */

async function requireSession(request, env) {
  const header = request.headers.get("Authorization") || "";
  const m = header.match(/^Bearer\s+(.+)$/i);
  if (!m) {
    return { error: json({ error: "Non authentifié" }, 401) };
  }
  const payload = await verifyToken(env, m[1].trim());
  if (!payload || payload.typ !== "session" || !payload.email) {
    return { error: json({ error: "Session expirée" }, 401) };
  }
  return { email: String(payload.email).toLowerCase() };
}

function userKey(email) {
  return `user:${email.toLowerCase()}`;
}

async function getUser(env, email) {
  if (!env.USERS) return null;
  const raw = await env.USERS.get(userKey(email));
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function putUser(env, email, data) {
  if (!env.USERS) {
    throw new Error("USERS KV non configuré — ajoutez [[kv_namespaces]] dans wrangler.toml puis wrangler deploy");
  }
  await env.USERS.put(userKey(email), JSON.stringify(data));
}

async function hashPassword(password, iterations = PBKDF2_ITERS) {
  const saltBytes = crypto.getRandomValues(new Uint8Array(16));
  const salt = b64(saltBytes);
  const hash = await pbkdf2(password, saltBytes, iterations);
  return { hash, salt, iterations };
}

async function verifyPassword(password, saltB64, hashB64, iterations = PBKDF2_ITERS) {
  if (!saltB64 || !hashB64) return false;
  const saltBytes = unb64(saltB64);
  const hash = await pbkdf2(password, saltBytes, iterations || PBKDF2_ITERS);
  return timingSafe.equal(hash, hashB64);
}

async function pbkdf2(password, saltBytes, iterations = PBKDF2_ITERS) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  );
  const bits = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt: saltBytes,
      iterations: iterations || PBKDF2_ITERS,
      hash: "SHA-256",
    },
    key,
    256
  );
  return b64(new Uint8Array(bits));
}

async function signToken(env, payload, ttlSec) {
  const secret = env.AUTH_SECRET;
  if (!secret) throw new Error("AUTH_SECRET missing");
  const body = {
    ...payload,
    exp: Math.floor(Date.now() / 1000) + ttlSec,
    iat: Math.floor(Date.now() / 1000),
  };
  const data = b64url(encJson(body));
  const sig = await hmacSign(secret, data);
  return `${data}.${sig}`;
}

async function verifyToken(env, token) {
  if (!token || !token.includes(".")) return null;
  const [data, sig] = token.split(".");
  const expected = await hmacSign(env.AUTH_SECRET, data);
  if (!timingSafe.equal(sig, expected)) return null;
  try {
    const payload = JSON.parse(decJson(unb64url(data)));
    if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch {
    return null;
  }
}

async function hmacSign(secret, data) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(data));
  return b64url(new Uint8Array(sig));
}

async function stripeGet(env, path) {
  const r = await fetch(`https://api.stripe.com/v1${path}`, {
    headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` },
  });
  return r.json();
}

async function sendResend(env, { to, subject, html }) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.RESEND_FROM || "Flipcards <onboarding@resend.dev>",
      to: [to],
      subject,
      html,
    }),
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`Resend ${r.status}: ${t}`);
  }
  return r.json();
}

/* ---------- helpers ---------- */

async function readJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}

function json(obj, status = 200, request = null, env = null) {
  const res = new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
  return request ? cors(res, request, env) : res;
}

function cors(res, request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = [
    env?.SITE_ORIGIN || "https://cabpechard-wq.github.io",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
  ];
  const headers = new Headers(res.headers);
  if (!origin || allowed.some((a) => origin === a || origin.startsWith(a))) {
    headers.set("Access-Control-Allow-Origin", origin || "*");
  }
  headers.set("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  headers.set(
    "Access-Control-Allow-Headers",
    "Content-Type, Authorization"
  );
  headers.set("Access-Control-Max-Age", "86400");
  headers.set("Vary", "Origin");
  return new Response(res.body, { status: res.status, headers });
}

function encJson(obj) {
  return new TextEncoder().encode(JSON.stringify(obj));
}
function decJson(bytes) {
  return new TextDecoder().decode(bytes);
}
function b64(bytes) {
  let s = "";
  bytes.forEach((b) => (s += String.fromCharCode(b)));
  return btoa(s);
}
function unb64(str) {
  const bin = atob(str);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
function b64url(bytes) {
  return b64(bytes).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function unb64url(str) {
  const pad = "=".repeat((4 - (str.length % 4)) % 4);
  const b64s = (str + pad).replace(/-/g, "+").replace(/_/g, "/");
  return unb64(b64s);
}
const timingSafe = {
  equal(a, b) {
    if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) {
      return false;
    }
    let out = 0;
    for (let i = 0; i < a.length; i++) out |= a.charCodeAt(i) ^ b.charCodeAt(i);
    return out === 0;
  },
};
