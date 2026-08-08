import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { colors, notionTone } from "../theme/colors";

type Props = {
  label: string;
  selected: boolean;
  disabled?: boolean;
  /** Nom de couleur Notion (blue, orange, …). */
  colorName?: string;
  onPress: () => void;
};

export function Chip({
  label,
  selected,
  disabled,
  colorName = "default",
  onPress,
}: Props) {
  const tone = notionTone(colorName);
  const locked = disabled && !selected;

  return (
    <Pressable
      onPress={onPress}
      disabled={locked}
      style={[
        styles.chip,
        { borderColor: tone.border },
        selected && {
          backgroundColor: tone.vivid,
          borderColor: tone.vivid,
        },
        locked && styles.disabled,
      ]}
    >
      <Text
        style={[
          styles.label,
          selected && styles.labelSelected,
          locked && styles.labelDisabled,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    borderWidth: 2,
    backgroundColor: "#fff",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  disabled: {
    opacity: 0.28,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.muted,
  },
  labelSelected: { color: "#fff" },
  labelDisabled: { color: colors.muted },
});
