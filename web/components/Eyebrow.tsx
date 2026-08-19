import { theme } from "@/lib/theme";

interface EyebrowProps {
  text: string;
}

export function Eyebrow({ text }: EyebrowProps) {
  return (
    <p
      style={{
        fontFamily: theme.fontSans,
        fontSize: "11px",
        fontWeight: 700,
        letterSpacing: "0.12em",
        color: theme.gold,
        textTransform: "uppercase",
        margin: "0 0 8px 0",
      }}
    >
      {text}
    </p>
  );
}
