"use client";

import Link from "next/link";
import { CHAIN, VAULT_ADDRESS, explorerAddress } from "@/lib/web3/constants";
import { formatUsdc, useVaultState } from "@/lib/web3/hooks";

// ─── Navbar ──────────────────────────────────────────────────────────────
function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-8 md:px-16 h-20 nav-glass">
      <div className="flex items-center gap-10">
        <Link href="/" className="text-lg font-bold tracking-tighter text-white">
          Signals
        </Link>
        <div className="hidden md:flex gap-6 text-[11px] font-semibold tracking-[0.15em] uppercase">
          <a href="#how" className="text-neutral-500 hover:text-white transition-colors">
            How it works
          </a>
          <a href="#why" className="text-neutral-500 hover:text-white transition-colors">
            Why Signals
          </a>
          <Link
            href="/dashboard/leaderboard"
            className="text-neutral-500 hover:text-white transition-colors"
          >
            Proof
          </Link>
        </div>
      </div>
      <Link
        href="/dashboard/vault"
        className="px-5 py-2.5 rounded-full font-bold text-[11px] tracking-widest uppercase transition-all active:scale-95"
        style={{ backgroundColor: "#a7cbeb", color: "#1e435e" }}
      >
        Launch App
      </Link>
    </nav>
  );
}

// ─── Hero ────────────────────────────────────────────────────────────────
function HeroSection() {
  return (
    <section
      className="min-h-screen flex flex-col items-center justify-center px-6 text-center"
      style={{ paddingTop: "8rem", paddingBottom: "4rem" }}
    >
      <div
        className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full mb-10"
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <span className="zen-pulse" />
        <span
          className="text-[10px] uppercase tracking-[0.25em] font-medium"
          style={{ color: "#acabaa" }}
        >
          Live on {CHAIN.name}
        </span>
      </div>

      <h1
        className="font-bold text-white mb-6 max-w-5xl"
        style={{
          fontSize: "clamp(3rem, 9vw, 6.5rem)",
          lineHeight: "0.95",
          letterSpacing: "-0.04em",
        }}
      >
        Deposit USDC.
        <br />
        <span style={{ color: "#a7cbeb" }}>AI trades it.</span>
        <br />
        <span style={{ color: "rgba(255,255,255,0.18)" }}>Every decision proven on-chain.</span>
      </h1>

      <p className="text-lg md:text-xl text-neutral-400 max-w-xl font-light leading-relaxed mb-14 mx-auto">
        A non-custodial ERC-4626 vault on Base. Every trade ships with the AI&apos;s
        reasoning hash committed on-chain — no edits, no cherry-picking.
      </p>

      <div className="flex flex-col sm:flex-row gap-3 items-center">
        <Link
          href="/dashboard/vault"
          className="px-10 py-4 rounded-full font-bold text-sm tracking-wide hover:opacity-90 transition-all active:scale-95"
          style={{ backgroundColor: "#a7cbeb", color: "#1e435e" }}
        >
          Launch App
        </Link>
        <Link
          href="/dashboard/leaderboard"
          className="px-10 py-4 rounded-full font-semibold text-sm tracking-wide hover:bg-white/10 transition-all active:scale-95"
          style={{
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "rgba(255,255,255,0.75)",
          }}
        >
          See Proof of Alpha
        </Link>
      </div>
    </section>
  );
}

// ─── Stat Card ───────────────────────────────────────────────────────────
function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div
      className="rounded-2xl p-6 flex flex-col gap-2"
      style={{
        backgroundColor: "#131313",
        border: "1px solid rgba(72,72,72,0.25)",
      }}
    >
      <span
        className="text-[10px] font-semibold tracking-[0.2em] uppercase"
        style={{ color: "#acabaa" }}
      >
        {label}
      </span>
      <span
        className="text-2xl md:text-3xl font-black font-mono tracking-tight"
        style={{ color: accent ? "#a7cbeb" : "#e7e5e5" }}
      >
        {value}
      </span>
      {sub ? (
        <span className="text-xs" style={{ color: "#acabaa" }}>
          {sub}
        </span>
      ) : null}
    </div>
  );
}

