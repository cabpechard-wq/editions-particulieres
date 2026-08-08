import { useRouter } from "expo-router";
import React from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Accordion } from "../src/components/Accordion";
import { Chip } from "../src/components/Chip";
import {
  PAGE_TITLE,
  allCards,
  allNotions,
  allThemes,
  colorForLabel,
  presentImportanceLevels,
  starsLabel,
  type Card,
} from "../src/data/cards";
import { useStudySession } from "../src/data/StudyContext";
import { useFilters } from "../src/hooks/useFilters";
import { colors } from "../src/theme/colors";

function shuffle<T>(arr: T[]): T[] {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export default function HomeScreen() {
  const router = useRouter();
  const { setSession } = useStudySession();
  const {
    selectedThemes,
    selectedNotions,
    selectedImportance,
    filteredCards,
    count,
    isChipEnabled,
    toggle,
    clear,
    selectionHint,
  } = useFilters();

  const enterStudy = (cards: Card[], hint: string) => {
    if (!cards.length) return;
    setSession({ cards, hint });
    router.push("/study");
  };

  const startAll = () => {
    const cards = shuffle(filteredCards);
    enterStudy(cards, `${selectionHint} · ${cards.length} carte(s)`);
  };

  const startRandom10 = () => {
    const pool = shuffle(filteredCards);
    const cards = pool.slice(0, Math.min(10, pool.length));
    const hint =
      "10 au hasard" +
      (filteredCards.length < 10 ? ` (${cards.length})` : "") +
      ` · ${selectionHint}`;
    enterStudy(cards, hint);
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "left", "right"]}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>{PAGE_TITLE}</Text>
        <Text style={styles.sub}>
          1 thème (choix unique), notions et importance — comme sur le web.
          Laissez vide pour tout le set ({allCards.length} cartes).
        </Text>

        <View style={styles.card}>
          <Accordion
            title="1 — Thèmes (1 seul choix)"
            onClear={() => clear("theme")}
          >
            <View style={styles.chips}>
              {allThemes.length ? (
                allThemes.map((t) => (
                  <Chip
                    key={t}
                    label={t}
                    colorName={colorForLabel(t, "theme")}
                    selected={selectedThemes.includes(t)}
                    disabled={!isChipEnabled("theme", t)}
                    onPress={() => toggle("theme", t)}
                  />
                ))
              ) : (
                <Text style={styles.emptyChips}>Aucun classificateur renseigné.</Text>
              )}
            </View>
          </Accordion>

          <Accordion title="2 — Notions" onClear={() => clear("notion")}>
            <View style={styles.chips}>
              {allNotions.length ? (
                allNotions.map((n) => (
                  <Chip
                    key={n}
                    label={n}
                    colorName={colorForLabel(n, "notion")}
                    selected={selectedNotions.includes(n)}
                    disabled={!isChipEnabled("notion", n)}
                    onPress={() => toggle("notion", n)}
                  />
                ))
              ) : (
                <Text style={styles.emptyChips}>Aucun classificateur renseigné.</Text>
              )}
            </View>
          </Accordion>

          <Accordion
            title="3 — Importance"
            onClear={() => clear("importance")}
          >
            <View style={styles.chips}>
              {(presentImportanceLevels.length
                ? presentImportanceLevels
                : [1, 2, 3, 4]
              ).map((lvl) => (
                <Chip
                  key={lvl}
                  label={starsLabel(lvl)}
                  colorName="default"
                  selected={selectedImportance.includes(lvl)}
                  disabled={!isChipEnabled("importance", lvl)}
                  onPress={() => toggle("importance", lvl)}
                />
              ))}
            </View>
          </Accordion>

          <View style={styles.footer}>
            <View style={styles.countBlock}>
              <Text style={styles.count}>
                <Text style={styles.countNum}>{count}</Text> carte(s)
              </Text>
              <Text style={styles.hint}>{selectionHint}</Text>
            </View>
            <View style={styles.actions}>
              <Pressable
                onPress={startRandom10}
                disabled={!count}
                style={[styles.btnRandom, !count && styles.btnDisabled]}
              >
                <Text style={styles.btnRandomText}>10 au hasard…</Text>
              </Pressable>
              <Pressable
                onPress={startAll}
                disabled={!count}
                style={[styles.btn, !count && styles.btnDisabled]}
              >
                <Text style={styles.btnText}>Étudier</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: 16, paddingBottom: 40 },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: colors.title,
    marginBottom: 6,
    letterSpacing: -0.4,
    fontFamily: "serif",
  },
  sub: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 18,
    maxWidth: 520,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: colors.radius,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 16,
    paddingTop: 4,
    paddingBottom: 16,
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 7,
  },
  emptyChips: { color: colors.muted, fontSize: 14 },
  footer: {
    gap: 14,
    marginTop: 8,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  countBlock: { gap: 2 },
  count: { fontSize: 16, fontWeight: "600", color: colors.ink },
  countNum: {
    color: colors.accent,
    fontSize: 19,
    fontWeight: "700",
    fontFamily: "serif",
  },
  hint: { color: colors.muted, fontSize: 13, fontWeight: "500" },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  btn: {
    flexGrow: 1,
    backgroundColor: colors.accent,
    borderRadius: colors.radius,
    paddingHorizontal: 18,
    paddingVertical: 13,
    alignItems: "center",
  },
  btnRandom: {
    flexGrow: 1,
    backgroundColor: "#fff",
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: colors.radius,
    paddingHorizontal: 16,
    paddingVertical: 12,
    alignItems: "center",
  },
  btnDisabled: { opacity: 0.35 },
  btnText: { color: "#fff", fontWeight: "700", fontSize: 15 },
  btnRandomText: { color: colors.ink, fontWeight: "700", fontSize: 15 },
});
