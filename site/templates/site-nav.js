/* Bandeau site : brand + liens + état connexion (email).
   Dépend de auth.js (FLIPCARDS_AUTH). Placer après auth.js. */
(function () {
  const script = document.currentScript;
  const root = new URL("./", script.src).href;

  function abs(path) {
    return new URL(path.replace(/^\//, ""), root).href;
  }

  const header = document.createElement("header");
  header.className = "site-nav";
  header.innerHTML =
    '<a class="site-nav-brand" href="' + abs("index.html") + '">' +
      '<span class="site-nav-kicker">Éditions Particulières</span>' +
      '<span class="site-nav-product">Droit public et administratif</span>' +
    "</a>" +
    '<nav class="site-nav-links" aria-label="Navigation">' +
      '<a data-nav="home" href="' + abs("index.html") + '">Accueil</a>' +
      '<a data-nav="bibliotheque" href="' + abs("bibliotheque/") + '">BU</a>' +
      '<a data-nav="ressources" href="' + abs("ressources/") + '">Amphi\'</a>' +
      '<a data-nav="exercices" href="' + abs("exercices/") + '">Salles de TD</a>' +
      '<a data-nav="checkout" href="' + abs("checkout/") + '">Inscriptions</a>' +
      '<span class="site-nav-guest">' +
        '<a data-nav="membre" href="' + abs("membre/") + '">Espace pédagogique</a>' +
      "</span>" +
      '<span class="site-nav-auth" hidden>' +
        '<a class="site-nav-user" href="' + abs("index.html") + '" title="Espace pédagogique">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
            '<path d="M4 6h16v12H4z"/><path d="M4 8l8 6 8-6"/>' +
          "</svg>" +
          '<span data-nav-email></span>' +
        "</a>" +
        '<button type="button" class="site-nav-logout" data-nav-logout>Déconnexion</button>' +
      "</span>" +
    "</nav>";

  document.body.prepend(header);
  document.body.classList.add("site-body");

  header.querySelectorAll("[data-nav]").forEach((a) => {
    const key = a.getAttribute("data-nav");
    const href = a.getAttribute("href") || "";
    try {
      const p = new URL(href).pathname.replace(/\/index\.html$/, "").replace(/\/+$/, "") || "/";
      const cur = location.pathname.replace(/\/index\.html$/, "").replace(/\/+$/, "") || "/";
      if (key === "home") {
        if (cur === p) a.classList.add("is-active");
      } else if (key === "ressources") {
        const onManuel = cur.indexOf("/manuel") !== -1;
        const onArrets = cur.indexOf("/arrets") !== -1;
        if (cur === p || onManuel || onArrets) {
          a.classList.add("is-active");
        }
      } else if (key === "bibliotheque") {
        const onDict = cur.indexOf("/dictionnaire") !== -1;
        if (cur === p || onDict) {
          a.classList.add("is-active");
        }
      } else if (key === "exercices") {
        // actif sur /exercices/, /demo/, /flipcards/ (pas /editions-particulieres/)
        const onDemo = cur.indexOf("/demo/") !== -1 || cur.endsWith("/demo");
        const onFlip = cur.indexOf("/flipcards/") !== -1 || cur.endsWith("/flipcards");
        if (cur === p || onDemo || onFlip) {
          a.classList.add("is-active");
        }
      } else if (cur === p || (p !== "/" && cur.startsWith(p + "/"))) {
        a.classList.add("is-active");
      }
    } catch (_) {}
  });

  const guest = header.querySelector(".site-nav-guest");
  const auth = header.querySelector(".site-nav-auth");
  const emailEl = header.querySelector("[data-nav-email]");
  const logoutBtn = header.querySelector("[data-nav-logout]");

  logoutBtn.addEventListener("click", () => {
    if (window.FLIPCARDS_AUTH) FLIPCARDS_AUTH.clearToken();
    location.href = abs("index.html");
  });

  async function refreshAuth() {
    if (!window.FLIPCARDS_AUTH) return null;
    const me = await FLIPCARDS_AUTH.requireSession();
    if (me && me.email) {
      guest.hidden = true;
      auth.hidden = false;
      emailEl.textContent = me.email;
    } else {
      guest.hidden = false;
      auth.hidden = true;
      emailEl.textContent = "";
    }
    return me;
  }

  function applyHomeAuth(isMember) {
    const btn = document.querySelector("[data-home-auth-btn]");
    if (!btn) return;
    if (isMember) {
      btn.textContent = "Déconnexion";
      btn.href = "#";
      btn.setAttribute("aria-label", "Se déconnecter");
      btn.dataset.authMode = "logout";
    } else {
      btn.textContent = "Se connecter";
      btn.href = abs("membre/");
      btn.setAttribute("aria-label", "Se connecter — Espace pédagogique");
      btn.dataset.authMode = "login";
    }
  }

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-home-auth-btn]");
    if (!btn || btn.dataset.authMode !== "logout") return;
    e.preventDefault();
    if (window.FLIPCARDS_AUTH) FLIPCARDS_AUTH.clearToken();
    location.href = abs("index.html");
  });

  function applyManuelPreview(isMember) {
    const prose = document.querySelector("article.manuel-prose");
    if (!prose) return;

    const wrap = document.querySelector(".manuel-readmore-wrap");
    if (wrap) wrap.remove();

    if (isMember) {
      prose.classList.remove("is-preview");
      return;
    }

    prose.classList.add("is-preview");
  }

  function blockCopyOn(el) {
    if (!el) return;
    ["copy", "cut", "contextmenu", "selectstart", "dragstart"].forEach((ev) => {
      el.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });
  }

  function protectManuelCopy() {
    const prose = document.querySelector("article.manuel-prose");
    if (!prose) return;
    blockCopyOn(prose);
    blockCopyOn(document.querySelector(".manuel-content"));
    document.addEventListener("keydown", (e) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      const key = String(e.key || "").toLowerCase();
      if (key !== "c" && key !== "x" && key !== "a" && key !== "s") return;
      const sel = window.getSelection && window.getSelection();
      if (!sel || sel.isCollapsed) {
        if (key === "a" || key === "s") {
          e.preventDefault();
        }
        return;
      }
      try {
        const node = sel.anchorNode && (sel.anchorNode.nodeType === 3
          ? sel.anchorNode.parentElement
          : sel.anchorNode);
        if (node && prose.contains(node)) e.preventDefault();
      } catch (_) {
        e.preventDefault();
      }
    });
  }

  // Infobulle titre complet sur les entrées tronquées du menu Manuel
  document.querySelectorAll(".manuel-nav-side .nav-title").forEach((el) => {
    const t = (el.textContent || "").trim();
    if (t) {
      const a = el.closest("a");
      if (a && !a.getAttribute("title")) a.setAttribute("title", t);
    }
  });

  function applyFlipcardsEntry(isMember) {
    document.querySelectorAll("[data-flipcards-entry]").forEach((el) => {
      const typeEl = el.querySelector("[data-fc-type]");
      const descEl = el.querySelector("[data-fc-desc]");
      const ctaEl = el.querySelector("[data-fc-cta]");
      if (isMember) {
        el.setAttribute("href", abs("flipcards/app.html"));
        if (typeEl) typeEl.textContent = "Accès membre";
        if (descEl) {
          descEl.textContent =
            "Jeu complet des flipcards : tous les arrêts, filtres par thèmes et notions, mode étude.";
        }
        if (ctaEl) ctaEl.textContent = "Ouvrir les flipcards →";
      } else {
        el.setAttribute("href", abs("demo/"));
        if (typeEl) typeEl.textContent = "Démo";
        if (descEl) {
          descEl.textContent =
            "Cartes recto / verso sur la jurisprudence essentielle. Thèmes, notions clés, règles de droit et portée des arrêts.";
        }
        if (ctaEl) ctaEl.textContent = "Essayer la démo →";
      }
    });
  }

  // Aperçu Manuel : verrouiller d'abord, déverrouiller si membre (évite le flash du texte complet)
  if (document.querySelector("article.manuel-prose")) {
    applyManuelPreview(false);
    protectManuelCopy();
  }

  function needsSiteTTS() {
    if (!("speechSynthesis" in window)) return false;
    return Boolean(
      document.querySelector("article.manuel-prose") ||
      document.querySelector(".dict-entries")
    );
  }

  function ensureSiteTTS(cb) {
    if (!needsSiteTTS()) {
      cb();
      return;
    }
    if (window.SiteTTS) {
      cb();
      return;
    }
    const existing = document.querySelector('script[src*="site-tts.js"]');
    if (existing) {
      if (window.SiteTTS) {
        cb();
        return;
      }
      existing.addEventListener("load", () => cb(), { once: true });
      existing.addEventListener("error", () => cb(), { once: true });
      return;
    }
    const s = document.createElement("script");
    s.src = abs("site-tts.js?v=8");
    s.onload = () => cb();
    s.onerror = () => cb();
    document.body.appendChild(s);
  }

  ensureSiteTTS(() => {
    refreshAuth().then((me) => {
      const ok = Boolean(me && me.email);
      applyHomeAuth(ok);
      applyManuelPreview(ok);
      applyFlipcardsEntry(ok);
      if (window.SiteTTS) window.SiteTTS.init(ok);
    });
  });

  function shouldShowErrorReport() {
    const cur = location.pathname || "";
    if (cur.indexOf("/manuel") !== -1) return true;
    if (cur.indexOf("/dictionnaire") !== -1) return true;
    if (cur.indexOf("/arrets") !== -1) return true;
    if (cur.indexOf("/demo/") !== -1 || cur.endsWith("/demo")) return true;
    if (cur.indexOf("/flipcards/") !== -1 || cur.endsWith("/flipcards")) return true;
    return false;
  }

  if (shouldShowErrorReport()) {
    const report = document.createElement("a");
    report.className = "site-error-report";
    report.href =
      "mailto:cab.pechard@gmail.com"
      + "?subject=" + encodeURIComponent("Signaler une erreur / suggérer un ajout")
      + "&body=" + encodeURIComponent(
        "Bonjour,\n\nJe souhaite signaler une erreur ou suggérer un ajout sur la page suivante :\n"
        + location.href
        + "\n\nDescription :\n"
      );
    report.textContent = "Signaler une erreur / suggérer un ajout";
    report.setAttribute(
      "aria-label",
      "Signaler une erreur ou suggérer un ajout par e-mail"
    );
    document.body.appendChild(report);
  }

  const footer = document.createElement("footer");
  footer.className = "site-footer";
  footer.innerHTML =
    '<div class="site-footer-inner">' +
      '<div class="site-footer-meta">' +
        '<p class="site-footer-brand">Éditions Particulières — Droit public et administratif</p>' +
        '<p class="site-footer-copy">© Éditions Particulières · Tous droits réservés · Reproductions / exportations interdites</p>' +
      "</div>" +
      '<nav class="site-footer-links" aria-label="Informations légales">' +
        '<a href="' + abs("mentions-legales/") + '">Mentions légales</a>' +
        '<a href="' + abs("cgv/") + '">CGV</a>' +
        '<a href="mailto:cab.pechard@gmail.com">Contact</a>' +
      "</nav>" +
    "</div>";
  document.body.appendChild(footer);

  // Sélecteur de charte (Campus par défaut) — chargé après le bandeau
  const themeJs = document.createElement("script");
  themeJs.src = new URL("site-theme.js?v=5", script.src).href;
  themeJs.onerror = function () {
    console.warn("[site-theme] Impossible de charger site-theme.js — rebuild du site requis.");
  };
  document.body.appendChild(themeJs);
})();
