import { useCallback, useMemo, useState } from "react";
import { allCards, Card } from "../data/cards";

export type FilterGroup = "theme" | "notion";

function matchesFilters(
  card: Card,
  themes: string[],
  notions: string[]
): boolean {
  if (themes.length && !(card.themes || []).some((t) => themes.includes(t))) {
    return false;
  }
  if (
    notions.length &&
    !(card.notions || []).some((n) => notions.includes(n))
  ) {
    return false;
  }
  return true;
}

export function useFilters() {
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedNotions, setSelectedNotions] = useState<string[]>([]);

  const filteredCards = useMemo(
    () =>
      allCards.filter((c) =>
        matchesFilters(c, selectedThemes, selectedNotions)
      ),
    [selectedThemes, selectedNotions]
  );

  const compatible = useMemo(() => {
    const themes = new Set<string>();
    const notions = new Set<string>();
    for (const card of filteredCards) {
      (card.themes || []).forEach((t) => themes.add(t));
      (card.notions || []).forEach((n) => notions.add(n));
    }
    return { themes, notions };
  }, [filteredCards]);

  const anyFilter = selectedThemes.length > 0 || selectedNotions.length > 0;

  const isChipEnabled = useCallback(
    (group: FilterGroup, value: string) => {
      const selected =
        group === "theme" ? selectedThemes.includes(value) : selectedNotions.includes(value);
      if (selected || !anyFilter) return true;
      return group === "theme"
        ? compatible.themes.has(value)
        : compatible.notions.has(value);
    },
    [anyFilter, compatible, selectedThemes, selectedNotions]
  );

  const toggle = useCallback((group: FilterGroup, value: string) => {
    if (group === "theme") {
      setSelectedThemes((prev) =>
        prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
      );
    } else {
      setSelectedNotions((prev) =>
        prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
      );
    }
  }, []);

  const clear = useCallback((group: FilterGroup) => {
    if (group === "theme") setSelectedThemes([]);
    else setSelectedNotions([]);
  }, []);

  const selectionHint = useMemo(() => {
    if (!anyFilter) return "Tout le set";
    const bits: string[] = [];
    if (selectedThemes.length) bits.push(`${selectedThemes.length} thème(s)`);
    if (selectedNotions.length) bits.push(`${selectedNotions.length} notion(s)`);
    return bits.join(" · ");
  }, [anyFilter, selectedThemes.length, selectedNotions.length]);

  return {
    selectedThemes,
    selectedNotions,
    filteredCards,
    count: filteredCards.length,
    anyFilter,
    isChipEnabled,
    toggle,
    clear,
    selectionHint,
  };
}
