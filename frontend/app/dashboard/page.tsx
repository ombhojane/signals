"use client";

import { Suspense, useState } from "react";

// ── Hero Section ────────────────────────────────────────────────────────────
function HeroSection() {
  return (
    <section className="grid grid-cols-1 md:grid-cols-12 gap-8 items-end mb-8">
      {/* Welcome */}
      <div className="md:col-span-8 flex flex-col gap-2">
        <span
          className="text-xs uppercase font-medium"
          style={{ color: '#a7cbeb', letterSpacing: '0.3em' }}
        >
          Portfolio Intelligence
        </span>
        <h2 className="text-5xl font-bold tracking-tight leading-tight" style={{ color: '#e7e5e5' }}>
          Welcome back,{' '}
          <br />
          <span style={{ color: '#acabaa' }}>Curator Alpha</span>
        </h2>
      </div>

      {/* Stats */}
      <div className="md:col-span-4 flex justify-end gap-12 pb-2">
        <div className="flex flex-col">
          <span className="text-xs uppercase tracking-widest mb-1" style={{ color: '#acabaa' }}>Total Value</span>
          <span className="text-2xl font-semibold tracking-tight" style={{ color: '#e7e5e5' }}>$1,420,592.12</span>
          <span className="text-xs mt-1 font-medium" style={{ color: '#a7cbeb' }}>
            +12.4% <span style={{ opacity: 0.5, fontWeight: 400 }}>24h</span>
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs uppercase tracking-widest mb-1" style={{ color: '#acabaa' }}>Active Signals</span>
          <span className="text-2xl font-semibold tracking-tight" style={{ color: '#e7e5e5' }}>14</span>
          <span className="text-xs mt-1 font-normal" style={{ color: '#acabaa' }}>Across 8 chains</span>
        </div>
      </div>
    </section>
  );
}

// ── Market Sentiment Widget ─────────────────────────────────────────────────
function MarketSentimentCard() {
  return (
    <div
      className="md:col-span-4 rounded-xl p-8 flex flex-col justify-between relative overflow-hidden group"
      style={{ backgroundColor: '#131313', height: '420px' }}
    >
      {/* Ambient glow */}
      <div
        className="absolute top-0 right-0 w-64 h-64 rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none"
        style={{ background: 'rgba(167,203,235,0.05)', filter: 'blur(100px)' }}
      />

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-12">
          <h3
            className="text-sm font-bold uppercase"
            style={{ letterSpacing: '0.2em', color: '#acabaa' }}
          >
            Market Sentiment
          </h3>
          <span className="material-symbols-outlined" style={{ color: '#a7cbeb', fontSize: '1.25rem' }}>analytics</span>
        </div>

        <div className="space-y-6">
          {/* Fear & Greed */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs mb-2">
              <span className="uppercase tracking-tighter" style={{ color: '#acabaa' }}>Fear &amp; Greed Index</span>
              <span className="font-bold" style={{ color: '#a7cbeb' }}>78 / 100</span>
            </div>
            <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ backgroundColor: '#252626' }}>
              <div
                className="h-full rounded-full"
                style={{ width: '78%', background: 'linear-gradient(to right, rgba(167,203,235,0.5), #a7cbeb)' }}
              />
            </div>
            <span className="text-[10px] uppercase tracking-widest mt-2" style={{ color: '#acabaa' }}>Extreme Greed</span>
          </div>

          {/* Editorial text */}
          <div className="pt-8">
            <p className="text-lg font-light leading-relaxed" style={{ color: '#e7e5e5' }}>
              The market is showing strong upward momentum driven by institutional inflows. Liquidity is concentrating in Tier 1 assets.
            </p>
          </div>
        </div>
      </div>

      <div className="relative z-10 pt-4">
        <button
          className="text-xs uppercase font-bold hover:gap-4 transition-all flex items-center gap-2"
          style={{ color: '#a7cbeb', letterSpacing: '0.2em' }}
        >
          Full Analysis{' '}
          <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>arrow_forward</span>
        </button>
      </div>
    </div>
  );
}

