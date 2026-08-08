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

const src = pickSource();
if (src) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  console.log(`Synced ${src} -> mobile/assets/cards.json`);
}
