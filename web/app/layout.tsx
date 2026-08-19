import type { Metadata } from "next";
import { Nav } from "@/components/Nav";
import { theme } from "@/lib/theme";

export const metadata: Metadata = {
  title: "Driftsagent",
  description: "AI-agentplattform for norske SMB — lager, innkjøp, service og produksjon",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nb">
      <body
        style={{
          margin: 0,
          padding: 0,
          fontFamily: theme.fontSans,
          background: theme.bg,
          color: theme.ink,
          minHeight: "100vh",
        }}
      >
        <Nav />
        <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "40px 32px" }}>
          {children}
        </main>
      </body>
    </html>
  );
}