// ── Performance Orbit Chart ─────────────────────────────────────────────────
function PerformanceOrbitCard() {
  const [activeRange, setActiveRange] = useState<'1W' | '1M' | '1Y'>('1M');
  const barHeights = [40, 55, 48, 65, 80, 72, 90, 85, 70, 60, 65, 50];

  return (
    <div
      className="md:col-span-8 rounded-xl p-8 flex flex-col"
      style={{ backgroundColor: '#191a1a', height: '420px' }}
    >
      <div className="flex justify-between items-center mb-8">
        <div className="flex gap-4 items-center">
          <h3
            className="text-sm font-bold uppercase"
            style={{ letterSpacing: '0.2em', color: '#e7e5e5' }}
          >
            Performance Orbit
          </h3>
          <div className="flex gap-1">
            {(['1W', '1M', '1Y'] as const).map((r) => (
              <button
                key={r}
                onClick={() => setActiveRange(r)}
                className="px-3 py-1 rounded-full text-[10px] font-bold transition-all"
                style={
                  activeRange === r
                    ? { backgroundColor: '#a7cbeb', color: '#1e435e' }
                    : { backgroundColor: '#252626', color: '#acabaa' }
                }
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <span className="text-sm font-medium" style={{ color: '#acabaa' }}>Asset Distribution</span>
      </div>

      {/* Bar chart */}
      <div className="flex-1 flex items-end gap-1 px-4">
        {barHeights.map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-t-lg transition-colors hover:opacity-80 cursor-pointer"
            style={{
              height: `${h}%`,
              backgroundColor: i === 6 ? 'rgba(167,203,235,0.4)' : '#252626',
            }}
          />
        ))}
      </div>

      {/* X-axis labels */}
      <div
        className="flex justify-between mt-4 px-4 text-[10px] uppercase tracking-widest font-medium"
        style={{ color: '#acabaa' }}
      >
        <span>Jan 12</span>
        <span>Jan 19</span>
        <span>Jan 26</span>
        <span>Feb 02</span>
      </div>
    </div>
  );
}

// ── Top AI Signals ──────────────────────────────────────────────────────────
const SIGNALS = [
  {
    icon: 'sensors',
    iconColor: '#a7cbeb',
    title: 'SOL Ecosystem Accumulation',
    desc: 'High confidence buy signal detected in Solana liquidity pools',
    conf: '88% CONF',
    time: '2m ago',
    highlight: true,
  },
  {
    icon: 'trending_up',
    iconColor: '#acabaa',
    title: 'Arbitrum Governance Spike',
    desc: 'On-chain voting volume increasing rapidly; potential volatility',
    conf: '72% CONF',
    time: '14m ago',
    highlight: false,
  },
  {
    icon: 'auto_awesome',
    iconColor: '#acabaa',
    title: 'Layer 2 Rebalancing Flow',
    desc: 'Whale wallets moving assets from Mainnet to Optimism',
    conf: '64% CONF',
    time: '1h ago',
    highlight: false,
  },
];

function TopAISignals() {
  return (
    <div className="md:col-span-7 flex flex-col gap-4">
      <div className="flex items-center justify-between px-4 mb-2">
        <h3
          className="text-xs font-bold uppercase"
          style={{ letterSpacing: '0.2em', color: '#acabaa' }}
        >
          Top AI Signals
        </h3>
        <button
          className="text-[10px] uppercase font-bold"
          style={{ letterSpacing: '0.1em', color: '#a7cbeb' }}
        >
          Refresh Intel
        </button>
      </div>

      {SIGNALS.map((signal) => (
        <div
          key={signal.title}
          className="rounded-xl p-6 flex items-center justify-between group cursor-pointer transition-all"
          style={{ backgroundColor: '#131313' }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.backgroundColor = '#1f2020'; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.backgroundColor = '#131313'; }}
        >
          <div className="flex items-center gap-6">
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: '#252626' }}>
              <span
                className="material-symbols-outlined"
                style={{
                  color: signal.iconColor,
                  fontSize: '1.25rem',
                  fontVariationSettings: signal.highlight ? "'FILL' 1" : "'FILL' 0",
                }}
              >
                {signal.icon}
              </span>
            </div>
            <div>
              <h4 className="font-bold" style={{ color: '#e7e5e5' }}>{signal.title}</h4>
              <p className="text-xs mt-1" style={{ color: '#acabaa' }}>{signal.desc}</p>
            </div>
          </div>
          <div className="text-right">
            <span className="block font-bold tracking-tight" style={{ color: '#a7cbeb' }}>{signal.conf}</span>
            <span className="text-[10px] uppercase tracking-widest" style={{ color: '#acabaa' }}>{signal.time}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Featured Discovery ──────────────────────────────────────────────────────
function FeaturedDiscovery() {
  return (
    <div
      className="md:col-span-5 rounded-xl overflow-hidden relative group flex flex-col justify-end p-8"
      style={{ height: '340px' }}
    >
      {/* Background */}
      <div className="absolute inset-0" style={{ backgroundColor: '#111' }}>
        <div
          className="absolute inset-0 opacity-20"
          style={{ background: 'radial-gradient(ellipse at 30% 70%, rgba(167,203,235,0.15), transparent 70%)' }}
        />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: 'linear-gradient(rgba(37,38,38,0.8) 1px, transparent 1px), linear-gradient(90deg, rgba(37,38,38,0.8) 1px, transparent 1px)',
            backgroundSize: '30px 30px',
          }}
        />
      </div>
      <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/60 to-transparent" />

      {/* Content */}
      <div className="relative z-10 flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <span
            className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
            style={{ backgroundColor: 'rgba(167,203,235,0.2)', color: '#a7cbeb' }}
          >
            Curator&#39;s Choice
          </span>
        </div>
        <h4 className="text-2xl font-bold leading-tight" style={{ color: '#e7e5e5' }}>
          The Rise of DePIN:{' '}
          <br />
          Physical Infrastructure on-chain
        </h4>
        <p className="text-sm line-clamp-2" style={{ color: '#acabaa' }}>
          How decentralized physical networks are creating the next multi-billion dollar asset class for patient capital.
        </p>
        <button
          className="mt-2 py-3 px-6 rounded-full text-xs font-bold uppercase tracking-widest self-start transition-colors hover:text-[#1e435e]"
          style={{ backgroundColor: 'rgba(43,44,44,0.5)', backdropFilter: 'blur(12px)', color: '#e7e5e5' }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#a7cbeb'; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'rgba(43,44,44,0.5)'; }}
        >
          Read Deep Dive
        </button>
      </div>
    </div>
  );
}

// ── Footer ──────────────────────────────────────────────────────────────────
function DashboardFooter() {
  return (
    <footer
      className="mt-auto py-12 px-12"
      style={{ backgroundColor: 'rgb(0,0,0)', borderTop: '1px solid rgba(72,72,72,0.1)' }}
    >
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
        <div className="text-[10px] uppercase font-light" style={{ letterSpacing: '0.2em', color: '#525252' }}>
          © 2024 Signals Editorial. All rights reserved.
        </div>
        <div className="flex gap-10">
          {['Privacy', 'Terms', 'API Docs', 'Changelog'].map((link) => (
            <a
              key={link}
              href="#"
              className="text-[10px] uppercase font-light hover:underline underline-offset-4 transition-colors"
              style={{ letterSpacing: '0.2em', color: '#525252' }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = '#b1d4f5'; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = '#525252'; }}
            >
              {link}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────
function DashboardContent() {
  return (
    <div className="flex flex-col gap-10">
      {/* Hero */}
      <HeroSection />

      {/* Main Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        <MarketSentimentCard />
        <PerformanceOrbitCard />
        <TopAISignals />
        <FeaturedDiscovery />
      </div>

      {/* Footer */}
      <DashboardFooter />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-4">
            <div className="zen-pulse" />
            <span className="text-xs uppercase tracking-widest" style={{ color: '#acabaa' }}>
              Loading intelligence...
            </span>
          </div>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
