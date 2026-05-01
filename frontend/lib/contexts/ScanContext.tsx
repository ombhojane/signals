"use client";

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from "react";

// Types
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

export type ScanState = {
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

type ScanAction = 
  | { type: "SET_STATE"; payload: ScanState }
  | { type: "ADD_EVENT"; payload: ScanEvent }
  | { type: "CLEAR_STATE" }
  | { type: "SET_RUNNING"; payload: boolean };

interface ScanContextType {
  state: ScanState;
  dispatch: React.Dispatch<ScanAction>;
  clearState: () => void;
}

const ScanContext = createContext<ScanContextType | undefined>(undefined);

// Constants
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

// Helper to apply events
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
    case "signal": {
      return patchLastToken(state, t => ({
        ...t,
        signal_vector: ev as Record<string, unknown>,
      }));
    }
    case "killswitch": {
      return patchLastToken(state, t => ({
        ...t,
        killswitch: {
          triggered: Boolean(ev.triggered),
          rule: (ev.rule as string | null) ?? null,
          message: (ev.message as string | null) ?? null,
        },
      }));
    }
    case "token.done": {
      return patchLastToken(state, t => ({
        ...t,
        result: ev as Record<string, unknown>,
        done: true,
      }));
    }
    case "scan.done":
      return {
        ...state,
        running: false,
        summary: ev as Record<string, unknown>,
      };
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

// Reducer
const initialState: ScanState = {
  running: false,
  filters: [],
  tokens: [],
  warnings: [],
};

function scanReducer(state: ScanState, action: ScanAction): ScanState {
  switch (action.type) {
    case "SET_STATE":
      return action.payload;
    case "ADD_EVENT":
      return applyEvent(state, action.payload);
    case "CLEAR_STATE":
      return initialState;
    case "SET_RUNNING":
      return { ...state, running: action.payload };
    default:
      return state;
  }
}

// Provider Component
export function ScanProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(scanReducer, initialState);

  // Persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem("scanState", JSON.stringify(state));
    } catch (e) {
      console.warn("Failed to persist scan state:", e);
    }
  }, [state]);

  // Restore from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("scanState");
      if (stored) {
        const parsed = JSON.parse(stored);
        dispatch({ type: "SET_STATE", payload: parsed });
      }
    } catch (e) {
      console.warn("Failed to restore scan state:", e);
    }
  }, []);

  const clearState = () => dispatch({ type: "CLEAR_STATE" });

  return (
    <ScanContext.Provider value={{ state, dispatch, clearState }}>
      {children}
    </ScanContext.Provider>
  );
}

// Hook
export function useScanState() {
  const context = useContext(ScanContext);
  if (!context) {
    throw new Error("useScanState must be used within ScanProvider");
  }
  return context;
}

export { applyEvent, patchLastToken };
