import { theme } from "@/lib/theme";

type KpiStatus = "ok" | "warn" | "avvik" | "neutral";

interface KpiCardProps {
  label: string;
  value: string;
  status?: KpiStatus;
  sublabel?: string;
}

const statusColors: Record<KpiStatus, { bg: string; border: string; text: string }> = {
  ok: { bg: theme.okBg, border: theme.ok, text: theme.ok },
  warn: { bg: theme.warnBg, border: theme.warn, text: theme.warn },
  avvik: { bg: theme.avvikBg, border: theme.avvik, text: theme.avvik },
  neutral: { bg: theme.card, border: theme.line, text: theme.navy },
};

export function KpiCard({ label, value, status = "neutral", sublabel }: KpiCardProps) {
  const colors = statusColors[status];
  return (
    <div
      style={{
        background: colors.bg,
        border: `1.5px solid ${colors.border}`,
        borderRadius: theme.radiusCard,
        padding: "20px 24px",
        minWidth: "160px",
        flex: 1,
      }}
    >
      <p
        style={{
          fontFamily: theme.fontSans,
          fontSize: "12px",
          color: theme.muted,
          margin: "0 0 8px 0",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          fontWeight: 600,
        }}
      >
        {label}
      </p>
      <p
        style={{
          fontFamily: theme.fontSans,
          fontSize: "26px",
          fontWeight: 700,
          color: colors.text,
          margin: "0 0 4px 0",
        }}
      >
        {value}
      </p>
      {sublabel && (
        <p style={{ fontFamily: theme.fontSans, fontSize: "12px", color: theme.muted, margin: 0 }}>
          {sublabel}
        </p>
      )}
    </div>
  );
}
