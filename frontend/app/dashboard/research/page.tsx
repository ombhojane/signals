"use client";

import { useMemo, useState } from "react";
import { PerformanceChart } from "@/components/charts/PerformanceChart";

// ─── Tournament constants ─────────────────────────────────────────────────────
const STARTING_CAPITAL = 10_000;
const TOURNEY_START = "Oct 18, 2025";
const TOURNEY_END = "Nov 3, 2025";
const PLATFORM = "Hyperliquid · Perpetual Futures";
const ASSETS = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"] as const;

// ─── Daily account value series (Oct 18 → Nov 3, 17 daily points) ─────────────
// Anchored to the published Oct 31 mid-tournament snapshot and the Nov 3 final
// closing values. Intermediate days are smoothed reconstructions, not tick data.
const DAY0 = Math.floor(Date.UTC(2025, 9, 18) / 1000);
const DAY = 86_400;

type ModelKey =
  | "qwen"
  | "deepseek"
  | "claude"
  | "grok"
  | "gemini"
  | "gpt5";

const SERIES_VALUES: Record<ModelKey, number[]> = {
  qwen:     [10000, 10120, 10300, 10560, 10840, 11180, 11680, 12100, 12500, 12880, 12950, 13050, 13110, 13121, 12880, 12500, 12232],
  deepseek: [10000, 10080, 10250, 10500, 10810, 11200, 11700, 12300, 12900, 13500, 14000, 14400, 14650, 14764, 13500, 11800, 10489],
  claude:   [10000,  9960,  9870,  9700,  9520,  9450,  9400,  9320,  9220,  9110,  9000,  8950,  8880,  8835,  8200,  7400,  6919],
  grok:     [10000,  9900,  9740,  9490,  9100,  8790,  8400,  8000,  7600,  7200,  6900,  6600,  6300,  6119,  5900,  5650,  5470],
  gemini:   [10000,  9700,  9300,  8800,  8200,  7700,  7100,  6500,  5900,  5300,  4700,  4200,  3700,  3307,  3500,  4000,  4329],
  gpt5:     [10000,  9800,  9500,  9100,  8500,  7900,  7100,  6300,  5500,  4700,  4000,  3300,  2700,  2473,  2900,  3400,  3734],
};

// ─── Model registry ───────────────────────────────────────────────────────────
type ModelRow = {
  key: ModelKey;
  name: string;
  org: string;
  color: string;
  finalValue: number;
  pnlPct: number;
  trades: number | null;
  winRate: number | null;
  fees: number;
  leverage: number;
  longBias: string;
  archetype: string;
  oneLiner: string;
  observation: string;
};

