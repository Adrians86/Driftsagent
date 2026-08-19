"use client";

import { useState } from "react";
import { SectionHeader } from "@/components/SectionHeader";
import { KpiCard } from "@/components/KpiCard";
import { UploadCard } from "@/components/UploadCard";
import { theme } from "@/lib/theme";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const FIRMA_ID = 1;

interface Analyse {
  totalt_antall_ordre: number;
  antall_forsinkede: number;
  forsinkede_ordre: ServiceOrdre[];
  hyppigst_service: { utstyr_id: string; antall_ordre: number }[];
  total_nedetid_timer: number;
  nedetid_per_maned: Record<string, number>;
  gjentakende_feil: { utstyr_id: string; feilbeskrivelse: string; antall_gjentakelser: number }[];
}

interface ServiceOrdre {
  ordre_nummer: string;
  utstyr_id: string;
  opprettet: string;
  status: string;
  dager_forsinket?: number;
  feilbeskrivelse?: string;
}

export default function ServiceinnsiktPage() {
  const [analyse, setAnalyse] = useState<Analyse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [feil, setFeil] = useState<string | null>(null);
  const [sporsmal, setSporsmal] = useState("");
  const [svar, setSvar] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);

  const handleUpload = async (fil: File) => {
    setUploading(true);
    setFeil(null);
    try {
      const fd = new FormData();
      fd.append("fil", fil);
      const res = await fetch(`${API}/firma/${FIRMA_ID}/service/last-opp`, { method: "POST", body: fd });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Opplasting feilet");
      }
      const a = await fetch(`${API}/firma/${FIRMA_ID}/service/analyse`);
      setAnalyse(await a.json());
    } catch (err: unknown) {
      setFeil(err instanceof Error ? err.message : "Noe gikk galt");
    } finally {
      setUploading(false);
    }
  };

  const handleSporsmal = async () => {
    if (!sporsmal.trim()) return;
    setAsking(true);
    setSvar(null);
    try {
      const res = await fetch(`${API}/firma/${FIRMA_ID}/service/sporsmal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sporsmal }),
      });
      const data = await res.json();
      setSvar(data.svar || data.detail);
    } catch {
      setSvar("Beklager, noe gikk galt.");
    } finally {
      setAsking(false);
    }
  };

  return (
    <div>
      <SectionHeader
        eyebrow="SERVICEINNSIKT"
        title="Serviceanalyse"
        subtitle="Last opp serviceordrer fra ditt ERP-system for analyse av forsinkelser og mønstre"
      />

      <UploadCard label="Last opp serviceordrer (Excel/CSV)" onUpload={handleUpload} loading={uploading} />

      {feil && (
        <div
          style={{
            background: theme.avvikBg,
            border: `1.5px solid ${theme.avvik}`,
            borderRadius: theme.radiusCard,
            padding: "14px 20px",
            margin: "20px 0",
            fontFamily: theme.fontSans,
            fontSize: "14px",
            color: theme.avvik,
          }}
        >
          {feil}
        </div>
      )}

      {analyse && (
        <>
          <div style={{ display: "flex", gap: "16px", margin: "32px 0", flexWrap: "wrap" }}>
            <KpiCard label="Totalt serviceordrer" value={String(analyse.totalt_antall_ordre)} status="neutral" />
            <KpiCard
              label="Forsinkede"
              value={String(analyse.antall_forsinkede)}
              status={analyse.antall_forsinkede > 0 ? "avvik" : "ok"}
            />
            <KpiCard
              label="Total nedetid"
              value={`${analyse.total_nedetid_timer.toFixed(1)} t`}
              status={analyse.total_nedetid_timer > 0 ? "warn" : "ok"}
            />
            <KpiCard
              label="Gjentakende feil"
              value={String(analyse.gjentakende_feil.length)}
              status={analyse.gjentakende_feil.length > 0 ? "warn" : "ok"}
            />
          </div>

          {analyse.forsinkede_ordre.length > 0 && (
            <div style={{ marginBottom: "40px" }}>
              <h2 style={{ fontFamily: theme.fontSans, fontSize: "18px", fontWeight: 700, color: theme.navy, margin: "0 0 16px 0" }}>
                Forsinkede serviceordrer
              </h2>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: theme.fontSans, fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: theme.bg }}>
                      {["Ordrenr", "Utstyr", "Opprettet", "Status", "Dager forsinket", "Feil"].map((h) => (
                        <th key={h} style={{ textAlign: "left", padding: "10px 14px", color: theme.muted, fontWeight: 600, fontSize: "12px", borderBottom: `1px solid ${theme.line}` }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {analyse.forsinkede_ordre.map((o, i) => (
                      <tr key={i} style={{ borderBottom: `1px solid ${theme.line}`, background: i % 2 ? theme.bg : theme.card }}>
                        <td style={{ padding: "10px 14px", color: theme.navy, fontWeight: 600 }}>{o.ordre_nummer}</td>
                        <td style={{ padding: "10px 14px" }}>{o.utstyr_id}</td>
                        <td style={{ padding: "10px 14px" }}>{o.opprettet}</td>
                        <td style={{ padding: "10px 14px" }}>{o.status}</td>
                        <td style={{ padding: "10px 14px", color: theme.avvik, fontWeight: 600 }}>{o.dager_forsinket ?? "—"}</td>
                        <td style={{ padding: "10px 14px", color: theme.muted }}>{o.feilbeskrivelse ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Chat */}
          <div style={{ background: theme.card, borderRadius: theme.radiusCard, border: `1.5px solid ${theme.line}`, padding: "28px 24px" }}>
            <h2 style={{ fontFamily: theme.fontSans, fontSize: "18px", fontWeight: 700, color: theme.navy, margin: "0 0 16px 0" }}>
              Spør om service
            </h2>
            <div style={{ display: "flex", gap: "12px" }}>
              <input
                value={sporsmal}
                onChange={(e) => setSporsmal(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSporsmal()}
                placeholder="F.eks. «Hvilke maskiner har flest forsinkede ordrer?»"
                style={{ flex: 1, fontFamily: theme.fontSans, fontSize: "14px", border: `1.5px solid ${theme.line}`, borderRadius: "8px", padding: "10px 14px", outline: "none", color: theme.ink }}
              />
              <button
                onClick={handleSporsmal}
                disabled={asking}
                style={{ background: theme.navy, color: "#fff", border: "none", borderRadius: theme.radiusPill, padding: "10px 22px", fontFamily: theme.fontSans, fontSize: "14px", fontWeight: 600, cursor: asking ? "wait" : "pointer" }}
              >
                {asking ? "…" : "Spør"}
              </button>
            </div>
            {svar && (
              <div style={{ marginTop: "20px", background: theme.bg, borderRadius: "8px", padding: "16px 18px", fontFamily: theme.fontSans, fontSize: "14px", color: theme.ink, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                {svar}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
