"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useScanState } from "@/lib/contexts/ScanContext";
import { TokenSkeleton, FilterSkeleton, StatsPillarSkeleton } from "@/components/ui/skeleton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- Event + state types ---------------------------------------------------

type ScanEvent = {
  type: string;
  [key: string]: unknown;
};

type AgentName = "market_agent" | "rug_check_agent" | "social_agent" | "predictor";

type AgentState = {
  status: "idle" | "start" | "ok" | "error";
  duration_ms?: number;
  score?: number;
  confidence?: number;
  red_flags?: string[];
  error?: string | null;
  analysis?: Record<string, unknown> | null;
};

type PhaseName = "plan" | "fetch" | "preprocess" | "ai" | "scoring" | "predict";

type PhaseState = {
  status: "pending" | "start" | "done";
  duration_ms?: number;
  extra?: Record<string, unknown>;
};

type TokenState = {
  index: number;
  address: string;
  symbol: string;
  name?: string;
  price?: number;
  volume_24h?: number;
  liquidity?: number;
  market_cap?: number;
  phases: Record<PhaseName, PhaseState>;
  agents: Record<AgentName, AgentState>;
  signal_vector?: Record<string, unknown>;
  killswitch?: { triggered: boolean; rule?: string | null; message?: string | null };
  result?: Record<string, unknown>;
  done: boolean;
};

type FilterRow = {
  address: string;
  symbol: string | null;
  passed: boolean;
  reason: string;
  price?: number;
  volume_24h?: number;
  liquidity?: number;
  market_cap?: number;
};

type ScanWarning = {
  code: string;
  message: string;
};

type ScanState = {
  running: boolean;
  run_id?: string;
  started_at?: string;
  elapsed_seconds?: number;
  discovered?: number;
  filtered?: number;
  analyzed?: number;
  filters: FilterRow[];
  tokens: TokenState[];
  summary?: Record<string, unknown>;
  warnings: ScanWarning[];
  error?: string;
};

const INITIAL_AGENTS: Record<AgentName, AgentState> = {
  market_agent: { status: "idle" },
  rug_check_agent: { status: "idle" },
  social_agent: { status: "idle" },
  predictor: { status: "idle" },
};

const INITIAL_PHASES: Record<PhaseName, PhaseState> = {
  plan: { status: "pending" },
  fetch: { status: "pending" },
  preprocess: { status: "pending" },
  ai: { status: "pending" },
  scoring: { status: "pending" },
  predict: { status: "pending" },
};

const PHASE_ORDER: PhaseName[] = [
  "plan", "fetch", "preprocess", "ai", "scoring", "predict",
];

const AGENT_LABELS: Record<AgentName, { label: string; icon: string; color: string }> = {
  market_agent: { label: "Market",    icon: "show_chart",       color: "text-sky-400" },
  rug_check_agent: { label: "Rug Check", icon: "shield",        color: "text-amber-400" },
  social_agent: { label: "Social",    icon: "forum",            color: "text-fuchsia-400" },
  predictor: { label: "Predictor",    icon: "psychology",       color: "text-emerald-400" },
};

// --- Reducer ---------------------------------------------------------------

