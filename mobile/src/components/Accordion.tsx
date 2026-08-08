import React, { useEffect, useState } from "react";
import {
  LayoutAnimation,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  UIManager,
  View,
} from "react-native";
import { colors } from "../theme/colors";

if (
  Platform.OS === "android" &&
  UIManager.setLayoutAnimationEnabledExperimental
) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

type Props = {
  title: string;
  onClear: () => void;
  children: React.ReactNode;
  initiallyOpen?: boolean;
};

export function Accordion({
  title,
  onClear,
  children,
  initiallyOpen = false,
}: Props) {
  const [open, setOpen] = useState(initiallyOpen);

  useEffect(() => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
  }, [open]);

  return (
    <View style={styles.wrap}>
      <View style={styles.row}>
        <Pressable
          onPress={() => setOpen((v) => !v)}
          style={styles.toggle}
          accessibilityRole="button"
          accessibilityState={{ expanded: open }}
        >
          <Text style={[styles.chevron, open && styles.chevronOpen]}>▾</Text>
          <Text style={styles.title}>{title}</Text>
        </Pressable>
        <Pressable onPress={onClear} hitSlop={8}>
          <Text style={styles.clear}>Effacer la sélection</Text>
        </Pressable>
      </View>
      {open ? <View style={styles.body}>{children}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: 48,
    gap: 10,
  },
  toggle: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    flexShrink: 1,
  },
  chevron: {
    fontSize: 14,
    color: colors.ink,
    width: 16,
    transform: [{ rotate: "-90deg" }],
  },
  chevronOpen: {
    transform: [{ rotate: "0deg" }],
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.ink,
  },
  clear: {
    marginLeft: "auto",
    color: colors.clear,
    fontSize: 13,
    fontWeight: "500",
  },
  body: {
    paddingLeft: 24,
    paddingBottom: 14,
  },
});
