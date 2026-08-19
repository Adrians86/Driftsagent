"use client";

import { useState } from "react";
import { SectionHeader } from "@/components/SectionHeader";
import { theme } from "@/lib/theme";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FirmaData {
  navn: string;
  org_nr: string;
  bransje: string;
  antall_ansatte: string;
  erp_system: string;
}

const defaultForm: FirmaData = {
  navn: "",
  org_nr: "",
  bransje: "",
  antall_ansatte: "",
  erp_system: "",
};

export default function FirmaPage() {
  const [form, setForm] = useState<FirmaData>(defaultForm);
  const [lagret, setLagret] = useState(false);
  const [feil, setFeil] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setFeil(null);
    try {
      const res = await fetch(`${API}/firma/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          navn: form.navn,
          org_nr: form.org_nr || null,
          bransje: form.bransje || null,
          antall_ansatte: form.antall_ansatte ? parseInt(form.antall_ansatte) : null,
          erp_system: form.erp_system || null,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setLagret(true);
    } catch (err: unknown) {
      setFeil(err instanceof Error ? err.message : "Noe gikk galt");
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    fontFamily: theme.fontSans,
    fontSize: "14px",
    border: `1.5px solid ${theme.line}`,
    borderRadius: "8px",
    padding: "10px 14px",
    width: "100%",
    color: theme.ink,
    background: theme.card,
    outline: "none",
    boxSizing: "border-box",
  };

  return (
    <div style={{ maxWidth: "540px" }}>
      <SectionHeader
        eyebrow="MIN BEDRIFT"
        title="Firmaprofil"
        subtitle="Registrer bedriftsinformasjon for å komme i gang"
      />

      {lagret && (
        <div
          style={{
            background: theme.okBg,
            border: `1.5px solid ${theme.ok}`,
            borderRadius: theme.radiusCard,
            padding: "14px 20px",
            marginBottom: "24px",
            fontFamily: theme.fontSans,
            fontSize: "14px",
            color: theme.ok,
          }}
        >
          Bedriften er registrert.
        </div>
      )}

      {feil && (
        <div
          style={{
            background: theme.avvikBg,
            border: `1.5px solid ${theme.avvik}`,
            borderRadius: theme.radiusCard,
            padding: "14px 20px",
            marginBottom: "24px",
            fontFamily: theme.fontSans,
            fontSize: "14px",
            color: theme.avvik,
          }}
        >
          {feil}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {[
          { key: "navn" as const, label: "Bedriftsnavn *", required: true },
          { key: "org_nr" as const, label: "Organisasjonsnummer" },
          { key: "bransje" as const, label: "Bransje" },
          { key: "antall_ansatte" as const, label: "Antall ansatte", type: "number" },
          { key: "erp_system" as const, label: "ERP-system (f.eks. Visma, 24SevenOffice)" },
        ].map(({ key, label, required, type }) => (
          <div key={key}>
            <label
              style={{
                display: "block",
                fontFamily: theme.fontSans,
                fontSize: "13px",
                fontWeight: 600,
                color: theme.navy,
                marginBottom: "6px",
              }}
            >
              {label}
            </label>
            <input
              type={type || "text"}
              value={form[key]}
              onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
              required={required}
              style={inputStyle}
            />
          </div>
        ))}

        <button
          type="submit"
          disabled={loading}
          style={{
            background: theme.navy,
            color: "#fff",
            border: "none",
            borderRadius: theme.radiusPill,
            padding: "12px 28px",
            fontFamily: theme.fontSans,
            fontSize: "14px",
            fontWeight: 600,
            cursor: loading ? "wait" : "pointer",
            alignSelf: "flex-start",
            marginTop: "8px",
          }}
        >
          {loading ? "Lagrer…" : "Lagre bedrift"}
        </button>
      </form>
    </div>
  );
}