function applyEvent(state: ScanState, ev: ScanEvent): ScanState {
  switch (ev.type) {
    case "scan.start":
      return {
        running: true,
        run_id: String(ev.run_id),
        started_at: String(ev.started_at),
        filters: [],
        tokens: [],
        warnings: [],
      };
    case "scan.warning":
      return {
        ...state,
        warnings: [
          ...state.warnings,
          { code: String(ev.code), message: String(ev.message) },
        ],
      };
    case "discover.done":
      return { ...state, discovered: Number(ev.count) };
    case "filter":
      return {
        ...state,
        filters: [
          ...state.filters,
          {
            address: String(ev.address),
            symbol: (ev.symbol as string | null) ?? null,
            passed: Boolean(ev.passed),
            reason: String(ev.reason),
            price: ev.price as number | undefined,
            volume_24h: ev.volume_24h as number | undefined,
            liquidity: ev.liquidity as number | undefined,
            market_cap: ev.market_cap as number | undefined,
          },
        ],
      };
    case "filter.done":
      return {
        ...state,
        filtered: Number(ev.survived),
      };
    case "token.start": {
      const token: TokenState = {
        index: Number(ev.index),
        address: String(ev.address),
        symbol: String(ev.symbol ?? "?"),
        name: ev.name as string | undefined,
        price: ev.price as number | undefined,
        volume_24h: ev.volume_24h as number | undefined,
        liquidity: ev.liquidity as number | undefined,
        market_cap: ev.market_cap as number | undefined,
        phases: { ...INITIAL_PHASES },
        agents: { ...INITIAL_AGENTS },
        done: false,
      };
      return { ...state, tokens: [...state.tokens, token] };
    }
    case "phase": {
      const name = ev.name as PhaseName;
      const status = ev.status as "start" | "done";
      return patchLastToken(state, t => ({
        ...t,
        phases: {
          ...t.phases,
          [name]: {
            ...t.phases[name],
            status,
            duration_ms: (ev.duration_ms as number | undefined) ?? t.phases[name].duration_ms,
            extra: { ...t.phases[name].extra, ...ev },
          },
        },
      }));
    }
    case "agent": {
      const name = ev.name as AgentName;
      const status = ev.status as "start" | "ok" | "error";
      return patchLastToken(state, t => ({
        ...t,
        agents: {
          ...t.agents,
          [name]: {
            status,
            duration_ms: ev.duration_ms as number | undefined,
            score: ev.score as number | undefined,
            confidence: ev.confidence as number | undefined,
            red_flags: ev.red_flags as string[] | undefined,
            error: ev.error as string | null | undefined,
            analysis: ev.analysis as Record<string, unknown> | null | undefined,
          },
        },
      }));
    }
    case "killswitch":
      return patchLastToken(state, t => ({
        ...t,
        killswitch: {
          triggered: Boolean(ev.triggered),
          rule: ev.rule as string | null | undefined,
          message: ev.message as string | null | undefined,
        },
      }));
    case "signal_vector":
      return patchLastToken(state, t => ({
        ...t,
        signal_vector: ev as Record<string, unknown>,
      }));
    case "token.done":
      return patchLastToken(state, t => ({
        ...t,
        done: true,
        result: ev.result as Record<string, unknown>,
      }));
    case "token.error":
      return patchLastToken(state, t => ({ ...t, done: true }));
    case "scan.done":
      return {
        ...state,
        running: false,
        discovered: Number(ev.discovered ?? state.discovered ?? 0),
        filtered: Number(ev.filtered ?? state.filtered ?? 0),
        analyzed: Number(ev.analyzed ?? state.analyzed ?? 0),
        elapsed_seconds: Number(ev.elapsed_seconds),
        summary: ev.summary as Record<string, unknown>,
      };
    case "error":
      return { ...state, running: false, error: String(ev.message) };
    default:
      return state;
  }
}

function patchLastToken(
  state: ScanState,
  patch: (t: TokenState) => TokenState,
): ScanState {
  if (state.tokens.length === 0) return state;
  const tokens = [...state.tokens];
  tokens[tokens.length - 1] = patch(tokens[tokens.length - 1]);
  return { ...state, tokens };
}

// --- Small UI atoms --------------------------------------------------------

function StatPill({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1 px-4 py-3 rounded-lg border border-white/5 bg-white/[0.02]">
      <span className="text-[10px] uppercase tracking-[0.18em] text-neutral-500">{label}</span>
      <span className="text-lg font-semibold text-white tabular-nums">{value}</span>
    </div>
  );
}

function PhaseStep({
  name, phase, active,
}: { name: PhaseName; phase: PhaseState; active: boolean }) {
  const done = phase.status === "done";
  const running = phase.status === "start";
  return (
    <div className={cn(
      "flex items-center gap-2 rounded-md px-2.5 py-1.5 text-[11px] font-medium",
      done && "bg-emerald-500/10 text-emerald-300",
      running && "bg-sky-500/10 text-sky-300 animate-pulse",
      !done && !running && "text-neutral-500 bg-white/[0.02]",
      active && !done && !running && "ring-1 ring-white/10",
    )}>
      <span className="material-symbols-outlined text-[14px]">
        {done ? "check_circle" : running ? "progress_activity" : "radio_button_unchecked"}
      </span>
      <span className="capitalize">{name}</span>
      {typeof phase.duration_ms === "number" && (
        <span className="text-neutral-500 tabular-nums">{phase.duration_ms.toFixed(0)}ms</span>
      )}
    </div>
  );
}

