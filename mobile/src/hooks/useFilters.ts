import { useCallback, useMemo, useState } from "react";
import {
  allCards,
  cardImportanceLevel,
  type Card,
} from "../data/cards";

export type FilterGroup = "theme" | "notion" | "importance";

type UpstreamOpts = {
  applyTheme?: boolean;
  applyNotion?: boolean;
  applyImportance?: boolean;
};

function matchesUpstream(
  card: Card,
  themes: string[],
  notions: string[],
  levels: number[],
  opts: UpstreamOpts = {}
): boolean {
  const applyTheme = opts.applyTheme !== false;
  const applyNotion = opts.applyNotion !== false;
  const applyImportance = opts.applyImportance !== false;

  if (
    applyTheme &&
    themes.length &&
    !(card.themes || []).some((t) => themes.includes(t))
  ) {
    return false;
  }
  if (
    applyNotion &&
    notions.length &&
    !(card.notions || []).some((n) => notions.includes(n))
  ) {
    return false;
  }
  if (applyImportance && levels.length) {
    const lvl = cardImportanceLevel(card);
    if (!levels.includes(lvl)) return false;
  }
  return true;
}

/**
 * Filtres alignés web (flipcards/generator.py) :
 * - Thème : un seul choix
 * - Notions : multi OR
 * - Importance : multi OR sur niveaux 1–4
 * Cascade chips : Thème → Notions → ★
 */
export function useFilters() {
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedNotions, setSelectedNotions] = useState<string[]>([]);
  const [selectedImportance, setSelectedImportance] = useState<number[]>([]);

  const filteredCards = useMemo(
    () =>
      allCards.filter((c) =>
        matchesUpstream(c, selectedThemes, selectedNotions, selectedImportance)
      ),
    [selectedThemes, selectedNotions, selectedImportance]
  );

  const anyFilter =
    selectedThemes.length > 0 ||
    selectedNotions.length > 0 ||
    selectedImportance.length > 0;

  const isChipEnabled = useCallback(
    (group: FilterGroup, value: string | number) => {
      if (group === "theme") {
        const v = String(value);
        if (selectedThemes.includes(v) || !anyFilter) return true;
        // Thème : dispo si une carte matche notions+importance (sans thème)
        return allCards.some((card) =>
          matchesUpstream(card, [], selectedNotions, selectedImportance, {
            applyTheme: false,
            applyNotion: true,
            applyImportance: true,
          }) && (card.themes || []).includes(v)
        );
      }
      if (group === "notion") {
        const v = String(value);
        if (selectedNotions.includes(v)) return true;
        // Notions : scopées par thème seul
        return allCards.some(
          (card) =>
            matchesUpstream(card, selectedThemes, [], [], {
              applyTheme: true,
              applyNotion: false,
              applyImportance: false,
            }) && (card.notions || []).includes(v)
        );
      }
      // Importance : scopée par thème + notions
      const lvl = Number(value);
      if (selectedImportance.includes(lvl)) return true;
      return allCards.some(
        (card) =>
          matchesUpstream(card, selectedThemes, selectedNotions, [], {
            applyTheme: true,
            applyNotion: true,
            applyImportance: false,
          }) && cardImportanceLevel(card) === lvl
      );
    },
    [anyFilter, selectedThemes, selectedNotions, selectedImportance]
  );

  const toggle = useCallback((group: FilterGroup, value: string | number) => {
    if (group === "theme") {
      const v = String(value);
      // Un seul thème (comme le web)
      setSelectedThemes((prev) => (prev.includes(v) ? [] : [v]));
      return;
    }
    if (group === "notion") {
      const v = String(value);
      setSelectedNotions((prev) =>
        prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]
      );
      return;
    }
    const lvl = Number(value);
    setSelectedImportance((prev) =>
      prev.includes(lvl) ? prev.filter((x) => x !== lvl) : [...prev, lvl]
    );
  }, []);

  const clear = useCallback((group: FilterGroup) => {
    if (group === "theme") setSelectedThemes([]);
    else if (group === "notion") setSelectedNotions([]);
    else setSelectedImportance([]);
  }, []);

  const selectionHint = useMemo(() => {
    if (!anyFilter) return "Tout le set";
    const bits: string[] = [];
    if (selectedThemes.length) bits.push(selectedThemes[0]);
    if (selectedNotions.length) bits.push(`${selectedNotions.length} notion(s)`);
    if (selectedImportance.length) {
      bits.push(
        selectedImportance
          .slice()
          .sort()
          .map((n) => "★".repeat(n))
          .join(" ")
      );
    }
    return bits.join(" · ");
  }, [anyFilter, selectedThemes, selectedNotions, selectedImportance]);

  return {
    selectedThemes,
    selectedNotions,
    selectedImportance,
    filteredCards,
    count: filteredCards.length,
    anyFilter,
    isChipEnabled,
    toggle,
    clear,
    selectionHint,
  };
}
