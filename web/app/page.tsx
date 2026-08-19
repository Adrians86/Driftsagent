import Link from "next/link";
import { SectionHeader } from "@/components/SectionHeader";
import { KpiCard } from "@/components/KpiCard";
import { theme } from "@/lib/theme";

const moduler = [
  {
    href: "/lagerinnsikt",
    tittel: "Lagerinnsikt",
    beskrivelse: "Analyser lagerbeholdning, identifiser dødt lager og ABC-klassifisering.",
    aktiv: true,
    ikon: "📦",
  },
  {
    href: "/innkjopsinnsikt",
    tittel: "Innkjøpsinnsikt",
    beskrivelse: "Overvåk leverandørytelse og innkjøpsordrer.",
    aktiv: false,
    ikon: "🛒",
  },
  {
    href: "/serviceinnsikt",
    tittel: "Serviceinnsikt",
    beskrivelse: "Spor serviceordrer, nedetid og gjentakende feil.",
    aktiv: true,
    ikon: "🔧",
  },
  {
    href: "/produksjonsinnsikt",
    tittel: "Produksjonsinnsikt",
    beskrivelse: "Overvåk produksjonslinjer og kapasitetsutnyttelse.",
    aktiv: false,
    ikon: "🏭",
  },
];

export default function HjemPage() {
  return (
    <div>
      <SectionHeader
        eyebrow="DRIFTSAGENT"
        title="Agenter for drift"
        subtitle="Lager, innkjøp, service og produksjon — samlet oversikt med AI-analyse"
      />

      {/* KPI row */}
      <div style={{ display: "flex", gap: "16px", marginBottom: "48px", flexWrap: "wrap" }}>
        <KpiCard label="Aktive moduler" value="2" status="ok" sublabel="av 4 i MVP" />
        <KpiCard label="Sist oppdatert" value="2026-08-19" status="neutral" />
      </div>

      {/* Module cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: "20px",
        }}
      >
        {moduler.map((m) => (
          <div
            key={m.href}
            style={{
              background: theme.card,
              borderRadius: theme.radiusCard,
              border: `1.5px solid ${m.aktiv ? theme.line : theme.line}`,
              padding: "28px 24px",
              opacity: m.aktiv ? 1 : 0.55,
              transition: "box-shadow 0.15s",
            }}
          >
            <div style={{ fontSize: "28px", marginBottom: "12px" }}>{m.ikon}</div>
            <h2
              style={{
                fontFamily: theme.fontSans,
                fontSize: "18px",
                fontWeight: 700,
                color: theme.navy,
                margin: "0 0 8px 0",
              }}
            >
              {m.tittel}
            </h2>
            <p
              style={{
                fontFamily: theme.fontSans,
                fontSize: "14px",
                color: theme.muted,
                margin: "0 0 20px 0",
                lineHeight: 1.5,
              }}
            >
              {m.beskrivelse}
            </p>
            {m.aktiv ? (
              <Link
                href={m.href}
                style={{
                  display: "inline-block",
                  background: theme.navy,
                  color: "#fff",
                  padding: "8px 18px",
                  borderRadius: theme.radiusPill,
                  textDecoration: "none",
                  fontFamily: theme.fontSans,
                  fontSize: "13px",
                  fontWeight: 600,
                }}
              >
                Åpne modul →
              </Link>
            ) : (
              <span
                style={{
                  display: "inline-block",
                  background: theme.line,
                  color: theme.muted,
                  padding: "8px 18px",
                  borderRadius: theme.radiusPill,
                  fontFamily: theme.fontSans,
                  fontSize: "13px",
                  fontWeight: 600,
                }}
              >
                Kommer snart
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
