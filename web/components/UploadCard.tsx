"use client";

import { useRef, useState } from "react";
import { theme } from "@/lib/theme";

interface UploadCardProps {
  label: string;
  accept?: string;
  onUpload: (file: File) => Promise<void>;
  loading?: boolean;
}

export function UploadCard({ label, accept = ".xlsx,.xls,.csv", onUpload, loading }: UploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = async (file: File) => {
    await onUpload(file);
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      style={{
        border: `2px dashed ${dragOver ? theme.gold : theme.line}`,
        borderRadius: theme.radiusCard,
        background: dragOver ? theme.warnBg : theme.card,
        padding: "40px 32px",
        textAlign: "center",
        cursor: loading ? "wait" : "pointer",
        transition: "all 0.15s",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      <div style={{ fontSize: "32px", marginBottom: "12px" }}>📂</div>
      <p
        style={{
          fontFamily: theme.fontSans,
          fontSize: "15px",
          color: theme.navy,
          fontWeight: 600,
          margin: "0 0 6px 0",
        }}
      >
        {loading ? "Laster opp…" : label}
      </p>
      <p style={{ fontFamily: theme.fontSans, fontSize: "13px", color: theme.muted, margin: 0 }}>
        Excel (.xlsx) eller CSV — dra og slipp eller klikk
      </p>
    </div>
  );
}
