import { useRouter } from "expo-router";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { FlipCard } from "../src/components/FlipCard";
import {
  cardImportanceLevel,
  colorForLabel,
  starsLabel,
} from "../src/data/cards";
import { useStudySession } from "../src/data/StudyContext";
import { colors, notionTone } from "../src/theme/colors";

const PLAY_RECTO_MS = 3000;
const PLAY_VERSO_MS = 7000;

function shuffle<T>(arr: T[]): T[] {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function DetailBox({ title, text }: { title: string; text?: string }) {
  const empty = !(text || "").trim();
  return (
    <View style={styles.detailBox}>
      <Text style={styles.detailLabel}>{title}</Text>
      <Text style={[styles.detailText, empty && styles.detailEmpty]}>
        {empty ? "— Non renseigné —" : text}
      </Text>
    </View>
  );
}

function ColoredTag({
  label,
  group,
}: {
  label: string;
  group: "theme" | "notion";
}) {
  const tone = notionTone(colorForLabel(label, group));
  return (
    <Text
      style={[
        styles.tag,
        { borderColor: tone.border, color: colors.muted },
      ]}
    >
      {label}
    </Text>
  );
}

export default function StudyScreen() {
  const router = useRouter();
  const { session } = useStudySession();
  const base = session.cards;

  const [order, setOrder] = useState(() => base.map((_, i) => i));
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [shuffled, setShuffled] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flippedRef = useRef(flipped);
  const indexRef = useRef(index);
  const playingRef = useRef(playing);
  const cardsLenRef = useRef(0);

  flippedRef.current = flipped;
  indexRef.current = index;
  playingRef.current = playing;

  useEffect(() => {
    setOrder(base.map((_, i) => i));
    setIndex(0);
    setFlipped(false);
    setShuffled(false);
    setPlaying(false);
    setDetailsOpen(false);
  }, [base]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const cards = useMemo(
    () => order.map((i) => base[i]).filter(Boolean),
    [order, base]
  );
  cardsLenRef.current = cards.length;
  const current = cards[index];

  const stopPlay = () => {
    setPlaying(false);
    playingRef.current = false;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const go = (n: number) => {
    if (!cardsLenRef.current) return;
    const len = cardsLenRef.current;
    const next = ((n % len) + len) % len;
    setIndex(next);
    indexRef.current = next;
    setFlipped(false);
    flippedRef.current = false;
  };

  const schedulePlayStep = () => {
    if (!playingRef.current || !cardsLenRef.current) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    const delay = flippedRef.current ? PLAY_VERSO_MS : PLAY_RECTO_MS;
    timerRef.current = setTimeout(() => {
      if (!playingRef.current) return;
      if (!flippedRef.current) {
        setFlipped(true);
        flippedRef.current = true;
        schedulePlayStep();
      } else {
        go(indexRef.current + 1);
        schedulePlayStep();
      }
    }, delay);
  };

  const togglePlay = () => {
    if (playing) {
      stopPlay();
      return;
    }
    if (!cards.length) return;
    setPlaying(true);
    playingRef.current = true;
    schedulePlayStep();
  };

  const toggleShuffle = () => {
    stopPlay();
    setShuffled((s) => {
      const next = !s;
      setOrder(next ? shuffle(base.map((_, i) => i)) : base.map((_, i) => i));
      setIndex(0);
      setFlipped(false);
      return next;
    });
  };

  if (!base.length || !current) {
    return (
      <SafeAreaView style={styles.safe}>
        <Pressable onPress={() => router.back()} style={{ padding: 16 }}>
          <Text style={styles.backText}>← Accueil</Text>
        </Pressable>
        <Text style={styles.empty}>Aucune carte pour ces filtres.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top", "left", "right"]}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.bar}>
          <Pressable
            onPress={() => {
              stopPlay();
              router.back();
            }}
          >
            <Text style={styles.backText}>← Accueil</Text>
          </Pressable>
          <Text style={styles.summary} numberOfLines={2}>
            {session.hint}
          </Text>
        </View>

        <View style={styles.progressTrack}>
          <View
            style={[
              styles.progressFill,
              { width: `${((index + 1) / cards.length) * 100}%` },
            ]}
          />
        </View>

        <FlipCard
          recto={current.recto}
          verso={current.verso}
          flipped={flipped}
          onFlip={() => setFlipped((v) => !v)}
          stars={starsLabel(cardImportanceLevel(current))}
        />

        <View style={styles.controls}>
          <View style={styles.side}>
            <Pressable
              onPress={togglePlay}
              style={[styles.iconBtn, playing && styles.iconActive]}
              accessibilityLabel="Lecture auto (recto 3 s · verso 7 s)"
            >
              <Text style={[styles.icon, playing && styles.iconActiveText]}>
                {playing ? "⏸" : "▶"}
              </Text>
            </Pressable>
            <Pressable
              onPress={toggleShuffle}
              style={[styles.iconBtn, shuffled && styles.iconActive]}
              accessibilityLabel="Mélanger"
            >
              <Text style={[styles.icon, shuffled && styles.iconActiveText]}>
                ⇄
              </Text>
            </Pressable>
          </View>
          <View style={styles.center}>
            <Pressable
              onPress={() => {
                stopPlay();
                go(index - 1);
              }}
              style={styles.navBtn}
            >
              <Text style={styles.navText}>‹</Text>
            </Pressable>
            <Text style={styles.counter}>
              {index + 1} / {cards.length}
            </Text>
            <Pressable
              onPress={() => {
                stopPlay();
                go(index + 1);
              }}
              style={styles.navBtn}
            >
              <Text style={[styles.navText, styles.navPrimaryText]}>›</Text>
            </Pressable>
          </View>
          <View style={[styles.side, styles.sideRight]} />
        </View>

        <Pressable
          onPress={() => setDetailsOpen((v) => !v)}
          style={[styles.detailsBtn, detailsOpen && styles.detailsBtnActive]}
          accessibilityState={{ expanded: detailsOpen }}
        >
          <Text
            style={[
              styles.detailsBtnText,
              detailsOpen && styles.detailsBtnTextActive,
            ]}
          >
            Objet · Portée · Considérant
          </Text>
        </Pressable>

        {detailsOpen ? (
          <View style={styles.details}>
            <DetailBox title="Objet" text={current.objet} />
            <DetailBox title="Portée" text={current.portee} />
            <DetailBox title="Considérant de principe" text={current.considerant} />
          </View>
        ) : null}

        <View style={styles.list}>
          {cards.map((c) => (
            <View key={c.id || c.recto} style={styles.row}>
              <View style={styles.rowLeft}>
                <Text style={styles.rowTitle}>{c.recto}</Text>
                <View style={styles.tags}>
                  {starsLabel(cardImportanceLevel(c)) ? (
                    <Text style={styles.rowStars}>
                      {starsLabel(cardImportanceLevel(c))}
                    </Text>
                  ) : null}
                  {(c.themes || []).map((t) => (
                    <ColoredTag key={`t-${t}`} label={t} group="theme" />
                  ))}
                  {(c.notions || []).map((n) => (
                    <ColoredTag key={`n-${n}`} label={n} group="notion" />
                  ))}
                </View>
              </View>
              <Text style={styles.rowVerso}>{c.verso || "—"}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: 16, paddingBottom: 48, maxWidth: 560, width: "100%", alignSelf: "center" },
  bar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 14,
  },
  backText: {
    fontWeight: "600",
    color: colors.accent,
    fontSize: 14,
  },
  summary: {
    flex: 1,
    textAlign: "right",
    color: colors.muted,
    fontWeight: "500",
    fontSize: 13,
  },
  progressTrack: {
    height: 2,
    backgroundColor: "#f3f4f6",
    borderRadius: 99,
    overflow: "hidden",
    marginBottom: 12,
    alignSelf: "center",
    width: "100%",
    maxWidth: 448,
  },
  progressFill: {
    height: "100%",
    backgroundColor: colors.accent,
  },
  controls: {
    marginTop: 12,
    flexDirection: "row",
    alignItems: "center",
  },
  side: { flex: 1, flexDirection: "row", gap: 2 },
  sideRight: { justifyContent: "flex-end" },
  center: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: colors.radius,
    alignItems: "center",
    justifyContent: "center",
  },
  iconActive: { backgroundColor: colors.accentSoft },
  icon: { fontSize: 15, color: colors.ink },
  iconActiveText: { color: colors.accent },
  navBtn: {
    width: 36,
    height: 36,
    borderRadius: colors.radius,
    alignItems: "center",
    justifyContent: "center",
  },
  navText: { fontSize: 26, color: colors.ink, lineHeight: 28 },
  navPrimaryText: { color: colors.accent },
  counter: {
    fontWeight: "700",
    color: colors.ink,
    fontVariant: ["tabular-nums"],
    minWidth: 64,
    textAlign: "center",
  },
  detailsBtn: {
    alignSelf: "center",
    marginTop: 12,
    borderWidth: 2,
    borderColor: "#d1d5db",
    backgroundColor: "#fff",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  detailsBtnActive: {
    backgroundColor: colors.accent,
    borderColor: colors.accent,
  },
  detailsBtnText: {
    color: colors.muted,
    fontWeight: "600",
    fontSize: 13,
  },
  detailsBtnTextActive: { color: "#fff" },
  details: {
    marginTop: 12,
    gap: 10,
    width: "100%",
  },
  detailBox: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: colors.radius,
    paddingHorizontal: 12,
    paddingTop: 10,
    paddingBottom: 12,
  },
  detailLabel: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: colors.muted,
    marginBottom: 6,
  },
  detailText: {
    fontSize: 14,
    lineHeight: 21,
    color: colors.versoText,
  },
  detailEmpty: {
    color: colors.muted,
    fontStyle: "italic",
  },
  list: { marginTop: 28, gap: 8 },
  row: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderLeftWidth: 3,
    borderLeftColor: colors.accent,
    borderRadius: colors.radius,
    padding: 14,
    gap: 10,
  },
  rowLeft: { gap: 6 },
  rowTitle: {
    fontWeight: "700",
    color: colors.ink,
    fontSize: 16,
    fontFamily: "serif",
  },
  tags: { flexDirection: "row", flexWrap: "wrap", gap: 4, alignItems: "center" },
  rowStars: {
    fontSize: 12,
    letterSpacing: 1,
    color: colors.accent,
    fontWeight: "700",
    marginRight: 2,
  },
  tag: {
    fontSize: 11,
    fontWeight: "600",
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 999,
    borderWidth: 2,
    overflow: "hidden",
    backgroundColor: "#fff",
  },
  rowVerso: { color: "#4b5563", lineHeight: 20, fontSize: 14 },
  empty: {
    marginTop: 40,
    textAlign: "center",
    color: colors.muted,
    fontSize: 16,
  },
});