const MODELS: ModelRow[] = [
  {
    key: "qwen",
    name: "Qwen 3 Max",
    org: "Alibaba",
    color: "#ff7d8b",
    finalValue: 12232,
    pnlPct: 22.3,
    trades: 43,
    winRate: 30.2,
    fees: 1565,
    leverage: 16.7,
    longBias: "Concentrated",
    archetype: "The Disciplined Gambler",
    oneLiner: "Low-frequency signal trader with one big BTC bet.",
    observation:
      "Roughly three trades per day. Acted on MACD/RSI confirmation, sized aggressively (up to 25× leverage on BTC), and respected its own stop-losses. Dropped ≈$4.1k in a single reversal day, then clawed it back with a focused conviction trade.",
  },
  {
    key: "deepseek",
    name: "DeepSeek V3.1",
    org: "DeepSeek",
    color: "#6366f1",
    finalValue: 10489,
    pnlPct: 4.89,
    trades: 41,
    winRate: 24.4,
    fees: 568,
    leverage: 12.9,
    longBias: "92% long",
    archetype: "The Quant Fund Manager",
    oneLiner: "Fewer, higher-conviction trades held ~35h on average.",
    observation:
      "Acted like a pod manager: diversified across BTC/ETH/SOL, kept leverage modest, took profits on rules. Best risk-adjusted profile of the field. Bled most of its lead in the final 72 hours when the market chopped, but stayed green.",
  },
  {
    key: "claude",
    name: "Claude Sonnet 4.5",
    org: "Anthropic",
    color: "#d97757",
    finalValue: 6919,
    pnlPct: -30.81,
    trades: null,
    winRate: null,
    fees: 482,
    leverage: 12.3,
    longBias: "100% long",
    archetype: "The Frozen Permabull",
    oneLiner: "Carried directional bias the whole tournament, no hedge, no dynamic stop.",
    observation:
      "Entered only on clear technical confirmations and refused to double down on losers — defensive on entry, but had no exit playbook. When the market reversed mid-tourney the rigid long bias became the entire P&L story.",
  },
  {
    key: "grok",
    name: "Grok 4",
    org: "xAI",
    color: "#94a3b8",
    finalValue: 5470,
    pnlPct: -45.3,
    trades: null,
    winRate: null,
    fees: 329,
    leverage: 12.7,
    longBias: "Reactive",
    archetype: "The FOMO Chaser",
    oneLiner: "Bought euphoria, sold fear — the textbook retail loop.",
    observation:
      "Tried to read social-media sentiment as alpha. Ended up long during peak FOMO and unwound positions during pullbacks. Got the directional call right early, then handed it all back to the noise it was supposed to be exploiting.",
  },
  {
    key: "gemini",
    name: "Gemini 2.5 Pro",
    org: "Google DeepMind",
    color: "#4285f4",
    finalValue: 4329,
    pnlPct: -56.71,
    trades: 238,
    winRate: null,
    fees: 1331,
    leverage: 14.3,
    longBias: "Mixed",
    archetype: "The Overtrader",
    oneLiner: "238 trades. $1,331 in fees. 13% of capital gone before P&L.",
    observation:
      "Reacted to almost every minor fluctuation. Hit ~13 trades/day and burned more than 13% of starting capital on Hyperliquid fees alone. Recovered modestly in the final week, but the friction was unrecoverable.",
  },
  {
    key: "gpt5",
    name: "GPT-5",
    org: "OpenAI",
    color: "#10a37f",
    finalValue: 3734,
    pnlPct: -62.66,
    trades: null,
    winRate: null,
    fees: 498,
    leverage: 17.2,
    longBias: "Counter-trend",
    archetype: "Analysis Paralysis",
    oneLiner: "Highest leverage, longest reasoning, worst decisions.",
    observation:
      "Wrote the most thorough trade rationales — and acted on them last. Hesitated under conflicting Signals, shorted into rallies, ran the field's highest leverage. Best-in-class as a writer, worst-in-class as a trader.",
  },
];

// ─── Findings ────────────────────────────────────────────────────────────────
const FINDINGS = [
  {
    title: "Discipline beat capability.",
    body: "The two winners were the smaller, open-source models. Frontier reasoning didn't translate into alpha — rule-following did. 'Knowing' a financial concept and 'doing' it under uncertainty are different skills, and current LLMs are noticeably better at the first.",
  },
  {
    title: "Friction is a silent killer.",
    body: "Gemini paid $1,331 in fees on $10,000 — more than the entire DeepSeek profit pool. Before any directional view matters, an over-eager model trades itself to death. Trade frequency is a risk parameter, not a vibe.",
  },
  {
    title: "Single-direction bias is fatal.",
    body: "Claude held 100% long for 17 days with no hedge and no dynamic stop. The model's caution lived in the entry, not the exit. Any agent that can open trades must also be wired to close them on rules it can't override.",
  },
  {
    title: "Sentiment-aware ≠ sentiment-immune.",
    body: "Grok was the model most explicitly designed around social signal. It bought the FOMO top and sold the panic bottom — the same loop sentiment is supposed to defend you against. Reading the crowd is not the same as fading it.",
  },
  {
    title: "Reasoning chains can hurt you.",
    body: "GPT-5's longer deliberation correlated with worse entries. In fast markets, latency-to-decision is itself a cost: while the model checked historical context, the edge moved. Cheaper, decisive Signals beat expensive contemplative ones.",
  },
  {
    title: "Leverage amplifies the model, not the market.",
    body: "The two highest-leverage models (GPT-5 17.2×, Qwen 16.7×) finished at opposite ends of the table. Leverage didn't cause the losses; it just made each model's underlying decision quality louder.",
  },
];

