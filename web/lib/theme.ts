// Design tokens — identical across all Driftsagent modules
// Single source of truth — no module defines its own colours
export const theme = {
  navy: "#1F3A5F",
  navyDeep: "#152A47",
  gold: "#B08D2E",
  goldSoft: "#D9C079",
  ink: "#1A2230",
  muted: "#5C6B7F",
  line: "#E3E8EF",
  bg: "#F4F6F9",
  card: "#FFFFFF",
  ok: "#2E7D32",
  okBg: "#EAF4EC",
  warn: "#B8860B",
  warnBg: "#FBF7EC",
  avvik: "#C0392B",
  avvikBg: "#FBEAEA",
  radiusCard: "12px",
  radiusPill: "20px",
  fontSans: "-apple-system, 'Segoe UI', Roboto, sans-serif",
  fontSerif: "Georgia, 'Times New Roman', serif",
} as const;

export type Theme = typeof theme;