// ─── Live Stats Strip (reads vault contract directly) ───────────────────
function LiveStatsStrip() {
  const { totalAssets, totalSupply, positionOpen, sharePriceUsdc } = useVaultState();

  return (
    <section className="px-6 md:px-16 pt-8 pb-20 max-w-[1400px] mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <div className="zen-pulse" />
        <span
          className="text-[10px] uppercase tracking-[0.3em] font-semibold"
          style={{ color: "#a7cbeb" }}
        >
          Live Vault State
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Value Locked"
          value={`${formatUsdc(totalAssets, 2)} USDC`}
          sub={`On ${CHAIN.name}`}
        />
        <StatCard
          label="Shares Outstanding"
          value={formatUsdc(totalSupply, 2)}
          sub="ERC-4626 sVAULT"
        />
        <StatCard
          label="Share Price"
          value={sharePriceUsdc.toFixed(4)}
          sub="USDC per sVAULT"
        />
        <StatCard
          label="Status"
          value={positionOpen ? "Trading" : "Idle"}
          sub={positionOpen ? "Position open" : "Accepting deposits"}
          accent
        />
      </div>
    </section>
  );
}

// ─── How it works ────────────────────────────────────────────────────────
function HowItWorksSection() {
  const steps = [
    {
      num: "01",
      title: "Deposit USDC",
      desc: "Connect your wallet and deposit USDC into the vault contract. You receive sVAULT shares 1:1 with the current share price.",
    },
    {
      num: "02",
      title: "AI trades on Uniswap V3",
      desc: "The Signals agent analyzes market data and executes trades through the vault on Uniswap V3. Every trade commits a reasoning hash on-chain.",
    },
    {
      num: "03",
      title: "Withdraw anytime",
      desc: "When the vault is idle, redeem your sVAULT shares back to USDC at the current share price. Gas-efficient. Fully non-custodial.",
    },
  ];

  return (
    <section id="how" className="px-6 md:px-16 py-28 max-w-[1400px] mx-auto">
      <div className="flex items-end justify-between mb-16 flex-wrap gap-6">
        <div>
          <span
            className="text-[9px] uppercase tracking-[0.3em] font-semibold block mb-5"
            style={{ color: "#a7cbeb" }}
          >
            How it works
          </span>
          <h2
            className="text-5xl md:text-6xl font-bold tracking-tighter text-white"
            style={{ lineHeight: "0.95" }}
          >
            Three steps.
            <br />
            Zero custody.
          </h2>
        </div>
        <Link
          href="/dashboard/vault"
          className="text-xs uppercase font-bold flex items-center gap-2 transition-colors"
          style={{ color: "#a7cbeb", letterSpacing: "0.2em" }}
        >
          Start now
          <span className="material-symbols-outlined" style={{ fontSize: "1rem" }}>
            arrow_forward
          </span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map((s) => (
          <div
            key={s.num}
            className="rounded-2xl p-8 flex flex-col gap-4"
            style={{
              backgroundColor: "#131313",
              border: "1px solid rgba(72,72,72,0.25)",
            }}
          >
            <span
              className="text-5xl font-black font-mono tracking-tighter"
              style={{ color: "#a7cbeb", opacity: 0.5 }}
            >
              {s.num}
            </span>
            <h3 className="text-xl font-bold" style={{ color: "#e7e5e5" }}>
              {s.title}
            </h3>
            <p className="text-sm font-light leading-relaxed" style={{ color: "#acabaa" }}>
              {s.desc}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── Value Props ─────────────────────────────────────────────────────────
function ValuePropsSection() {
  const props = [
    {
      icon: "verified",
      title: "Verifiable Alpha",
      desc: "Every trade emits a TradeExecuted event with a keccak256 hash of the AI reasoning. Click any trade on the Proof page to audit the exact decision that produced it.",
    },
    {
      icon: "lock",
      title: "Non-custodial",
      desc: "Your funds sit inside an audited-base ERC-4626 vault contract, not on our servers. You interact directly with the contract from your wallet. Withdraw anytime.",
    },
    {
      icon: "bolt",
      title: "Agent Economy",
      desc: "Our AI signal API is priced per call via x402 — HTTP-native USDC micropayments. Other agents pay to query our AI. No API keys. No Stripe.",
    },
  ];

  return (
    <section
      id="why"
      className="py-28"
      style={{
        background: "rgba(255,255,255,0.015)",
        borderTop: "1px solid rgba(255,255,255,0.04)",
        borderBottom: "1px solid rgba(255,255,255,0.04)",
      }}
    >
      <div className="max-w-6xl mx-auto px-6 md:px-16">
        <div className="flex items-end justify-between mb-16 flex-wrap gap-6">
          <div>
            <span
              className="text-[9px] uppercase tracking-[0.3em] font-semibold block mb-5"
              style={{ color: "#a7cbeb" }}
            >
              Why Signals
            </span>
            <h2
              className="text-5xl md:text-6xl font-bold tracking-tighter text-white"
              style={{ lineHeight: "0.95" }}
            >
              Load-bearing
              <br />
              web3.
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-16">
          {props.map((p) => (
            <div key={p.title} className="space-y-5">
              <div
                className="h-10 w-10 rounded-full flex items-center justify-center"
                style={{
                  backgroundColor: "rgba(167,203,235,0.1)",
                  border: "1px solid rgba(167,203,235,0.2)",
                }}
              >
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: "1.25rem", color: "#a7cbeb" }}
                >
                  {p.icon}
                </span>
              </div>
              <h3 className="text-xl font-bold tracking-tight" style={{ color: "#e7e5e5" }}>
                {p.title}
              </h3>
              <p className="text-neutral-400 font-light leading-relaxed text-sm">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── CTA ─────────────────────────────────────────────────────────────────
function CTASection() {
  return (
    <section className="px-6 py-36">
      <div className="max-w-4xl mx-auto text-center">
        <h2
          className="font-bold tracking-tighter text-white mb-8"
          style={{
            fontSize: "clamp(2.5rem, 7vw, 5.5rem)",
            lineHeight: "0.93",
            letterSpacing: "-0.04em",
          }}
        >
          Let the AI trade.
          <br />
          Keep the receipts.
        </h2>
        <p className="text-lg text-neutral-400 font-light leading-relaxed mb-14 max-w-xl mx-auto">
          All on Base Sepolia. Every trade committed to the chain with its reasoning hash.
        </p>
        <Link
          href="/dashboard/vault"
          className="inline-block px-14 py-5 rounded-full font-black text-base tracking-tight hover:scale-[1.03] transition-all active:scale-95"
          style={{ backgroundColor: "#a7cbeb", color: "#1e435e" }}
        >
          Launch Signals
        </Link>
      </div>
    </section>
  );
}

// ─── Footer ──────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer style={{ backgroundColor: "#000", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
      <div className="max-w-7xl mx-auto px-8 md:px-16 py-12 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="space-y-2 text-center md:text-left">
          <div className="text-base font-bold tracking-tighter text-white">Signals</div>
          <p
            className="text-[10px] uppercase tracking-[0.2em] font-light"
            style={{ color: "#404040" }}
          >
            AI trading vault · {CHAIN.name} · Non-custodial
          </p>
        </div>
        <div
          className="flex flex-wrap justify-center gap-6 text-[10px] uppercase tracking-[0.25em] font-semibold"
          style={{ color: "#404040" }}
        >
          <a
            href={explorerAddress(VAULT_ADDRESS)}
            target="_blank"
            rel="noreferrer"
            className="hover:text-white transition-colors"
          >
            Contract
          </a>
          <Link href="/dashboard/leaderboard" className="hover:text-white transition-colors">
            Proof
          </Link>
          <Link href="/dashboard/simulation" className="hover:text-white transition-colors">
            Signal API
          </Link>
          <Link href="/dashboard/vault" className="hover:text-white transition-colors">
            Vault
          </Link>
        </div>
      </div>
    </footer>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div style={{ backgroundColor: "#0e0e0e", color: "#e7e5e5" }}>
      <Navbar />
      <main>
        <HeroSection />
        <LiveStatsStrip />
        <HowItWorksSection />
        <ValuePropsSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
