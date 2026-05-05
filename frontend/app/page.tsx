"use client";

import Link from "next/link";
import Image from "next/image";
import { CHAIN, VAULT_ADDRESS, explorerAddress } from "@/lib/web3/constants";
import { formatUsdc, useVaultState } from "@/lib/web3/hooks";
import { useState, useEffect } from "react";

// ─── Utility ─────────────────────────────────────────────────────────────
function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(" ");
}

// ─── Smooth Scroll Function ──────────────────────────────────────────────
function goToSection(sectionName: string) {
  if (sectionName === "Home") {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  const element = document.getElementById(sectionName);
  if (element) {
    element.scrollIntoView({ behavior: "smooth" });
  }
}

// ─── Navbar ──────────────────────────────────────────────────────────────
function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav 
      className={cn(
        "fixed top-0 w-full z-50 flex justify-between items-center px-6 md:px-12 transition-all duration-500",
        scrolled ? "h-16 nav-glass backdrop-blur-xs shadow-lg shadow-black/20" : "h-24 bg-transparent border-transparent"
      )}
    >
      <div className="flex items-center gap-4 md:gap-12">
        <button 
          onClick={() => goToSection("Home")}
          className="flex items-center gap-3 group"
        >
          <div className="relative w-8 h-8 rounded-full overflow-hidden flex items-center justify-center transition-transform duration-500 group-hover:scale-105">
            <Image 
              src="/signal_logo.svg" 
              alt="Signals Logo" 
              fill
              className="object-cover"
            />
          </div>
          <span className="text-xl font-bold tracking-tighter text-foreground" style={{ fontFamily: 'var(--font-space)' }}>Signals</span>
        </button>
        <div className="hidden md:flex gap-8 text-[11px] font-semibold tracking-[0.15em] uppercase">
          <button 
            onClick={() => goToSection("how")}
            className="text-muted-foreground hover:text-foreground transition-colors duration-300 relative group overflow-hidden"
          >
            How it works
            <span className="absolute bottom-0 left-0 w-full h-[1px] bg-primary scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300"></span>
          </button>
          <button 
            onClick={() => goToSection("why")}
            className="text-muted-foreground hover:text-foreground transition-colors duration-300 relative group overflow-hidden"
          >
            Why Signals
            <span className="absolute bottom-0 left-0 w-full h-[1px] bg-primary scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300"></span>
          </button>
          <Link
            href="/dashboard/leaderboard"
            className="text-muted-foreground hover:text-foreground transition-colors duration-300 relative group overflow-hidden"
          >
            Proof
            <span className="absolute bottom-0 left-0 w-full h-[1px] bg-primary scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300"></span>
          </Link>
        </div>
      </div>
      <Link
        href="/dashboard/vault"
        className="px-6 py-2.5 rounded-full font-bold text-[11px] tracking-widest uppercase transition-all duration-300 active:scale-95 group relative overflow-hidden"
        style={{ 
          backgroundColor: scrolled ? "var(--primary)" : "var(--primary-dim)", 
          color: scrolled ? "var(--primary-foreground)" : "var(--foreground)",
          border: scrolled ? "1px solid transparent" : "1px solid var(--border)"
        }}
      >
        <span className="relative z-10">Launch App</span>
        {!scrolled && (
          <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
        )}
      </Link>
    </nav>
  );
}

