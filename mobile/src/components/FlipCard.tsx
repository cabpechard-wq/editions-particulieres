import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Animated, {
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import { colors } from "../theme/colors";

type Props = {
  recto: string;
  verso: string;
  flipped: boolean;
  onFlip: () => void;
};

export function FlipCard({ recto, verso, flipped, onFlip }: Props) {
  const progress = useSharedValue(flipped ? 1 : 0);

  React.useEffect(() => {
    progress.value = withTiming(flipped ? 1 : 0, { duration: 600 });
  }, [flipped, progress]);

  const frontStyle = useAnimatedStyle(() => ({
    transform: [
      { perspective: 1600 },
      { rotateY: `${interpolate(progress.value, [0, 1], [0, 180])}deg` },
    ],
    opacity: progress.value < 0.5 ? 1 : 0,
    zIndex: progress.value < 0.5 ? 2 : 0,
  }));

  const backStyle = useAnimatedStyle(() => ({
    transform: [
      { perspective: 1600 },
      { rotateY: `${interpolate(progress.value, [0, 1], [180, 360])}deg` },
    ],
    opacity: progress.value >= 0.5 ? 1 : 0,
    zIndex: progress.value >= 0.5 ? 2 : 0,
  }));

  return (
    <Pressable onPress={onFlip} style={styles.scene} accessibilityRole="button">
      <View style={styles.inner}>
        <Animated.View style={[styles.face, frontStyle]}>
          <Text style={styles.term}>{recto}</Text>
        </Animated.View>
        <Animated.View style={[styles.face, styles.faceBack, backStyle]}>
          <Text style={[styles.def, !verso && styles.empty]}>
            {verso || "— Verso non renseigné —"}
          </Text>
        </Animated.View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  scene: {
    width: "100%",
    aspectRatio: 2,
    minHeight: 168,
    maxHeight: 288,
  },
  inner: {
    flex: 1,
  },
  face: {
    ...StyleSheet.absoluteFill,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: colors.radius,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 22,
    paddingVertical: 20,
    backfaceVisibility: "hidden",
  },
  faceBack: {
    alignItems: "stretch",
  },
  term: {
    fontSize: 20,
    fontWeight: "600",
    color: colors.ink,
    textAlign: "center",
    lineHeight: 28,
  },
  def: {
    fontSize: 15,
    fontWeight: "500",
    color: colors.versoText,
    lineHeight: 23,
    textAlign: "left",
    width: "100%",
  },
  empty: {
    color: colors.muted,
    fontStyle: "italic",
    textAlign: "center",
  },
});