function AgentCard({
  name, state,
}: { name: AgentName; state: AgentState }) {
  const meta = AGENT_LABELS[name];
  const statusColor = {
    idle: "bg-white/[0.02] text-neutral-500",
    start: "bg-sky-500/10 text-sky-300 animate-pulse",
    ok: "bg-emerald-500/10 text-emerald-300",
    error: "bg-rose-500/10 text-rose-300",
  }[state.status];

  return (
    <div className={cn("rounded-lg border border-white/5 p-3 flex flex-col gap-2", statusColor)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={cn("material-symbols-outlined text-[18px]", meta.color)}>{meta.icon}</span>
          <span className="font-medium text-[13px]">{meta.label}</span>
        </div>
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.14em]">
          {typeof state.duration_ms === "number" && (
            <span className="tabular-nums text-neutral-400">{state.duration_ms.toFixed(0)}ms</span>
          )}
          <span>{state.status}</span>
        </div>
      </div>

      {state.status !== "idle" && (
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          {typeof state.score === "number" && (
            <span>score: <span className="tabular-nums text-white">{state.score.toFixed(2)}</span></span>
          )}
          {typeof state.confidence === "number" && (
            <span>conf: <span className="tabular-nums text-white">{state.confidence.toFixed(2)}</span></span>
          )}
        </div>
      )}

      {state.red_flags && state.red_flags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {state.red_flags.map((f, i) => (
            <Badge key={i} variant="outline" className="text-[10px] border-white/10 bg-white/[0.03] truncate max-w-full">
              {f}
            </Badge>
          ))}
        </div>
      )}

      {state.error && (
        <div className="text-[10.5px] leading-snug text-rose-300/80 line-clamp-3 font-mono overflow-hidden break-all">
          {truncateError(state.error)}
        </div>
      )}

      {state.analysis && Object.keys(state.analysis).length > 0 && (
        <AnalysisPeek data={state.analysis} />
      )}
    </div>
  );
}

function AnalysisPeek({ data }: { data: Record<string, unknown> }) {
  const keys = Object.keys(data).slice(0, 3);
  return (
    <div className="text-[10.5px] leading-snug text-neutral-400 font-mono overflow-hidden">
      {keys.map(k => (
        <div key={k} className="truncate">
          <span className="text-neutral-500">{k}:</span>{" "}
          <span className="text-neutral-200 truncate inline-block max-w-[calc(100%-3rem)]">{stringifyShort((data as any)[k])}</span>
        </div>
      ))}
    </div>
  );
}

