"use client";

import { useState } from "react";
import { SectionHeader } from "@/components/SectionHeader";
import { KpiCard } from "@/components/KpiCard";
import { UploadCard } from "@/components/UploadCard";
import { theme } from "@/lib/theme";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const FIRMA_ID = 1; // MVP: single-firma, selectable in future

interface Analyse {
  total_verdi: number;
  dod_lager_verdi: number;
  dod_lager_antall: number;
  dod_lager_poster: LagerPost[];
  lav_beholdning: LagerPost[];
  overlager: LagerPost[];
  totalt_antall_poster: number;
}

interface LagerPost {
  artikkelnummer: string;
  beskrivelse: string;
  antall: number;
  verdi?: number;
  abc_kategori?: string;
  dager_siden_bevegelse?: number;
}

function formatNOK(val: number): string {
  return val.toLocaleString("nb-NO", { maximumFractionDigits: 0 }) + " kr";
}

const abcColors: Record<string, string> = {
  A: theme.avvik,
  B: theme.warn,
  C: theme.muted,
};

export default function LagerinnsiktPage() {
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
      const res = await fetch(`${API}/firma/${FIRMA_ID}/lager/last-opp`, { method: "POST", body: fd });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Opplasting feilet");
      }
      // Fetch full analysis
      const a = await fetch(`${API}/firma/${FIRMA_ID}/lager/analyse`);
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
      const res = await fetch(`${API}/firma/${FIRMA_ID}/lager/sporsmal`, {
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
        eyebrow="LAGERINNSIKT"
        title="Lageranalyse"
        subtitle="Last opp lagerliste fra ditt ERP-system for å få umiddelbar analyse"
      />

      <UploadCard
        label="Last opp lagerliste (Excel/CSV)"
        onUpload={handleUpload}
        loading={uploading}
      />

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
          {/* KPI row */}
          <div style={{ display: "flex", gap: "16px", margin: "32px 0", flexWrap: "wrap" }}>
            <KpiCard
              label="Total lagerverdi"
              value={formatNOK(analyse.total_verdi)}
              status="neutral"
            />
            <KpiCard
              label="Dødt lager (verdi)"
              value={formatNOK(analyse.dod_lager_verdi)}
              status={analyse.dod_lager_verdi > 0 ? "avvik" : "ok"}
              sublabel={`${analyse.dod_lager_antall} poster`}
            />
            <KpiCard
              label="Under min.nivå"
              value={String(analyse.lav_beholdning.length)}
              status={analyse.lav_beholdning.length > 0 ? "warn" : "ok"}
              sublabel="artikler"
            />
            <KpiCard
              label="Over maks.nivå"
              value={String(analyse.overlager.length)}
              status={analyse.overlager.length > 0 ? "warn" : "ok"}
              sublabel="artikler"
            />
          </div>

          {/* Dead stock table */}
          {analyse.dod_lager_poster.length > 0 && (
            <div style={{ marginBottom: "40px" }}>
              <h2
                style={{
                  fontFamily: theme.fontSans,
                  fontSize: "18px",
                  fontWeight: 700,
                  color: theme.navy,
                  margin: "0 0 16px 0",
                }}
              >
                Dødt lager — ingen bevegelse siste 12 måneder
              </h2>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: theme.fontSans, fontSize: "14px" }}>
                  <thead>
                    <tr style={{ background: theme.bg }}>
                      {["Artikkelnr", "Beskrivelse", "Antall", "Verdi", "Dager siden", "ABC"].map((h) => (
                        <th
                          key={h}
                          style={{
                            textAlign: "left",
                            padding: "10px 14px",
                            color: theme.muted,
                            fontWeight: 600,
                            fontSize: "12px",
                            borderBottom: `1px solid ${theme.line}`,
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {analyse.dod_lager_poster.map((p, i) => (
                      <tr
                        key={i}
                        style={{ borderBottom: `1px solid ${theme.line}`, background: i % 2 ? theme.bg : theme.card }}
                      >
                        <td style={{ padding: "10px 14px", color: theme.navy, fontWeight: 600 }}>
                          {p.artikkelnummer}
                        </td>
                        <td style={{ padding: "10px 14px", color: theme.ink }}>{p.beskrivelse}</td>
                        <td style={{ padding: "10px 14px", color: theme.ink }}>{p.antall}</td>
                        <td style={{ padding: "10px 14px", color: theme.ink }}>
                          {p.verdi ? formatNOK(p.verdi) : "—"}
                        </td>
                        <td style={{ padding: "10px 14px", color: theme.avvik }}>
                          {p.dager_siden_bevegelse ?? "—"}
                        </td>
                        <td style={{ padding: "10px 14px" }}>
                          {p.abc_kategori && (
                            <span
                              style={{
                                background: abcColors[p.abc_kategori] + "20",
                                color: abcColors[p.abc_kategori],
                                borderRadius: theme.radiusPill,
                                padding: "2px 10px",
                                fontWeight: 700,
                                fontSize: "12px",
                              }}
                            >
                              {p.abc_kategori}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Chat */}
          <div
            style={{
              background: theme.card,
              borderRadius: theme.radiusCard,
              border: `1.5px solid ${theme.line}`,
              padding: "28px 24px",
            }}
          >
            <h2
              style={{
                fontFamily: theme.fontSans,
                fontSize: "18px",
                fontWeight: 700,
                color: theme.navy,
                margin: "0 0 16px 0",
              }}
            >
              Spør om lageret ditt
            </h2>
            <div style={{ display: "flex", gap: "12px" }}>
              <input
                value={sporsmal}
                onChange={(e) => setSporsmal(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSporsmal()}
                placeholder="F.eks. «Hva er verdien av dødt lager?»"
                style={{
                  flex: 1,
                  fontFamily: theme.fontSans,
                  fontSize: "14px",
                  border: `1.5px solid ${theme.line}`,
                  borderRadius: "8px",
                  padding: "10px 14px",
                  outline: "none",
                  color: theme.ink,
                }}
              />
              <button
                onClick={handleSporsmal}
                disabled={asking}
                style={{
                  background: theme.navy,
                  color: "#fff",
                  border: "none",
                  borderRadius: theme.radiusPill,
                  padding: "10px 22px",
                  fontFamily: theme.fontSans,
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: asking ? "wait" : "pointer",
                }}
              >
                {asking ? "…" : "Spør"}
              </button>
            </div>
            {svar && (
              <div
                style={{
                  marginTop: "20px",
                  background: theme.bg,
                  borderRadius: "8px",
                  padding: "16px 18px",
                  fontFamily: theme.fontSans,
                  fontSize: "14px",
                  color: theme.ink,
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                }}
              >
                {svar}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