// ─── Hero ────────────────────────────────────────────────────────────────
function HeroSection() {
  return (
    <section
      id="Home"
      className="min-h-screen flex flex-col items-center justify-center px-6 text-center relative overflow-hidden"
      style={{ paddingTop: "6rem", paddingBottom: "4rem" }}
    >
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full opacity-[0.03] pointer-events-none blur-[100px]" style={{ background: "radial-gradient(circle, var(--primary) 0%, transparent 70%)" }} />

      <div
        className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full mb-12 animate-fade-in zen-glass-light"
        style={{
          animation: "fadeUp 1s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both"
        }}
      >
        <span className="zen-pulse" />
        <span
          className="text-[10px] uppercase tracking-[0.25em] font-medium text-neutral-300"
        >
          Live on {CHAIN.name}
        </span>
      </div>

      <h1
        className="font-bold text-foreground mb-8 max-w-5xl tracking-tighter text-5xl md:text-7xl"
        style={{
          lineHeight: "0.9",
          animation: "fadeUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both",
          fontFamily: "var(--font-space)"
        }}
      >
        Intelligent Signals.
        <br />
        <span style={{ color: "var(--primary)" }}>Autonomous trading.</span>
        <br />
        <span className="opacity-40 text-transparent bg-clip-text bg-gradient-to-b from-foreground to-muted-foreground">Unified vaults.</span>
      </h1>

      <p 
        className="text-lg md:text-xl text-muted-foreground max-w-2xl font-light leading-relaxed mb-16 mx-auto"
        style={{ animation: "fadeUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both" }}
      >
        Multi-source signal analysis powered by Gemma and Langchain. RL-based autonomous trading with real-time 
        market adaptation. Unified vault management with kill-switch safety mechanisms - everything onchain!
      </p>

      <div 
        className="flex flex-col sm:flex-row gap-4 items-center relative z-10"
        style={{ animation: "fadeUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.4s both" }}
      >
        <Link
          href="/dashboard/vault"
          className="px-10 py-4 rounded-full font-bold text-sm tracking-wide transition-all active:scale-95 hover:brightness-110 shadow-primary/20 hover:shadow-primary/40 flex items-center gap-2 group bg-primary text-primary-foreground"
        >
          Launch Signals
          <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">arrow_forward</span>
        </Link>
        <Link
          href="/dashboard/leaderboard"
          className="px-10 py-4 rounded-full font-semibold text-sm tracking-wide transition-all active:scale-95 flex items-center gap-2 group border border-border bg-transparent text-muted-foreground hover:text-foreground"
        >
          <span className="transition-colors">See Proof of Alpha</span>
        </Link>
      </div>

      {/* Scroll Indicator */}
      <div 
        className="absolute bottom-10 flex flex-col items-center gap-3 animate-bounce cursor-pointer group"
        onClick={() => goToSection('how')}
        style={{
          animation: "fadeUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.8s both, bounce 2s infinite 2s"
        }}
      >
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
      `}</style>
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
      className="rounded-[20px] p-8 flex flex-col gap-3 group transition-all duration-500 hover:-translate-y-1 relative overflow-hidden"
      style={{
        backgroundColor: "var(--surface-container-low)",
        border: "1px solid var(--border)",
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-[rgba(255,255,255,0.03)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      <span
        className="text-[10px] font-semibold tracking-[0.2em] uppercase"
        style={{ color: "var(--on-surface-variant)" }}
      >
        {label}
      </span>
      <span
        className="text-3xl md:text-4xl font-black font-mono tracking-tight numeric"
        style={{ color: accent ? "var(--primary)" : "var(--foreground)" }}
      >
        {value}
      </span>
      {sub ? (
        <span className="text-xs font-medium" style={{ color: "var(--on-surface-variant)" }}>
          {sub}
        </span>
      ) : null}
    </div>
  );
}

// ─── Live Stats Strip ───────────────────────────────────────────────────
function LiveStatsStrip() {
  const { totalAssets, totalSupply, positionOpen, sharePriceUsdc } = useVaultState();

  return (
    <section className="px-6 md:px-16 pt-8 pb-16 md:pb-32" style={{ maxWidth: "1400px", marginLeft: "auto", marginRight: "auto" }}>
      <div className="flex items-center gap-3 mb-8">
        <div className="zen-pulse" />
        <span
          className="text-[11px] uppercase tracking-[0.3em] font-semibold"
          style={{ color: "var(--primary)" }}
        >
          Live Vault State
        </span>
        <div className="flex-1 h-[1px] bg-gradient-to-r from-primary/20 to-transparent ml-4" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Total Value Locked"
          value={`$${formatUsdc(totalAssets, 2)}`}
          sub="Managed Across Protocols"
        />
        <StatCard
          label="Shares Outstanding"
          value={formatUsdc(totalSupply, 2)}
          sub="sVAULT Tokens"
        />
        <StatCard
          label="Share Price"
          value={`$${sharePriceUsdc.toFixed(4)}`}
          sub="USDC per Share"
        />
        <StatCard
          label="Trading Status"
          value={positionOpen ? "Active" : "Idle"}
          sub={positionOpen ? "Executing trades" : "Next signal incoming"}
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
      title: "Multi-Source Signal Analysis",
      desc: "Aggregates Twitter sentiment, on-chain metrics, and DEX activity. AI-powered refinement via Gemma and Langchain agents for high-quality, actionable Signals.",
    },
    {
      num: "02",
      title: "RL-Based Autonomous Trading",
      desc: "Reinforcement learning agent executes trades with real-time market adaptation. Risk management, portfolio optimization, and intelligent rebalancing—all autonomous.",
    },
    {
      num: "03",
      title: "Token Safety & Kill-Switch",
      desc: "Real-time token risk assessment with kill-switch mechanism for emergency stops. Comprehensive logging, rate limiting, and resilience safeguards.",
    },
  ];

  return (
    <section id="how" className="px-6 md:px-16 py-16 md:py-32 relative" style={{ maxWidth: "1400px", marginLeft: "auto", marginRight: "auto" }}>
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-16 md:mb-24 gap-8">
        <div className="max-w-2xl">
          <span
            className="text-[10px] uppercase tracking-[0.3em] font-semibold block mb-6"
            style={{ color: "var(--primary)" }}
          >
            How it works
          </span>
          <h2
            className="text-4xl md:text-5xl font-bold tracking-tight text-foreground"
            style={{ lineHeight: "0.95", fontFamily: "var(--font-space)" }}
          >
            Three pillars.
            <br />
            <span className="text-muted-foreground">On-chain execution.</span>
          </h2>
        </div>
        <Link
          href="/dashboard/vault"
          className="text-xs uppercase font-bold flex items-center gap-2 transition-colors group"
          style={{ color: "var(--primary)", letterSpacing: "0.2em" }}
        >
          <span className="relative">
            Start now
            <span className="absolute bottom-0 left-0 w-full h-[1px] bg-primary scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300"></span>
          </span>
          <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">
            arrow_forward
          </span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {steps.map((s, i) => (
          <div
            key={s.num}
            className="rounded-[24px] p-10 flex flex-col gap-6 relative group transition-all duration-500 hover:-translate-y-2 border border-transparent"
            style={{
              backgroundColor: "var(--surface-container-low)"
            }}
          >
            <div className="absolute inset-0 rounded-[24px] ring-1 ring-border group-hover:ring-border/80 transition-all duration-500 pointer-events-none" />
            <span
              className="text-6xl font-black font-mono tracking-tighter"
              style={{ color: "var(--primary)", opacity: 0.2 }}
            >
              {s.num}
            </span>
            <h3 className="text-2xl font-bold tracking-tight" style={{ color: "var(--foreground)", fontFamily: "var(--font-space)" }}>
              {s.title}
            </h3>
            <p className="text-[15px] font-light leading-relaxed" style={{ color: "var(--on-surface-variant)" }}>
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
      icon: "insights",
      title: "Intelligent Signal Generation",
      desc: "Multi-source analysis combines Twitter sentiment, on-chain metrics, and DEX activity. AI-powered refinement produces high-quality, low-noise Signals with customizable thresholds.",
    },
    {
      icon: "smart_toy",
      title: "Autonomous RL Trading",
      desc: "Reinforcement learning agent trained on market simulations. Real-time adaptation, portfolio optimization, risk management, and intelligent rebalancing—fully autonomous execution.",
    },
    {
      icon: "shield",
      title: "Safety-First Design",
      desc: "Token risk assessment framework with kill-switch emergency stops. Rate limiting, resilience mechanisms, comprehensive audit trails, and multi-protocol vault support.",
    },
  ];

  return (
    <section
      id="why"
      className="py-16 md:py-32 relative overflow-hidden"
      style={{
        background: "var(--surface-container-lowest)",
        borderTop: "1px solid var(--border)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div className="max-w-7xl mx-auto px-6 md:px-16 relative z-10">
        <div className="mb-24">
          <span
            className="text-[10px] uppercase tracking-[0.3em] font-semibold block mb-6"
            style={{ color: "var(--primary)" }}
          >
            Why Signals
          </span>
          <h2
            className="text-4xl md:text-5xl font-bold tracking-tight text-foreground"
            style={{ lineHeight: "0.95", fontFamily: "var(--font-space)" }}
          >
            Built for
            <br />
            Web3 traders.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          {props.map((p) => (
            <div 
              key={p.title} 
              className="flex flex-col space-y-6 group"
            >
              <div
                className="h-16 w-16 rounded-2xl flex items-center justify-center group-hover:scale-105 transition-transform duration-500 ease-out"
                style={{
                  backgroundColor: "color-mix(in srgb, var(--primary) 5%, transparent)",
                  border: "1px solid color-mix(in srgb, var(--primary) 15%, transparent)",
                }}
              >
                <span
                  className="material-symbols-outlined transition-colors duration-500"
                  style={{ fontSize: "2rem", color: "var(--primary)" }}
                >
                  {p.icon}
                </span>
              </div>
              <div>
                <h3 className="text-2xl font-bold tracking-tight mb-4" style={{ color: "var(--foreground)", fontFamily: "var(--font-space)" }}>
                  {p.title}
                </h3>
                <p className="text-[15px] font-light leading-relaxed" style={{ color: "var(--on-surface-variant)" }}>
                  {p.desc}
                </p>
              </div>
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
    <section className="px-6 py-24 md:py-40">
      <div className="max-w-4xl mx-auto text-center relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-[0.02] pointer-events-none blur-[80px]" style={{ background: "radial-gradient(circle, #ffffff 0%, transparent 70%)" }} />
        
        <h2
          className="font-bold tracking-tight text-foreground mb-8 relative z-10 text-4xl md:text-5xl"
          style={{
            lineHeight: "0.93",
            fontFamily: "var(--font-space)"
          }}
        >
          Cut through the noise.
          <br />
          <span className="text-muted-foreground">Trade with confidence.</span>
        </h2>
        <p className="text-lg md:text-xl text-muted-foreground font-light leading-relaxed mb-16 max-w-xl mx-auto relative z-10">
          Intelligent Signals meet autonomous trading. Multi-protocol vault management with safety mechanisms 
          built-in. Everything on-chain, fully auditable.
        </p>
        <Link
          href="/dashboard/vault"
          className="inline-block px-12 py-5 rounded-full font-bold text-sm tracking-wide transition-all active:scale-95 hover:brightness-110 shadow-primary/20 hover:shadow-primary/40 relative z-10 bg-primary text-primary-foreground"
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
    <footer style={{ backgroundColor: "var(--surface)", borderTop: "1px solid var(--border)" }}>
      <div className="max-w-[1400px] mx-auto px-6 md:px-16 py-16 flex flex-col md:flex-row justify-between items-start md:items-center gap-12">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8 rounded-full overflow-hidden">
              <Image 
                src="/signal_logo.svg" 
                alt="Signals Logo" 
                fill
                className="object-cover"
              />
            </div>
            <span className="text-xl font-bold tracking-tighter text-foreground" style={{ fontFamily: "var(--font-space)" }}>Signals</span>
          </div>
          <p
            className="text-[11px] uppercase tracking-[0.2em] font-medium"
            style={{ color: "var(--on-surface-variant)" }}
          >
            AI trading vault · {CHAIN.name} · Non-custodial
          </p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-12 gap-y-4 text-[11px] uppercase tracking-[0.2em] font-semibold w-full md:w-auto">
          <a
            href={explorerAddress(VAULT_ADDRESS)}
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Contract
          </a>
          <Link href="/dashboard/leaderboard" className="text-muted-foreground hover:text-foreground transition-colors">
            Proof
          </Link>
          <Link href="/dashboard/simulation" className="text-muted-foreground hover:text-foreground transition-colors">
            Signal API
          </Link>
          <Link href="/dashboard/vault" className="text-primary hover:text-foreground transition-colors">
            Vault App
          </Link>
        </div>
      </div>
    </footer>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div style={{ backgroundColor: "var(--background)", color: "var(--foreground)" }}>
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
