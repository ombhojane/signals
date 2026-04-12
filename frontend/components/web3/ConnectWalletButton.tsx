"use client";

import { useEffect, useRef, useState } from "react";
import { useAccount, useChainId, useConnect, useDisconnect, useSwitchChain } from "wagmi";
import { CHAIN, explorerAddress } from "@/lib/web3/constants";

function shortAddr(addr?: string): string {
  if (!addr) return "";
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}

function friendlyConnectError(err: Error | null): string | null {
  if (!err) return null;
  const msg = err.message;
  if (msg.includes("User rejected") || msg.includes("User denied")) {
    return "You cancelled the connection";
  }
  if (msg.toLowerCase().includes("no injected") || msg.toLowerCase().includes("no provider")) {
    return "No browser wallet detected — install MetaMask";
  }
  return msg.split("\n")[0].slice(0, 140);
}

export function ConnectWalletButton() {
  const { address, isConnected } = useAccount();
  const { connect, connectors, isPending, error, variables } = useConnect();
  const { disconnect } = useDisconnect();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();

  const [pickerOpen, setPickerOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const pickerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setPickerOpen(false);
      }
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (!mounted) {
    return (
      <div
        className="w-full rounded-full px-6 py-4 font-bold text-sm tracking-tight text-center"
        style={{ backgroundColor: "#a7cbeb", color: "#1e435e" }}
      >
        Connect Wallet
      </div>
    );
  }

  const errorMessage = friendlyConnectError(error);
  const wrongNetwork = isConnected && chainId !== CHAIN.id;

  // Only show connectors that don't need extra SDKs (injected only by default)
  const usableConnectors = connectors.filter(
    (c) => c.id.includes("injected") || c.id.includes("metaMask") || c.type === "injected"
  );
  const displayConnectors = usableConnectors.length > 0 ? usableConnectors : connectors;

  if (!isConnected) {
    return (
      <div ref={pickerRef} className="relative">
        <button
          onClick={() => {
            // Fast path: only one usable connector? connect directly
            if (displayConnectors.length === 1) {
              connect({ connector: displayConnectors[0] });
            } else {
              setPickerOpen((v) => !v);
            }
          }}
          disabled={isPending}
          className="w-full rounded-full px-6 py-4 font-bold text-sm tracking-tight active:scale-95 duration-300 transition-all disabled:opacity-60"
          style={{ backgroundColor: "#a7cbeb", color: "#1e435e" }}
        >
          {isPending ? "Connecting…" : "Connect Wallet"}
        </button>

        {errorMessage && !pickerOpen && (
          <p
            className="mt-2 text-[11px] leading-snug px-2 text-center"
            style={{ color: "#ee7d77" }}
          >
            {errorMessage}
          </p>
        )}

        {pickerOpen && displayConnectors.length > 1 && (
          <div
            className="absolute bottom-full left-0 right-0 mb-2 rounded-2xl p-2 flex flex-col gap-1 card-shadow"
            style={{
              backgroundColor: "#191a1a",
              border: "1px solid rgba(72,72,72,0.3)",
            }}
          >
            {displayConnectors.map((c) => {
              const pendingThis =
                isPending &&
                variables?.connector &&
                "id" in variables.connector &&
                variables.connector.id === c.id;
              return (
                <button
                  key={c.id}
                  onClick={() => {
                    connect({ connector: c });
                    setPickerOpen(false);
                  }}
                  disabled={isPending}
                  className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-left transition-colors hover:bg-[#252626] disabled:opacity-50"
                  style={{ color: "#e7e5e5" }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: "1.1rem", color: "#a7cbeb" }}>
                    extension
                  </span>
                  <span className="flex-1">{labelFor(c.id, c.name)}</span>
                  {pendingThis ? (
                    <span className="text-[10px] tracking-widest uppercase" style={{ color: "#acabaa" }}>
                      connecting…
                    </span>
                  ) : null}
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  if (wrongNetwork) {
    return (
      <button
        onClick={() => switchChain({ chainId: CHAIN.id })}
        className="w-full rounded-full px-6 py-4 font-bold text-sm tracking-tight active:scale-95 duration-300 transition-all"
        style={{ backgroundColor: "#ee7d77", color: "#2a0f0e" }}
      >
        Switch to Base Sepolia
      </button>
    );
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setMenuOpen((v) => !v)}
        className="w-full rounded-full px-6 py-4 flex items-center gap-3 transition-colors"
        style={{ backgroundColor: "#131313", border: "1px solid rgba(167,203,235,0.2)" }}
      >
        <span className="zen-pulse shrink-0" />
        <span className="flex-1 text-left">
          <span className="block text-xs tracking-widest uppercase" style={{ color: "#acabaa" }}>
            Connected
          </span>
          <span className="block text-sm font-mono tracking-tight" style={{ color: "#e7e5e5" }}>
            {shortAddr(address)}
          </span>
        </span>
        <span className="material-symbols-outlined" style={{ fontSize: "1.1rem", color: "#acabaa" }}>
          {menuOpen ? "expand_more" : "expand_less"}
        </span>
      </button>

      {menuOpen && (
        <div
          className="absolute bottom-full left-0 right-0 mb-2 rounded-2xl p-2 flex flex-col gap-1 card-shadow"
          style={{
            backgroundColor: "#191a1a",
            border: "1px solid rgba(72,72,72,0.3)",
          }}
        >
          <a
            href={address ? explorerAddress(address) : "#"}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition-colors hover:bg-[#252626]"
            style={{ color: "#e7e5e5" }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: "1.1rem", color: "#a7cbeb" }}>
              open_in_new
            </span>
            View on BaseScan
          </a>
          <button
            onClick={() => {
              if (address) navigator.clipboard.writeText(address);
              setMenuOpen(false);
            }}
            className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-left transition-colors hover:bg-[#252626]"
            style={{ color: "#e7e5e5" }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: "1.1rem", color: "#a7cbeb" }}>
              content_copy
            </span>
            Copy address
          </button>
          <button
            onClick={() => {
              disconnect();
              setMenuOpen(false);
            }}
            className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-left transition-colors hover:bg-[#252626]"
            style={{ color: "#ee7d77" }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: "1.1rem" }}>
              logout
            </span>
            Disconnect
          </button>
        </div>
      )}
    </div>
  );
}

function labelFor(id: string, fallback: string): string {
  if (id.includes("metaMask")) return "MetaMask";
  if (id.includes("injected")) return "Browser wallet";
  return fallback;
}