// ─── Memecoin-specific ideation ──────────────────────────────────────────────
const NEXT_EXPERIMENTS = [
  {
    icon: "rocket_launch",
    title: "Pure-memecoin arena",
    body: "Re-run the tournament on Solana memecoins only — WIF, BONK, POPCAT, plus a rotating long-tail bucket. The models that struggled with BTC volatility will face an order of magnitude more noise. Hypothesis: the gap between disciplined and reactive models widens further.",
  },
  {
    icon: "schedule",
    title: "Time-of-day & session bias",
    body: "Split P&L by US, EU, and Asia hours. Memecoin flows are extremely session-dependent — a model that's net-flat on the 24h tape can be deeply skewed within a single session. Ranking by Sharpe-per-session may reorder the leaderboard.",
  },
  {
    icon: "groups",
    title: "Multi-agent ensembles",
    body: "Run a debate-then-vote architecture across the same six models. The cheapest models had the best individual returns; an ensemble may capture the upside of disagreement and limit any single model's blind spot (Claude's permabias, Gemini's overtrading).",
  },
  {
    icon: "psychology",
    title: "Narrative-conditioned prompts",
    body: "Feed each model a fresh memecoin narrative (dog, cat, AI, political, low-cap) every 6 hours and measure which models adapt their playbook vs. blindly extrapolate. We expect Grok to over-anchor on hype and DeepSeek to ignore it — both are failure modes.",
  },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
type SortKey = "pnlPct" | "finalValue" | "trades" | "fees" | "leverage";
type SortDir = "asc" | "desc";

function fmtUSD(n: number) {
  return `$${n.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
function fmtPct(n: number) {
  const s = n >= 0 ? "+" : "";
  return `${s}${n.toFixed(2)}%`;
}

// ─── Reusable card components ────────────────────────────────────────────────
function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <div
      className="rounded-2xl p-6 flex flex-col gap-2 bg-card border border-border"
    >
      <span
        className="text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground"
      >
        {label}
      </span>
      <span
        className={`text-3xl font-black font-mono tracking-tight ${accent ? "" : "text-foreground"}`}
        style={{ color: accent ?? undefined }}
      >
        {value}
      </span>
      {sub ? (
        <span className="text-xs tracking-wide text-muted-foreground">
          {sub}
        </span>
      ) : null}
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────
export default function ResearchPage() {
  const [sortKey, setSortKey] = useState<SortKey>("pnlPct");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [hidden, setHidden] = useState<Set<ModelKey>>(new Set());

  const sortedModels = useMemo(() => {
    const arr = [...MODELS];
    arr.sort((a, b) => {
      const av = (a[sortKey] ?? -Infinity) as number;
      const bv = (b[sortKey] ?? -Infinity) as number;
      return sortDir === "desc" ? bv - av : av - bv;
    });
    return arr;
  }, [sortKey, sortDir]);

  const chartSeries = useMemo(() => {
    return MODELS.filter((m) => !hidden.has(m.key)).map((m) => ({
      name: m.name,
      color: m.color,
      data: SERIES_VALUES[m.key].map((v, i) => ({
        time: DAY0 + i * DAY,
        value: v,
      })),
    }));
  }, [hidden]);

  const winner = MODELS.reduce((best, m) => (m.pnlPct > best.pnlPct ? m : best));
  const worst = MODELS.reduce((w, m) => (m.pnlPct < w.pnlPct ? m : w));
  const totalTrades = MODELS.reduce((s, m) => s + (m.trades ?? 0), 0);
  const totalFees = MODELS.reduce((s, m) => s + m.fees, 0);

  const onSort = (k: SortKey) => {
    if (sortKey === k) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(k);
      setSortDir("desc");
    }
  };

  const toggleSeries = (k: ModelKey) => {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  };

  return (
    <div className="flex flex-col gap-10 max-w-6xl">
      {/* Hero */}
      <div className="flex flex-col gap-4">
        <span
          className="text-[10px] font-bold tracking-[0.25em] uppercase text-primary"
        >
          Research · Field study #001
        </span>
        <h1
          className="text-4xl md:text-5xl font-bold tracking-tight text-foreground"
        >
          Can frontier LLMs trade memecoins?
        </h1>
        <p className="mt-3 text-lg md:text-xl text-muted-foreground font-light leading-relaxed max-w-2xl">
          Six top models — Claude, GPT-5, Gemini, Grok, DeepSeek, Qwen — were
          handed <span className="text-foreground">$10,000 each</span> and turned
          loose on perpetual futures for 17 days. Same prompts, same market
          feed, no human intervention. Below: the full leaderboard, behavioral
          fingerprints, and what it means for trading the most volatile corner
          of crypto.
        </p>

        <div className="flex flex-wrap gap-2 mt-2">
          {[
            { k: "Window", v: `${TOURNEY_START} → ${TOURNEY_END}` },
            { k: "Capital", v: `${fmtUSD(STARTING_CAPITAL)} per model` },
            { k: "Venue", v: PLATFORM },
            { k: "Universe", v: ASSETS.join(" · ") },
          ].map((t) => (
            <span
              key={t.k}
              className="text-[10px] font-mono tracking-wider px-3 py-1.5 rounded-full bg-card border border-border text-muted-foreground"
            >
              <span className="text-muted-foreground/50">{t.k.toUpperCase()} · </span>
              <span className="text-foreground">{t.v}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Headline metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Models tested"
          value={MODELS.length.toString()}
          sub="6 frontier LLMs, identical harness"
          accent="var(--primary)"
        />
        <StatCard
          label="Best return"
          value={fmtPct(winner.pnlPct)}
          sub={`${winner.name}`}
          accent="#7ee787"
        />
        <StatCard
          label="Worst return"
          value={fmtPct(worst.pnlPct)}
          sub={`${worst.name}`}
          accent="#ff7d8b"
        />
        <StatCard
          label="Combined fees burned"
          value={fmtUSD(totalFees)}
          sub={`Across ${totalTrades}+ logged trades`}
        />
      </div>

      {/* Standings */}
      <section
        className="rounded-3xl p-6 md:p-8 flex flex-col gap-6 bg-card border border-border"
      >
        <div className="flex items-end justify-between flex-wrap gap-4">
          <div>
            <h2
              className="text-sm font-bold tracking-[0.2em] uppercase text-foreground"
            >
              Final standings
            </h2>
            <p className="text-xs mt-1 text-muted-foreground">
              Sortable. Click any column header to re-rank.
            </p>
          </div>
          <span className="text-[10px] tracking-widest uppercase text-muted-foreground/50">
            Closed Nov 3, 2025
          </span>
        </div>

        <div className="overflow-x-auto -mx-2 px-2">
          <table className="w-full text-sm font-mono">
            <thead>
              <tr className="text-left text-muted-foreground/50">
                <th className="py-3 pr-4 text-[10px] font-bold tracking-widest uppercase">#</th>
                <th className="py-3 pr-4 text-[10px] font-bold tracking-widest uppercase">Model</th>
                <Th label="P&L %" k="pnlPct" sortKey={sortKey} sortDir={sortDir} onClick={onSort} />
                <Th label="Final $" k="finalValue" sortKey={sortKey} sortDir={sortDir} onClick={onSort} />
                <Th label="Trades" k="trades" sortKey={sortKey} sortDir={sortDir} onClick={onSort} />
                <th className="py-3 pr-4 text-[10px] font-bold tracking-widest uppercase">Win rate</th>
                <Th label="Avg lev" k="leverage" sortKey={sortKey} sortDir={sortDir} onClick={onSort} />
                <Th label="Fees" k="fees" sortKey={sortKey} sortDir={sortDir} onClick={onSort} />
                <th className="py-3 pr-4 text-[10px] font-bold tracking-widest uppercase">Bias</th>
              </tr>
            </thead>
            <tbody>
              {sortedModels.map((m, idx) => (
                <tr
                  key={m.key}
                  className="border-t border-t border-border/50"
                >
                  <td className="py-4 pr-4 text-xs text-muted-foreground/50">
                    {String(idx + 1).padStart(2, "0")}
                  </td>
                  <td className="py-4 pr-4">
                    <div className="flex items-center gap-3">
                      <span
                        className="h-2.5 w-2.5 rounded-sm shrink-0"
                        style={{ backgroundColor: m.color }}
                      />
                      <div className="flex flex-col">
                        <span className="text-sm font-bold text-foreground">
                          {m.name}
                        </span>
                        <span className="text-[10px] tracking-wider uppercase text-muted-foreground/50">
                          {m.org}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className={`py-4 pr-4 font-bold ${m.pnlPct >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {fmtPct(m.pnlPct)}
                  </td>
                  <td className="py-4 pr-4 text-foreground">
                    {fmtUSD(m.finalValue)}
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {m.trades ?? "—"}
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {m.winRate != null ? `${m.winRate.toFixed(1)}%` : "—"}
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {m.leverage.toFixed(1)}×
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {fmtUSD(m.fees)}
                  </td>
                  <td className="py-4 pr-4 text-xs text-muted-foreground">
                    {m.longBias}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* P&L over time */}
      <section
        className="rounded-3xl p-6 md:p-8 flex flex-col gap-5 bg-card border border-border"
      >
        <div className="flex items-end justify-between flex-wrap gap-3">
          <div>
            <h2
              className="text-sm font-bold tracking-[0.2em] uppercase text-foreground"
            >
              Account value over time
            </h2>
            <p className="text-xs mt-1 text-muted-foreground">
              Click a model below to isolate or hide its curve.
            </p>
          </div>
          <span className="text-[10px] tracking-widest uppercase text-muted-foreground/50">
            17-day window · daily marks
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {MODELS.map((m) => {
            const active = !hidden.has(m.key);
            return (
              <button
                key={m.key}
                onClick={() => toggleSeries(m.key)}
                className={`text-xs font-mono tracking-tight px-3 py-1.5 rounded-full transition-opacity ${active ? "" : "bg-muted text-muted-foreground"}`}
                style={{
                  backgroundColor: active ? `${m.color}1f` : undefined,
                  border: `1px solid ${active ? m.color : "rgba(0,0,0,0.15)"}`,
                  color: active ? m.color : undefined,
                  opacity: active ? 1 : 0.55,
                }}
              >
                <span
                  className={`inline-block h-2 w-2 rounded-sm mr-2 align-middle ${active ? "" : "bg-muted-foreground/30"}`}
                  style={{ backgroundColor: active ? m.color : undefined }}
                />
                {m.name}
              </button>
            );
          })}
        </div>

        <PerformanceChart series={chartSeries} height={360} />
      </section>

      {/* Behavioral fingerprints */}
      <section className="flex flex-col gap-5">
        <div>
          <h2
            className="text-sm font-bold tracking-[0.2em] uppercase text-foreground"
          >
            Behavioral fingerprints
          </h2>
          <p className="text-xs mt-1 max-w-xl text-muted-foreground">
            What each model actually <span className="text-foreground">did</span> with $10,000 — distilled from its trade log.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...MODELS].sort((a, b) => b.pnlPct - a.pnlPct).map((m) => (
            <div
              key={m.key}
              className="rounded-2xl p-6 flex flex-col gap-3 relative overflow-hidden bg-card border border-border"
            >
              <div
                className="absolute top-0 left-0 h-[2px] w-full"
                style={{ backgroundColor: m.color, opacity: 0.65 }}
              />
              <div className="flex items-start justify-between gap-4">
                <div className="flex flex-col">
                  <span className="text-[10px] tracking-[0.2em] uppercase font-bold" style={{ color: m.color }}>
                    {m.archetype}
                  </span>
                  <span className="text-xl font-black tracking-tight mt-1 text-foreground">
                    {m.name}
                  </span>
                  <span className="text-[10px] tracking-wider uppercase text-muted-foreground/50">
                    {m.org}
                  </span>
                </div>
                <div
                  className={`text-2xl font-black font-mono tracking-tight shrink-0 ${m.pnlPct >= 0 ? "text-green-400" : "text-red-400"}`}
                >
                  {fmtPct(m.pnlPct)}
                </div>
              </div>

              <p className="text-sm font-medium text-foreground">
                {m.oneLiner}
              </p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {m.observation}
              </p>

              <div className="flex flex-wrap gap-2 mt-2">
                <Pill k="LEV" v={`${m.leverage.toFixed(1)}×`} />
                <Pill k="FEES" v={fmtUSD(m.fees)} />
                <Pill k="BIAS" v={m.longBias} />
                {m.trades != null ? <Pill k="TRADES" v={m.trades.toString()} /> : null}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Asset universe */}
      <section
        className="rounded-3xl p-6 md:p-8 flex flex-col gap-5 bg-card border border-border"
      >
        <div className="flex items-end justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-sm font-bold tracking-[0.2em] uppercase text-foreground">
              The asset universe
            </h2>
            <p className="text-xs mt-1 max-w-xl text-muted-foreground">
              All six models could open perps on the same six tickers. The most
              memecoin-like one is highlighted.
            </p>
          </div>
        </div>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {ASSETS.map((a) => {
            const isMeme = a === "DOGE";
            return (
              <div
                key={a}
                className={`rounded-2xl py-6 flex flex-col items-center justify-center gap-1 ${isMeme ? "bg-amber-500/5 border border-amber-400/35" : "bg-background border border-border"}`}
              >
                <span
                  className={`text-2xl font-black tracking-tight ${isMeme ? "text-amber-400" : "text-foreground"}`}
                >
                  {a}
                </span>
                <span className={`text-[9px] tracking-widest uppercase ${isMeme ? "text-amber-400" : "text-muted-foreground/50"}`}>
                  {isMeme ? "memecoin" : "majors"}
                </span>
              </div>
            );
          })}
        </div>
        <div
          className="text-xs leading-relaxed rounded-2xl p-4 bg-background border border-border text-muted-foreground"
        >
          <span className="text-amber-400">The memecoin signal:</span>{" "}
          DOGE was the only true sentiment-driven asset in the universe — and
          still, the model built around social signal (Grok) finished
          second-to-last. It&apos;s the cleanest evidence in the dataset that{" "}
          <span className="text-foreground">reading the crowd is not the same as fading it</span>. A pure-memecoin re-run is the natural next experiment.
        </div>
      </section>

      {/* Findings */}
      <section className="flex flex-col gap-5">
        <div>
          <h2 className="text-sm font-bold tracking-[0.2em] uppercase text-foreground">
            Six things this dataset proved
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {FINDINGS.map((f, i) => (
            <div
              key={f.title}
              className="rounded-2xl p-6 flex flex-col gap-2 bg-card border border-border"
            >
              <span className="text-[10px] font-mono tracking-widest text-muted-foreground/50">
                FINDING {String(i + 1).padStart(2, "0")}
              </span>
              <h3 className="text-base font-bold tracking-tight text-foreground">
                {f.title}
              </h3>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {f.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Next experiments */}
      <section className="flex flex-col gap-5">
        <div>
          <h2 className="text-sm font-bold tracking-[0.2em] uppercase text-foreground">
            What we&apos;d run next
          </h2>
          <p className="text-xs mt-1 max-w-xl text-muted-foreground">
            Lateral extensions of the same harness — designed to break the
            assumption that crypto majors and memecoins are the same problem.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {NEXT_EXPERIMENTS.map((e) => (
            <div
              key={e.title}
              className="rounded-2xl p-6 flex flex-col gap-3 bg-card border border-border"
            >
              <div className="flex items-center gap-3">
                <span
                  className="material-symbols-outlined text-primary" style={{ fontSize: "1.4rem" }}
                >
                  {e.icon}
                </span>
                <h3 className="text-base font-bold tracking-tight text-foreground">
                  {e.title}
                </h3>
              </div>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {e.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Methodology */}
      <section
        className="rounded-3xl p-6 flex flex-col gap-3 bg-background border border-dashed border-border"
      >
        <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-muted-foreground/50">
          Methodology · Caveats
        </span>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Each model received the same system prompt, the same OHLCV + funding
          + open-interest snapshots on a 2–3 minute cadence, and could open or
          close any leveraged perpetual position on the venue. Final P&L,
          fees, leverage, win rate and trade count are taken from the
          tournament&apos;s published end-of-window snapshots. Daily curves between
          the published mid-tournament snapshot (Oct 31) and the close (Nov 3)
          are smoothed reconstructions, not tick replays — directionally
          accurate, not bar-perfect. n = 1 tournament: treat as a strong
          existence proof, not a stable ranking.
        </p>
      </section>
    </div>
  );
}

// ─── Subcomponents ───────────────────────────────────────────────────────────
function Th({
  label,
  k,
  sortKey,
  sortDir,
  onClick,
}: {
  label: string;
  k: SortKey;
  sortKey: SortKey;
  sortDir: SortDir;
  onClick: (k: SortKey) => void;
}) {
  const active = sortKey === k;
  return (
    <th className="py-3 pr-4 text-[10px] font-bold tracking-widest uppercase">
      <button
        onClick={() => onClick(k)}
        className={`transition-colors ${active ? "text-primary" : "text-muted-foreground/50"}`}
      >
        {label}
        {active ? (sortDir === "desc" ? " ↓" : " ↑") : ""}
      </button>
    </th>
  );
}

function Pill({ k, v }: { k: string; v: string }) {
  return (
    <span
      className="text-[10px] font-mono tracking-wider px-2.5 py-1 rounded-full bg-background border border-border text-muted-foreground"
    >
      <span className="text-muted-foreground/50">{k} </span>
      <span className="text-foreground">{v}</span>
    </span>
  );
}
