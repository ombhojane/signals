"use client";

import Link from "next/link";

// ─── Navbar ────────────────────────────────────────────────────────────────
function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-8 md:px-16 h-20 nav-glass">
      <div className="flex items-center gap-10">
        <Link href="/" className="text-lg font-bold tracking-tighter text-white">
          Signals Zen
        </Link>
        <div className="hidden md:flex gap-6 text-[11px] font-semibold tracking-[0.15em] uppercase">
          <Link href="#intelligence" className="text-white/90 transition-opacity hover:opacity-60">Intelligence</Link>
          <Link href="#" className="text-neutral-500 transition-opacity hover:opacity-100">Portfolio</Link>
          <Link href="#" className="text-neutral-500 transition-opacity hover:opacity-100">Market</Link>
        </div>
      </div>
      <div className="flex items-center gap-5">
        <div className="hidden md:flex gap-3">
          <svg className="w-5 h-5 text-neutral-400 cursor-pointer hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <svg className="w-5 h-5 text-neutral-400 cursor-pointer hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
          </svg>
        </div>
        <Link
          href="/dashboard"
          className="px-5 py-2.5 rounded-full font-bold text-[11px] tracking-widest uppercase transition-all active:scale-95"
          style={{ backgroundColor: '#a7cbeb', color: '#1e435e' }}
        >
          Launch App
        </Link>
      </div>
    </nav>
  );
}

// ─── Hero ──────────────────────────────────────────────────────────────────
function HeroSection() {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center" style={{ paddingTop: '8rem', paddingBottom: '4rem' }}>
      {/* Live badge */}
      <div
        className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full mb-10"
        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
      >
        <span
          className="inline-block w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: '#a7cbeb', boxShadow: '0 0 8px #a7cbeb' }}
        />
        <span className="text-[10px] uppercase tracking-[0.25em] font-medium" style={{ color: '#acabaa' }}>
          Live On-Chain Intelligence
        </span>
      </div>

      {/* Headline */}
      <h1
        className="font-bold text-white mb-6 max-w-5xl"
        style={{ fontSize: 'clamp(3.5rem, 10vw, 7.5rem)', lineHeight: '0.93', letterSpacing: '-0.04em' }}
      >
        Quiet clarity in a{' '}
        <br />
        <span style={{ color: 'rgba(255,255,255,0.18)' }}>noisy ecosystem.</span>
      </h1>

      {/* Subtitle */}
      <p className="text-lg md:text-xl text-neutral-400 max-w-xl font-light leading-relaxed mb-14 mx-auto">
        Distilling global on-chain complexity into actionable editorial intelligence for the discerning institution.
      </p>

      {/* CTAs */}
      <div className="flex flex-col sm:flex-row gap-3 items-center">
        <Link
          href="/dashboard"
          className="px-10 py-4 rounded-full font-bold text-sm tracking-wide hover:opacity-90 transition-all active:scale-95"
          style={{ backgroundColor: 'white', color: 'black' }}
        >
          Connect Wallet
        </Link>
        <Link
          href="#intelligence"
          className="px-10 py-4 rounded-full font-semibold text-sm tracking-wide hover:bg-white/10 transition-all active:scale-95"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.75)' }}
        >
          Explore Signals
        </Link>
      </div>

      {/* Scroll hint */}
      <div className="mt-20 flex flex-col items-center gap-2 opacity-30">
        <div className="w-px h-12" style={{ background: 'linear-gradient(to bottom, transparent, #a7cbeb)' }} />
        <span className="text-[9px] uppercase tracking-[0.3em]" style={{ color: '#acabaa' }}>Scroll</span>
      </div>
    </section>
  );
}