function SignalBars({ sv }: { sv: Record<string, unknown> }) {
  const pairs: Array<[string, number]> = [
    ["Market", Number(sv.market ?? 0)],
    ["Rug",    Number(sv.rug    ?? 0)],
    ["Social", Number(sv.social ?? 0)],
    ["Overall", Number(sv.overall ?? 0)],
  ];
  return (
    <div className="grid grid-cols-4 gap-3">
      {pairs.map(([label, v]) => (
        <div key={label} className="flex flex-col gap-1">
          <div className="flex items-baseline justify-between">
            <span className="text-[10px] uppercase tracking-[0.14em] text-neutral-500">{label}</span>
            <span className="text-[11px] tabular-nums text-white">{v.toFixed(2)}</span>
          </div>
          <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                v >= 0.6 ? "bg-emerald-400" : v <= 0.4 ? "bg-rose-400" : "bg-amber-400",
              )}
              style={{ width: `${Math.max(3, v * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function ActionBadge({ hint }: { hint: string }) {
  const color = {
    STRONG_BUY: "bg-emerald-500/20 text-emerald-300 border-emerald-400/30",
    BUY:        "bg-emerald-500/10 text-emerald-300 border-emerald-400/20",
    HOLD:       "bg-amber-500/10  text-amber-300   border-amber-400/20",
    SELL:       "bg-rose-500/10   text-rose-300    border-rose-400/20",
    STRONG_SELL:"bg-rose-500/20   text-rose-300    border-rose-400/30",
  }[hint] ?? "bg-white/[0.04] text-neutral-300 border-white/10";
  return (
    <span className={cn("inline-flex items-center gap-1 border rounded-full px-3 py-1 text-[11px] font-semibold tracking-wide uppercase", color)}>
      {hint || "—"}
    </span>
  );
}

// --- Main page -------------------------------------------------------------

export default function ScanPage() {
  const { state, dispatch, clearState } = useScanState();
  const [maxTokens, setMaxTokens] = useState(3);
  const [rawEvents, setRawEvents] = useState<ScanEvent[]>([]);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => { esRef.current?.close(); };
  }, []);

  const start = useCallback(() => {
    if (esRef.current) esRef.current.close();
    clearState();
    dispatch({ type: "SET_RUNNING", payload: true });
    setRawEvents([]);

    const params = new URLSearchParams({
      max_tokens: String(Math.max(1, Math.min(10, maxTokens))),
    });
    const es = new EventSource(`${API_BASE}/cron/scan/stream?${params.toString()}`);
    esRef.current = es;

    es.onmessage = (msg) => {
      try {
        const ev = JSON.parse(msg.data) as ScanEvent;
        setRawEvents(prev => [...prev, ev]);
        dispatch({ type: "ADD_EVENT", payload: ev });
        if (ev.type === "scan.done" || ev.type === "error") {
          es.close();
          esRef.current = null;
          dispatch({ type: "SET_RUNNING", payload: false });
        }
      } catch (err) {
        console.error("bad sse event", err, msg.data);
      }
    };
    es.onerror = () => {
      es.close();
      esRef.current = null;
      dispatch({ type: "SET_RUNNING", payload: false });
    };
  }, [maxTokens, dispatch]);

  const stop = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    dispatch({ type: "SET_RUNNING", payload: false });
  }, [dispatch]);

  const passedCount = useMemo(
    () => state.filters.filter(f => f.passed).length,
    [state.filters],
  );

  // Derived: detect auth failure from agent errors across all tokens,
  // so the banner still appears even if preflight didn't emit a warning
  // (e.g. older backend without the preflight).
  const derivedAuthWarning = useMemo<ScanWarning | null>(() => {
    const agentsSeen: AgentState[] = [];
    for (const t of state.tokens) {
      for (const a of Object.values(t.agents) as AgentState[]) {
        if (a.status !== "idle") agentsSeen.push(a);
      }
    }
    if (agentsSeen.length === 0) return null;
    const auth = agentsSeen.filter(
      a => a.status === "error" && typeof a.error === "string" &&
        /api key|unauthor|unauthentic|INVALID_ARGUMENT/i.test(a.error),
    );
    if (auth.length >= Math.max(2, agentsSeen.length * 0.5)) {
      return {
        code: "ai_unauthenticated",
        message: `${auth.length}/${agentsSeen.length} agent calls failed with an API-key error — all HOLD results below are safety fallbacks, not real recommendations. Set a valid GOOGLE_API_KEY in backend/.env.`,
      };
    }
    return null;
  }, [state.tokens]);

  const allWarnings = useMemo<ScanWarning[]>(() => {
    const seen = new Set<string>();
    const out: ScanWarning[] = [];
    for (const w of [...state.warnings, ...(derivedAuthWarning ? [derivedAuthWarning] : [])]) {
      if (seen.has(w.code)) continue;
      seen.add(w.code);
      out.push(w);
    }
    return out;
  }, [state.warnings, derivedAuthWarning]);

  return (
    <div className="flex flex-col gap-6 pb-12">
      {/* HEADER */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold text-white tracking-tight" style={{ fontFamily: "var(--font-space)" }}>
            Signal Scanner
          </h1>
          <p className="text-sm text-neutral-500 max-w-xl">
            Autonomous discovery → kill-chain filter → multi-agent analysis. Watch each
            stage and agent run live as the scan executes.
          </p>
        </div>
        <div className="flex items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-[0.18em] text-neutral-500">Max tokens</label>
            <Input
              type="number" min={1} max={10}
              value={maxTokens}
              onChange={e => setMaxTokens(Number(e.target.value) || 1)}
              disabled={state.running}
              className="w-24"
            />
          </div>
          {state.running ? (
            <Button onClick={stop} variant="destructive" className="gap-2">
              <span className="material-symbols-outlined text-[18px]">stop</span>
              Stop
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button onClick={start} className="gap-2">
                <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                Run scan
              </Button>
              {state.tokens.length > 0 && (
                <Button onClick={clearState} variant="outline" className="gap-2">
                  <span className="material-symbols-outlined text-[18px]">delete</span>
                  Clear results
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* WARNINGS */}
      {allWarnings.map((w) => (
        <div
          key={w.code}
          className="flex items-start gap-3 rounded-lg border border-amber-400/30 bg-amber-500/10 px-4 py-3"
        >
          <span className="material-symbols-outlined text-amber-300 mt-0.5">warning</span>
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <span className="text-[11px] uppercase tracking-[0.18em] text-amber-300/80">
              {w.code.replace(/_/g, " ")}
            </span>
            <span className="text-[13px] text-amber-100 leading-snug">{w.message}</span>
          </div>
        </div>
      ))}

      {/* TOP STATS */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatPill
          label="Run ID"
          value={<span className="text-xs font-mono text-white/80">{state.run_id ?? "—"}</span>}
        />
        <StatPill label="Discovered" value={state.discovered ?? "—"} />
        <StatPill label="Passed filter" value={state.filtered ?? passedCount ?? "—"} />
        <StatPill label="Analyzed" value={state.analyzed ?? state.tokens.filter(t => t.done).length} />
        <StatPill
          label="Elapsed"
          value={state.elapsed_seconds != null ? `${state.elapsed_seconds.toFixed(1)}s` : state.running ? "running…" : "—"}
        />
      </div>

      {/* KILL-CHAIN FILTER */}
      <Card variant="glass" className="px-6 gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-neutral-400">Kill-chain filter</h2>
          <div className="text-xs text-neutral-500">
            {passedCount}/{state.filters.length} passed
          </div>
        </div>
        {state.filters.length === 0 ? (
          <div className="text-sm text-neutral-500 py-4">
            {state.running ? (
              <FilterSkeleton />
            ) : (
              "Click Run scan to discover trending tokens."
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {state.filters.map((f, i) => (
              <div key={i} className={cn(
                "flex items-center gap-3 rounded-lg border px-3 py-2",
                f.passed
                  ? "border-emerald-400/20 bg-emerald-500/5"
                  : "border-white/5 bg-white/[0.02]",
              )}>
                <span className={cn(
                  "material-symbols-outlined text-[18px]",
                  f.passed ? "text-emerald-400" : "text-neutral-500",
                )}>
                  {f.passed ? "check_circle" : "block"}
                </span>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-[13px] font-semibold text-white truncate">
                    {f.symbol || f.address.slice(0, 8) + "…"}
                  </span>
                  <span className="text-[11px] text-neutral-400 truncate">{f.reason}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* TOKEN CARDS */}
      <div className="flex flex-col gap-4">
        {state.tokens.map((t) => (
          <TokenCard key={t.address} token={t} />
        ))}
        {state.running && state.tokens.length < (state.analyzed ?? 0) + 2 && (
          <>
            {Array.from({ length: Math.min(2, (state.analyzed ?? 0) + 2 - state.tokens.length) }).map((_, i) => (
              <TokenSkeleton key={`skeleton-${i}`} />
            ))}
          </>
        )}
        {state.tokens.length === 0 && !state.running && state.filters.length > 0 && (
          <div className="text-center py-8 text-sm text-neutral-500">
            No survivors — all candidates filtered out.
          </div>
        )}
      </div>

      {/* RAW EVENT LOG */}
      {rawEvents.length > 0 && (
        <Card variant="glass" className="px-6 gap-3">
          <details>
            <summary className="text-sm font-semibold uppercase tracking-[0.18em] text-neutral-400 cursor-pointer">
              Raw event log ({rawEvents.length})
            </summary>
            <div className="mt-4 max-h-96 overflow-y-auto font-mono text-[11px] leading-relaxed text-neutral-400 space-y-1">
              {rawEvents.map((ev, i) => (
                <div key={i} className="truncate">
                  <span className="text-sky-300">{ev.type}</span>
                  {" "}
                  <span className="text-neutral-500">
                    {JSON.stringify(filterFields(ev))}
                  </span>
                </div>
              ))}
            </div>
          </details>
        </Card>
      )}
    </div>
  );
}

// --- Token card ------------------------------------------------------------

function TokenCard({ token }: { token: TokenState }) {
  const sv = token.signal_vector;
  const actionHint = (sv?.action_hint as string) || "—";
  const confidence = Number(sv?.confidence ?? 0);
  const ks = token.killswitch;

  return (
    <Card variant="glass" className="px-6 gap-4">
      {/* token header */}
      <div className="flex flex-wrap items-start gap-4 justify-between">
        <div className="flex flex-col gap-1 min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-lg font-semibold text-white truncate" style={{ fontFamily: "var(--font-space)" }}>
              {token.symbol}
            </span>
            {token.name && token.name !== token.symbol && (
              <span className="text-sm text-neutral-500 truncate">{token.name}</span>
            )}
            {ks?.triggered && (
              <Badge variant="destructive" className="gap-1 shrink-0">
                <span className="material-symbols-outlined text-[14px]">warning</span>
                Kill-switch: {ks.rule}
              </Badge>
            )}
          </div>
          <div className="text-[11px] text-neutral-500 font-mono truncate">{token.address}</div>
          <div className="flex flex-wrap gap-4 text-[11px] text-neutral-400 mt-1 tabular-nums">
            <span>Price ${numfmt(token.price)}</span>
            <span>Vol24h ${numfmt(token.volume_24h, 0)}</span>
            <span>Liq ${numfmt(token.liquidity, 0)}</span>
            <span>Mcap ${numfmt(token.market_cap, 0)}</span>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <ActionBadge hint={actionHint} />
          {confidence > 0 && (
            <span className="text-[11px] text-neutral-500 tabular-nums">{(confidence * 100).toFixed(0)}%</span>
          )}
        </div>
      </div>

      {/* phase stepper */}
      <div className="flex flex-wrap gap-2">
        {PHASE_ORDER.map((p) => (
          <PhaseStep
            key={p}
            name={p}
            phase={token.phases[p]}
            active={token.phases[p].status !== "done"}
          />
        ))}
      </div>

      {/* agents */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {(Object.keys(AGENT_LABELS) as AgentName[]).map((a) => (
          <AgentCard key={a} name={a} state={token.agents[a]} />
        ))}
      </div>

      {/* signal vector */}
      {sv && (
        <div className="rounded-lg border border-white/5 bg-white/[0.02] px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] uppercase tracking-[0.18em] text-neutral-500">Signal vector</span>
            {Array.isArray(sv.warnings) && sv.warnings.length > 0 && (
              <div className="flex flex-wrap gap-1 justify-end">
                {(sv.warnings as string[]).map((w, i) => (
                  <Badge key={i} variant="outline" className="text-[10px] border-amber-400/20 bg-amber-500/5 text-amber-300 truncate max-w-full">
                    {w}
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <SignalBars sv={sv} />
        </div>
      )}

      {/* result reasoning */}
      {token.done && token.result && (
        <ResultPanel result={token.result} />
      )}
    </Card>
  );
}

function ResultPanel({ result }: { result: Record<string, unknown> }) {
  const reasoning = (result.reasoning as string) || "";
  const keyFactors = (result.key_factors as string[]) || [];
  const redFlags = (result.red_flags as string[]) || [];
  if (!reasoning && keyFactors.length === 0 && redFlags.length === 0) return null;
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] px-4 py-3 flex flex-col gap-2">
      <div className="text-[10px] uppercase tracking-[0.18em] text-neutral-500">Predictor summary</div>
      {reasoning && <p className="text-[12px] leading-relaxed text-neutral-200">{reasoning}</p>}
      {keyFactors.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {keyFactors.map((f, i) => (
            <Badge key={i} variant="outline" className="text-[10.5px] border-white/10 truncate max-w-full">{f}</Badge>
          ))}
        </div>
      )}
      {redFlags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {redFlags.map((f, i) => (
            <Badge key={i} variant="outline" className="text-[10.5px] border-rose-400/20 bg-rose-500/5 text-rose-300 truncate max-w-full">
              {f}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

// --- helpers ---------------------------------------------------------------

function numfmt(n: number | undefined, digits = 6): string {
  if (n == null || Number.isNaN(n)) return "—";
  if (n === 0) return "0";
  if (n >= 1) return n.toLocaleString("en-US", { maximumFractionDigits: digits });
  return n.toPrecision(3);
}

function truncateError(msg: string): string {
  const m = msg.match(/'message':\s*'([^']+)'/);
  if (m) return m[1];
  return msg.length > 180 ? msg.slice(0, 177) + "…" : msg;
}

function stringifyShort(v: unknown): string {
  if (v == null) return "—";
  if (typeof v === "string") return v.length > 60 ? v.slice(0, 57) + "…" : v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  try { const s = JSON.stringify(v); return s.length > 60 ? s.slice(0, 57) + "…" : s; }
  catch { return String(v); }
}

function filterFields(ev: ScanEvent): Record<string, unknown> {
  // Strip heavy fields from raw-log preview.
  const { type: _t, analysis, results, result, filter_log, ...rest } = ev as any;
  return rest;
}
