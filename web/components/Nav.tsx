"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { theme } from "@/lib/theme";

const navItems = [
  { href: "/", label: "Hjem" },
  { href: "/firma", label: "Min bedrift" },
  { href: "/lagerinnsikt", label: "Lagerinnsikt" },
  { href: "/serviceinnsikt", label: "Serviceinnsikt" },
  { href: "/driftsagent", label: "Driftsagent" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        background: theme.navyDeep,
        padding: "0 32px",
        display: "flex",
        alignItems: "center",
        gap: "8px",
        height: "56px",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <Link
        href="/"
        style={{
          fontFamily: theme.fontSans,
          fontSize: "15px",
          fontWeight: 700,
          color: theme.goldSoft,
          textDecoration: "none",
          marginRight: "24px",
          letterSpacing: "0.04em",
        }}
      >
        DRIFTSAGENT
      </Link>
      {navItems.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            style={{
              fontFamily: theme.fontSans,
              fontSize: "14px",
              color: active ? theme.goldSoft : "rgba(255,255,255,0.6)",
              textDecoration: "none",
              padding: "8px 14px",
              borderRadius: theme.radiusPill,
              background: active ? "rgba(176,141,46,0.15)" : "transparent",
              fontWeight: active ? 600 : 400,
              transition: "all 0.15s",
            }}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