// ─── Proven Intelligence ────────────────────────────────────────────────────
function ProvenSection() {
  return (
    <section id="intelligence" className="px-6 md:px-16 py-28 max-w-[1400px] mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
        {/* Left */}
        <div className="lg:col-span-5 space-y-8">
          <div>
            <span className="text-[9px] uppercase tracking-[0.3em] font-semibold block mb-5" style={{ color: '#a7cbeb' }}>
              Proven Intelligence
            </span>
            <h2 className="text-5xl font-bold tracking-tighter text-white leading-[1.0]">
              Proven<br />Intelligence.
            </h2>
          </div>
          <p className="text-lg text-neutral-400 font-light leading-relaxed">
            Our proprietary filtering algorithm surfaces the top 0.01% of market movements, providing a definitive edge in the noise of decentralized finance.
          </p>

          <div className="grid grid-cols-2 gap-8 pt-2">
            {[
              { label: 'Accuracy', value: '99.4%' },
              { label: 'Latency', value: '12ms' },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="text-[9px] uppercase tracking-[0.25em] mb-2" style={{ color: '#737373' }}>{label}</div>
                <div className="text-3xl font-bold text-white tracking-tighter">{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Mock dashboard card */}
        <div className="lg:col-span-7">
          <div
            className="rounded-[2rem] p-px overflow-hidden"
            style={{ background: 'linear-gradient(135deg, rgba(167,203,235,0.15), rgba(167,203,235,0.03) 60%, transparent)' }}
          >
            <div className="rounded-[2rem] p-8 space-y-5" style={{ backgroundColor: '#0f0f0f' }}>
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="zen-pulse" />
                  <span className="text-[9px] uppercase tracking-[0.25em] font-semibold" style={{ color: '#a7cbeb' }}>Live Network</span>
                </div>
                <span className="text-[9px] uppercase tracking-[0.2em]" style={{ color: '#525252' }}>Portfolio Intelligence</span>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Total Value', value: '$1.42M', sub: '+12.4%' },
                  { label: '24h Volume', value: '$34.2B', sub: '+5.1%' },
                  { label: 'Active Signals', value: '14', sub: '8 chains' },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-2xl p-4" style={{ backgroundColor: '#191a1a' }}>
                    <div className="text-[9px] uppercase tracking-[0.2em] mb-2" style={{ color: '#acabaa' }}>{stat.label}</div>
                    <div className="text-xl font-bold text-white">{stat.value}</div>
                    <div className="text-[10px] mt-1" style={{ color: '#a7cbeb' }}>{stat.sub}</div>
                  </div>
                ))}
              </div>

              {/* Bar chart */}
              <div className="rounded-2xl p-5" style={{ backgroundColor: '#131313' }}>
                <div className="text-[9px] uppercase tracking-[0.2em] mb-4" style={{ color: '#acabaa' }}>Performance Orbit — 1M</div>
                <div className="flex items-end gap-1" style={{ height: '72px' }}>
                  {[40, 55, 48, 65, 80, 72, 90, 85, 70, 60, 65, 50].map((h, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-t"
                      style={{
                        height: `${h}%`,
                        backgroundColor: i === 6 ? 'rgba(167,203,235,0.5)' : '#252626',
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Signal row */}
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: '#1f2020' }}>
                    <svg className="w-4 h-4" style={{ color: '#a7cbeb' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white">SOL Ecosystem Accumulation</div>
                    <div className="text-[10px]" style={{ color: '#acabaa' }}>High confidence buy signal</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold" style={{ color: '#a7cbeb' }}>88% CONF</div>
                  <div className="text-[9px]" style={{ color: '#525252' }}>2m ago</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Trust Architecture ─────────────────────────────────────────────────────
function TrustSection() {
  return (
    <section className="py-32" style={{ background: 'rgba(255,255,255,0.015)', borderTop: '1px solid rgba(255,255,255,0.04)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
      <div className="max-w-6xl mx-auto px-6 md:px-16">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end mb-20 gap-8">
          <div className="max-w-2xl">
            <span className="text-[9px] uppercase tracking-[0.35em] font-semibold block mb-6" style={{ color: '#a7cbeb' }}>
              Trust Architecture
            </span>
            <h2 className="text-5xl md:text-6xl font-bold tracking-tighter text-white" style={{ lineHeight: '0.92' }}>
              The standard for<br />institutional web3.
            </h2>
          </div>
          <p className="text-neutral-500 text-sm font-light max-w-xs leading-relaxed">
            Built at the intersection of quantitative finance and editorial excellence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-16">
          {[
            {
              title: 'Immutable Performance',
              desc: 'Every intelligence signal is cryptographically signed and archived on-chain for total transparency.',
            },
            {
              title: 'Institutional Custody',
              desc: 'Engineered with multi-sig architecture and air-gapped security protocols for sovereign peace of mind.',
            },
            {
              title: 'Curated Alpha',
              desc: 'Moving beyond raw data to provide context, narrative, and actionable foresight for long-term capital.',
            },
          ].map((f) => (
            <div key={f.title} className="space-y-5">
              <div className="h-px w-full" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }} />
              <h3 className="text-xl font-bold tracking-tight text-white">{f.title}</h3>
              <p className="text-neutral-400 font-light leading-relaxed text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Visual Feature Stats ───────────────────────────────────────────────────
function StatsSection() {
  return (
    <section className="px-6 md:px-16 py-28 max-w-[1400px] mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6" style={{ minHeight: '420px' }}>
        {/* Left — "Quiet luxury" card */}
        <div className="md:col-span-7 rounded-[2rem] overflow-hidden relative group" style={{ minHeight: '400px' }}>
          <div className="absolute inset-0" style={{ backgroundColor: '#0c0c0c' }}>
            <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at 20% 80%, rgba(167,203,235,0.06), transparent 60%)' }} />
            <div
              className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: 'linear-gradient(rgba(37,38,38,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(37,38,38,0.6) 1px, transparent 1px)',
                backgroundSize: '40px 40px',
              }}
            />
          </div>
          <div className="absolute inset-0" style={{ background: 'linear-gradient(to top, black 0%, rgba(0,0,0,0.4) 50%, transparent 100%)' }} />
          <div className="absolute bottom-12 left-12 max-w-sm">
            <span className="text-[9px] uppercase tracking-[0.35em] font-semibold block mb-3" style={{ color: '#a7cbeb' }}>
              Design Principles
            </span>
            <h3 className="text-3xl font-bold tracking-tighter text-white mb-4">
              Quiet luxury for the digital asset era.
            </h3>
            <button className="text-sm font-bold tracking-widest uppercase flex items-center gap-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
              The Manifesto
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </button>
          </div>
        </div>

        {/* Right — Stat cards */}
        <div className="md:col-span-5 flex flex-col gap-5">
          {[
            { value: '$14B+', label: 'Assets Tracked Annually' },
            { value: '1.2M', label: 'Daily Intelligence Signals' },
          ].map((stat) => (
            <div
              key={stat.value}
              className="flex-1 rounded-[2rem] p-10 flex flex-col justify-center"
              style={{ backgroundColor: '#0e0e0e', border: '1px solid rgba(255,255,255,0.04)' }}
            >
              <div className="text-5xl font-black tracking-tighter text-white mb-2">{stat.value}</div>
              <div className="text-[10px] uppercase tracking-[0.25em] font-semibold" style={{ color: '#525252' }}>{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Built for Signal Section ───────────────────────────────────────────────
function PhilosophySection() {
  return (
    <section className="py-24" style={{ backgroundColor: '#070707' }}>
      <div className="max-w-6xl mx-auto px-6 md:px-16">
        <div className="flex flex-col md:flex-row items-end justify-between gap-8 mb-16">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tighter text-white leading-[0.95]">
            Built for those who<br />demand more than noise.
          </h2>
          <div className="flex gap-12">
            {[
              { label: 'Assets Tracked', value: '$14B+' },
              { label: 'Daily Signals', value: '1.2M' },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="text-3xl font-black tracking-tighter text-white">{value}</div>
                <div className="text-[9px] uppercase tracking-[0.25em] mt-1" style={{ color: '#525252' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
        <p className="text-neutral-500 font-light max-w-lg text-sm leading-relaxed">
          Signals Zen operates at the intersection of quantitative finance and editorial excellence. We distill complexity into clarity.
        </p>
      </div>
    </section>
  );
}

// ─── CTA ────────────────────────────────────────────────────────────────────
function CTASection() {
  return (
    <section className="px-6 py-36">
      <div className="max-w-4xl mx-auto text-center">
        <h2
          className="font-bold tracking-tighter text-white mb-8"
          style={{ fontSize: 'clamp(3rem, 8vw, 6rem)', lineHeight: '0.93', letterSpacing: '-0.04em' }}
        >
          Transcend the volatility.
        </h2>
        <p className="text-lg text-neutral-400 font-light leading-relaxed mb-14 max-w-xl mx-auto">
          Join an exclusive network of curators leveraging the world&#39;s most sophisticated on-chain intelligence platform.
        </p>
        <Link
          href="/dashboard"
          className="inline-block px-14 py-5 rounded-full font-black text-base tracking-tight hover:scale-[1.03] transition-all active:scale-95"
          style={{ backgroundColor: 'white', color: 'black', boxShadow: '0 25px 60px -15px rgba(255,255,255,0.12)' }}
        >
          Request Early Access
        </Link>
      </div>
    </section>
  );
}

// ─── Footer ────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer style={{ backgroundColor: '#000', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
      <div className="max-w-7xl mx-auto px-8 md:px-16 py-16 flex flex-col md:flex-row justify-between items-center gap-10">
        <div className="space-y-2 text-center md:text-left">
          <div className="text-base font-bold tracking-tighter text-white">Signals Zen</div>
          <p className="text-[10px] uppercase tracking-[0.2em] font-light" style={{ color: '#404040' }}>
            © 2024 Signals Zen Editorial. Crafted for the sovereign mind.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-8 text-[10px] uppercase tracking-[0.25em] font-semibold" style={{ color: '#404040' }}>
          {['Privacy', 'Terms', 'Intelligence', 'Changelog'].map((link) => (
            <a key={link} href="#" className="hover:text-white transition-colors">{link}</a>
          ))}
        </div>
        <div className="flex gap-4">
          {[
            <svg key="s" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>,
            <svg key="h" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" /></svg>,
          ].map((icon, i) => (
            <button key={i} className="cursor-pointer transition-colors" style={{ color: '#404040' }}
              onMouseEnter={e => (e.currentTarget.style.color = '#a7cbeb')}
              onMouseLeave={e => (e.currentTarget.style.color = '#404040')}
            >
              {icon}
            </button>
          ))}
        </div>
      </div>
    </footer>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div style={{ backgroundColor: '#0e0e0e', color: '#e7e5e5' }}>
      <Navbar />
      <main>
        <HeroSection />
        <ProvenSection />
        <TrustSection />
        <StatsSection />
        <PhilosophySection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
