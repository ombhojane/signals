"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useAccount, useChainId } from "wagmi";
import { Moon, Sun, Monitor } from "lucide-react";
import { CHAIN, VAULT_ADDRESS, USDC_ADDRESS, explorerAddress } from "@/lib/web3/constants";

function shortAddr(addr?: string): string {
  if (!addr) return "—";
  return `${addr.slice(0, 8)}…${addr.slice(-6)}`;
}

function SettingsSection({
  title,
  description,
  icon,
  children,
}: {
  title: string;
  description: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className="rounded-3xl p-8 flex flex-col gap-6"
      style={{
        backgroundColor: "#131313",
        border: "1px solid rgba(72,72,72,0.25)",
      }}
    >
      <div className="flex items-start gap-4">
        <div
          className="h-10 w-10 rounded-full flex items-center justify-center shrink-0"
          style={{
            backgroundColor: "rgba(167,203,235,0.1)",
            border: "1px solid rgba(167,203,235,0.2)",
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: "1.1rem", color: "#a7cbeb" }}
          >
            {icon}
          </span>
        </div>
        <div>
          <h3 className="text-sm font-bold tracking-[0.2em] uppercase" style={{ color: "#e7e5e5" }}>
            {title}
          </h3>
          <p className="text-xs mt-1" style={{ color: "#acabaa" }}>
            {description}
          </p>
        </div>
      </div>
      {children}
    </section>
  );
}

function InfoRow({
  label,
  value,
  mono = false,
  href,
}: {
  label: string;
  value: string;
  mono?: boolean;
  href?: string;
}) {
  const valueClass = `text-sm ${mono ? "font-mono" : ""}`;

  const content = (
    <span
      className={valueClass}
      style={{ color: href ? "#a7cbeb" : "#e7e5e5" }}
    >
      {value}
    </span>
  );

  return (
    <div
      className="flex items-center justify-between py-3"
      style={{ borderBottom: "1px solid rgba(72,72,72,0.2)" }}
    >
      <span className="text-[10px] tracking-[0.2em] uppercase" style={{ color: "#acabaa" }}>
        {label}
      </span>
      {href ? (
        <a href={href} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 hover:underline">
          {content}
          <span className="material-symbols-outlined" style={{ fontSize: "0.9rem", color: "#a7cbeb" }}>
            open_in_new
          </span>
        </a>
      ) : (
        content
      )}
    </div>
  );
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { address, isConnected } = useAccount();
  const chainId = useChainId();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const chainMatch = chainId === CHAIN.id;

  return (
    <div className="flex flex-col gap-8 p-8 max-w-4xl">
      <div>
        <span
          className="text-[10px] font-bold tracking-[0.2em] uppercase"
          style={{ color: "#acabaa" }}
        >
          Preferences
        </span>
        <h1
          className="text-5xl font-black tracking-[-0.03em] mt-2"
          style={{ color: "#e7e5e5" }}
        >
          Settings
        </h1>
        <p className="mt-3 text-sm max-w-xl" style={{ color: "#acabaa" }}>
          Appearance, wallet info, and vault contract details.
        </p>
      </div>

      {/* Appearance */}
      <SettingsSection
        title="Appearance"
        description="Dark mode is the default and looks best. Light mode is experimental."
        icon="palette"
      >
        <div className="flex gap-2">
          {[
            { id: "light", label: "Light", icon: Sun },
            { id: "system", label: "System", icon: Monitor },
            { id: "dark", label: "Dark", icon: Moon },
          ].map(({ id, label, icon: Icon }) => {
            const active = mounted && theme === id;
            return (
              <button
                key={id}
                onClick={() => setTheme(id)}
                className="flex-1 rounded-2xl p-4 flex flex-col items-center gap-2 transition-colors"
                style={{
                  backgroundColor: active ? "#252626" : "#0e0e0e",
                  border: `1px solid ${active ? "rgba(167,203,235,0.4)" : "rgba(72,72,72,0.25)"}`,
                }}
              >
                <Icon className="size-4" style={{ color: active ? "#a7cbeb" : "#acabaa" }} />
                <span
                  className="text-[10px] tracking-widest uppercase font-bold"
                  style={{ color: active ? "#a7cbeb" : "#acabaa" }}
                >
                  {label}
                </span>
              </button>
            );
          })}
        </div>
      </SettingsSection>

      {/* Wallet */}
      <SettingsSection
        title="Connected Wallet"
        description="Your active session. Manage it from the sidebar Connect Wallet button."
        icon="account_balance_wallet"
      >
        {!isConnected ? (
          <div
            className="rounded-2xl p-6 text-center"
            style={{
              backgroundColor: "#0e0e0e",
              border: "1px dashed rgba(72,72,72,0.3)",
            }}
          >
            <p className="text-sm" style={{ color: "#acabaa" }}>
              No wallet connected
            </p>
          </div>
        ) : (
          <div>
            <InfoRow label="Address" value={shortAddr(address)} mono />
            <InfoRow
              label="Network"
              value={chainMatch ? CHAIN.name : `Wrong chain (${chainId})`}
            />
            {!chainMatch && (
              <p className="mt-2 text-xs" style={{ color: "#ee7d77" }}>
                Switch to {CHAIN.name} using the sidebar button.
              </p>
            )}
          </div>
        )}
      </SettingsSection>

      {/* Vault */}
      <SettingsSection
        title="Vault Contract"
        description="Public addresses used by this interface. All verifiable on-chain."
        icon="savings"
      >
        <div>
          <InfoRow
            label="Vault Address"
            value={shortAddr(VAULT_ADDRESS)}
            mono
            href={explorerAddress(VAULT_ADDRESS)}
          />
          <InfoRow
            label="Asset"
            value="USDC"
            href={explorerAddress(USDC_ADDRESS)}
          />
          <InfoRow label="Network" value={CHAIN.name} />
          <InfoRow label="Chain ID" value={String(CHAIN.id)} mono />
        </div>
      </SettingsSection>
    </div>
  );
}
