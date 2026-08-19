import { theme } from "@/lib/theme";
import { Eyebrow } from "./Eyebrow";

interface SectionHeaderProps {
  eyebrow: string;
  title: string;
  subtitle?: string;
}

export function SectionHeader({ eyebrow, title, subtitle }: SectionHeaderProps) {
  return (
    <div style={{ marginBottom: "32px" }}>
      <Eyebrow text={eyebrow} />
      <h1
        style={{
          fontFamily: theme.fontSans,
          fontSize: "28px",
          fontWeight: 700,
          color: theme.navy,
          margin: "0 0 8px 0",
        }}
      >
        {title}
      </h1>
      {subtitle && (
        <p
          style={{
            fontFamily: theme.fontSans,
            fontSize: "16px",
            color: theme.muted,
            margin: 0,
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}
