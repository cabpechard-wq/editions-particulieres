import raw from "../../assets/cards.json";

export type Card = {
  id: string;
  recto: string;
  verso: string;
  url?: string;
  date?: string;
  juridiction?: string;
  formation?: string;
  titre?: string;
  reference?: string;
  importance?: string;
  theme?: string;
  themes: string[];
  notions: string[];
  objet?: string;
  portee?: string;
  considerant?: string;
};

export type FlipcardsData = {
  kind: string;
  count: number;
  recto_field: string;
  verso_field: string;
  classifiers: {
    theme_field: string;
    notions_field: string;
    themes: string[];
    notions: string[];
  };
  classifier_colors?: {
    themes?: Record<string, string>;
    notions?: Record<string, string>;
  };
  cards: Card[];
};

export const PAGE_TITLE = "Grands arrêts du droit public et administratif";

export const data = raw as FlipcardsData;
export const allCards: Card[] = (data.cards || []).filter((c) => !!c.recto);
export const allThemes: string[] = data.classifiers?.themes || [];
export const allNotions: string[] = data.classifiers?.notions || [];

const themeColors = data.classifier_colors?.themes || {};
const notionColors = data.classifier_colors?.notions || {};

function lookupColor(
  label: string,
  mapping: Record<string, string>
): string {
  const bit = (label || "").trim();
  if (!bit) return "default";
  if (mapping[bit]) return mapping[bit];
  // Thèmes parfois stockés avec préfixe numérique dans le mapping
  for (const [k, v] of Object.entries(mapping)) {
    if (
      k === bit ||
      k.endsWith(`-${bit}`) ||
      k.endsWith(`–${bit}`) ||
      k.endsWith(`—${bit}`)
    ) {
      return v;
    }
    const m = k.match(/^\d+\s*[-–—]\s*(.+)$/);
    if (m && m[1].trim() === bit) return v;
  }
  return "default";
}

export function colorForLabel(
  label: string,
  group: "theme" | "notion"
): string {
  return lookupColor(label, group === "theme" ? themeColors : notionColors);
}
