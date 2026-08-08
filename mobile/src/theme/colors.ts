/** Aligné sur le HTML (`flipcards/generator.py` :root). */
export const colors = {
  bg: "#ffffff",
  card: "#ffffff",
  ink: "#1a1a1a",
  muted: "#6b7280",
  accent: "#0f766e",
  accentHover: "#0d9488",
  accentSoft: "#ccfbf1",
  brass: "#b45309",
  border: "#e5e7eb",
  bar: "#1a1a1a",
  title: "#1a1a1a",
  clear: "#c4c8d0",
  ok: "#047857",
  okSoft: "#d1fae5",
  disabledBg: "#ffffff",
  versoText: "#374151",
  radius: 6,
};

/** Palette Notion des chips / tags (bordure repos, teinte vive). */
export const notionPalette: Record<string, { border: string; vivid: string }> = {
  default: { border: "#d1d5db", vivid: "#4b5563" },
  gray: { border: "#d1d5db", vivid: "#4b5563" },
  brown: { border: "#d4a574", vivid: "#9a5b3a" },
  orange: { border: "#fdba74", vivid: "#ea580c" },
  yellow: { border: "#facc15", vivid: "#ca8a04" },
  green: { border: "#a8bba8", vivid: "#4a6b52" },
  blue: { border: "#93c5fd", vivid: "#2563eb" },
  purple: { border: "#d8b4fe", vivid: "#9333ea" },
  pink: { border: "#f9a8d4", vivid: "#db2777" },
  red: { border: "#fca5a5", vivid: "#dc2626" },
};

export function notionTone(name?: string | null) {
  const key = (name || "default").toLowerCase();
  return notionPalette[key] || notionPalette.default;
}
