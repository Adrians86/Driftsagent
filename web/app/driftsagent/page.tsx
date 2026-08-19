"use client";

import { useState } from "react";
import { SectionHeader } from "@/components/SectionHeader";
import { theme } from "@/lib/theme";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const FIRMA_ID = 1;

export default function DriftsagentPage() {
  const [sporsmal, setSporsmal] = useState("");
  const [svar, setSvar] = useState<string | null>(null);
  const [moduler, setModuler] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [feil, setFeil] = useState<string | null>(null);

  const handleSporsmal = async () => {
    if (!sporsmal.trim()) return;
    setAsking(true);
    setSvar(null);
    setFeil(null);
    setModuler(null);
    try {
      const res = await fetch(`${API}/firma/${FIRMA_ID}/driftsagent/sporsmal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sporsmal, moduler: ["lagerinnsikt", "serviceinnsikt"] }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Noe gikk galt");
      setSvar(data.svar);
      setModuler(data.involverte_moduler?.join(", ") ?? null);
    } catch (err: unknown) {
      setFeil(err instanceof Error ? err.message : "Noe gikk galt");
    } finally {
      setAsking(false);
    }
  };

  return (
    <div style={{ maxWidth: "720px" }}>
      <SectionHeader
        eyebrow="DRIFTSAGENT — SAMLET OVERSIKT"
        title="Tverrfaglig analyse"
        subtitle="Still spørsmål som krever data fra flere moduler — lager og service analyseres sammen"
      />

      <div style={{ background: theme.card, borderRadius: theme.radiusCard, border: `1.5px solid ${theme.line}`, padding: "32px 28px" }}>
        <p style={{ fontFamily: theme.fontSans, fontSize: "14px", color: theme.muted, margin: "0 0 20px 0" }}>
          Eksempel: «Hvorfor stoppet linjen i forrige uke?» eller «Hvilke maskiner har både serviceproblemer og manglende reservedeler?»
        </p>
        <div style={{ display: "flex", gap: "12px" }}>
          <input
            value={sporsmal}
            onChange={(e) => setSporsmal(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSporsmal()}
            placeholder="Still et tverrfaglig spørsmål…"
            style={{ flex: 1, fontFamily: theme.fontSans, fontSize: "14px", border: `1.5px solid ${theme.line}`, borderRadius: "8px", padding: "12px 16px", outline: "none", color: theme.ink }}
          />
          <button
            onClick={handleSporsmal}
            disabled={asking}
            style={{ background: theme.navy, color: "#fff", border: "none", borderRadius: theme.radiusPill, padding: "12px 24px", fontFamily: theme.fontSans, fontSize: "14px", fontWeight: 600, cursor: asking ? "wait" : "pointer" }}
          >
            {asking ? "Analyserer…" : "Analyser"}
          </button>
        </div>

        {feil && (
          <div style={{ marginTop: "20px", background: theme.avvikBg, border: `1.5px solid ${theme.avvik}`, borderRadius: "8px", padding: "14px 18px", fontFamily: theme.fontSans, fontSize: "14px", color: theme.avvik }}>
            {feil}
          </div>
        )}

        {svar && (
          <>
            {moduler && (
              <p style={{ fontFamily: theme.fontSans, fontSize: "12px", color: theme.muted, margin: "20px 0 8px 0" }}>
                Brukte moduler: <strong>{moduler}</strong>
              </p>
            )}
            <div style={{ background: theme.bg, borderRadius: "8px", padding: "18px 20px", fontFamily: theme.fontSans, fontSize: "14px", color: theme.ink, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
              {svar}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
