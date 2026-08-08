const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const dest = path.join(__dirname, "..", "assets", "cards.json");

function isFlipcardsJson(fileName) {
  const lower = fileName.toLowerCase();
  if (!lower.endsWith(".json")) return false;
  if (lower === "cards.json") return true;
  return (
    lower.includes("flipcards") ||
    lower.includes("grands arrêts") ||
    lower.includes("grands arrets")
  );
}

function candidateDirs() {
  const dirs = [];
  const envRoot = (process.env.EP_OUTPUT_ROOT || "").trim();
  if (envRoot) {
    dirs.push(path.join(envRoot, "flipcards", "output"));
    dirs.push(path.join(envRoot, "output"));
  }
  // Convention monorepo (Google Drive)
  dirs.push(path.join("G:", "Mon Drive", "Editions Particulieres", "flipcards", "output"));
  // Cache local repo (exports HTML/JSON hors Drive)
  dirs.push(path.join(repoRoot, "output"));
  dirs.push(path.join(repoRoot, "flipcards", "output"));
  return [...new Set(dirs.map((d) => path.resolve(d)))];
}

function pickSource() {
  const found = [];
  for (const outputDir of candidateDirs()) {
    if (!fs.existsSync(outputDir)) continue;
    for (const f of fs.readdirSync(outputDir).filter(isFlipcardsJson)) {
      const full = path.join(outputDir, f);
      found.push({ full, mtime: fs.statSync(full).mtimeMs });
    }
  }
  found.sort((a, b) => b.mtime - a.mtime);
  if (!found.length) {
    if (fs.existsSync(dest)) {
      console.warn(
        "Aucun JSON source trouvé — conservation de mobile/assets/cards.json existant."
      );
      console.warn(
        "Pour rafraîchir : python -m flipcards --offline --format json"
      );
      return null;
    }
    throw new Error(
      "Aucun JSON flipcards trouvé (EP_OUTPUT_ROOT/flipcards/output, Drive, ou repo/output/).\n" +
        "Lance : python -m flipcards --offline --format json"
    );
  }
  return found[0].full;
}

/** Aligné generator.importance_level — complète les JSON anciens. */
function importanceLevelFromRaw(raw) {
  const s = String(raw || "").trim();
  if (!s) return 0;
  const star =
    (s.match(/⭐/g) || []).length ||
    (s.match(/★/g) || []).length ||
    (s.match(/\*/g) || []).length;
  if (star) return Math.min(4, Math.max(1, star));
  const m = s.match(/[1-4]/);
  return m ? Number(m[0]) : 0;
}

function enrichCardsJson(filePath) {
  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return { enriched: 0 };
  }
  if (!data || !Array.isArray(data.cards)) return { enriched: 0 };
  let enriched = 0;
  for (const card of data.cards) {
    const lvl = Number(card.importance_level) || 0;
    if (lvl >= 1 && lvl <= 4) continue;
    const derived = importanceLevelFromRaw(card.importance);
    if (derived) {
      card.importance_level = derived;
      enriched += 1;
    }
  }
  if (enriched) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf8");
  }
  return { enriched, count: data.cards.length };
}

const src = pickSource();
if (src) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  console.log(`Synced ${src} -> mobile/assets/cards.json`);
}

if (fs.existsSync(dest)) {
  const { enriched, count } = enrichCardsJson(dest);
  if (enriched) {
    console.log(
      `Enrichi importance_level sur ${enriched}/${count} carte(s) (JSON ancien).`
    );
  } else if (count != null) {
    console.log(`OK ${count} carte(s) — importance_level à jour.`);
  }
}
