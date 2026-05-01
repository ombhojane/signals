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
    <section className="rounded-3xl p-8 flex flex-col gap-6 bg-card border border-border">
      <div className="flex items-start gap-4">
        <div className="h-10 w-10 rounded-full flex items-center justify-center shrink-0 bg-primary/10 border border-primary/20">
          <span className="material-symbols-outlined text-primary" style={{ fontSize: "1.1rem" }}>
            {icon}
          </span>
        </div>
        <div>
          <h3 className="text-sm font-bold tracking-[0.2em] uppercase text-foreground">
            {title}
          </h3>
          <p className="text-xs mt-1 text-muted-foreground">
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
  const valueClass = `text-sm ${mono ? "font-mono" : ""} ${href ? "text-primary" : "text-foreground"}`;

  const content = (
    <span className={valueClass}>
      {value}
    </span>
  );

  return (
    <div className="flex items-center justify-between py-3 border-b border-border/50">
      <span className="text-[10px] tracking-[0.2em] uppercase text-muted-foreground">
        {label}
      </span>
      {href ? (
        <a href={href} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 hover:underline">
          {content}
          <span className="material-symbols-outlined text-primary" style={{ fontSize: "0.9rem" }}>
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
        <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-muted-foreground">
          Preferences
        </span>
        <h1 className="text-5xl font-black tracking-[-0.03em] mt-2 text-foreground">
          Settings
        </h1>
        <p className="mt-3 text-sm max-w-xl text-muted-foreground">
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
                className={`flex-1 rounded-2xl p-4 flex flex-col items-center gap-2 transition-colors border ${
                  active
                    ? "bg-accent border-primary/40"
                    : "bg-background border-border hover:bg-accent/50"
                }`}
              >
                <Icon className={`size-4 ${active ? "text-primary" : "text-muted-foreground"}`} />
                <span className={`text-[10px] tracking-widest uppercase font-bold ${active ? "text-primary" : "text-muted-foreground"}`}>
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
          <div className="rounded-2xl p-6 text-center bg-background border border-dashed border-border">
            <p className="text-sm text-muted-foreground">No wallet connected</p>
          </div>
        ) : (
          <div>
            <InfoRow label="Address" value={shortAddr(address)} mono />
            <InfoRow
              label="Network"
              value={chainMatch ? CHAIN.name : `Wrong chain (${chainId})`}
            />
            {!chainMatch && (
              <p className="mt-2 text-xs text-destructive">
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
