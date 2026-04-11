"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { SimulationInput } from "@/components/simulation/SimulationInput";
import { DataFetchProgress } from "@/components/simulation/DataFetchProgress";
import { AnalysisPanel } from "@/components/simulation/AnalysisPanel";
import { PredictionCard } from "@/components/simulation/PredictionCard";
import { SimulationControls } from "@/components/simulation/SimulationControls";
import { SimulationMetrics } from "@/components/simulation/SimulationMetrics";
import { ResultSummary } from "@/components/simulation/ResultSummary";
import { SimulationHistory } from "@/components/simulation/SimulationHistory";
import { MarketChart, MarketChartHandle } from "@/components/charts/MarketChart";
import { Card } from "@/components/ui/card";
import {
  SimulationState,
  TokenSnapshot,
  SimulationResult,
} from "@/lib/types/simulation";
import {
  generateDEXData,
  generateGMGNData,
  generateTwitterData,
  createTokenSnapshot,
} from "@/lib/simulation/market-data-generator";
import { PredictionService } from "@/lib/simulation/prediction-service";
import {
  fetchTokenAnalysis,
  fetchTwitterData as fetchTwitterDataAPI,
  fetchRLAgentAnalysis,
  fetchTokenScan,
} from "@/lib/api/client";
import { SimulationEngine } from "@/lib/simulation/simulation-engine";
import { SimulationStorage } from "@/lib/simulation/storage";
import { compressChartData } from "@/lib/utils/simulation-helpers";
import { generateId } from "@/lib/utils";

// ─── Regime toast messages ─────────────────────────────────────────────────────
const REGIME_LABELS: Record<string, string> = {
  breakout:      "📈 Breakout detected",
  dump:          "📉 Sell pressure building",
  pullback:      "⬇️ Pullback in progress",
  consolidation: "⏸ Price consolidating",
  accumulation:  "🔄 Accumulation phase",
};

// ─── Micro-fluctuate snapshot for predicted-phase live feel ───────────────────
function nudgeSnapshot(snap: TokenSnapshot): TokenSnapshot {
  const j = (r: number) => (Math.random() - 0.5) * r;
  return {
    ...snap,
    rsi: Math.max(0, Math.min(100, snap.rsi + j(1.5))),
    sentimentScore: Math.max(0, Math.min(100, snap.sentimentScore + j(2))),
    mentions24h: Math.max(0, snap.mentions24h + Math.round(j(4))),
    communitySize: Math.max(0, snap.communitySize + Math.round(j(20))),
    influencerMentions: Math.max(0, snap.influencerMentions + Math.round(j(1))),
    macd: snap.macd + j(0.00005),
    macdSignal: snap.macdSignal + j(0.00005),
    volume24h: Math.max(0, snap.volume24h * (1 + j(0.02))),
  };
}

function SimulationContent() {
  const searchParams = useSearchParams();
  const urlAddress = searchParams.get("address") || "";

  const [state, setState] = useState<SimulationState>({
    phase: "idle",
    coinAddress: "",
    duration: 15,
    marketData: [],
    isPaused: false,
  });

  // Historical + live points stored for final save. Chart is updated imperatively.
  const tickHistoryRef = useRef<Array<{ time: number; value: number }>>([]);

  // Chart imperative ref
  const chartRef = useRef<MarketChartHandle | null>(null);

  // Initial data for the chart (set once)
  const [initialChartData, setInitialChartData] = useState<Array<{ time: number; value: number }>>([]);

  // Live snapshot for Market Analysis in predicted phase
  const [liveSnapshot, setLiveSnapshot] = useState<TokenSnapshot | null>(null);

  // Simulation engine
  const engineRef = useRef<SimulationEngine | null>(null);

  // Predicted-phase live tick
  const liveTickRef = useRef<NodeJS.Timeout | null>(null);

  // Regime toast state
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const toastTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastRegimeRef = useRef<string | null>(null);

  // Latest price for metrics
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);

  // Init engine
  useEffect(() => {
    engineRef.current = new SimulationEngine();
    return () => { engineRef.current?.stop(); };
  }, []);

  // ── Show regime toast ────────────────────────────────────────────────────────
  const showRegimeToast = useCallback((regime: string) => {
    if (regime === lastRegimeRef.current) return;
    lastRegimeRef.current = regime;
    const msg = REGIME_LABELS[regime];
    if (!msg) return;
    setToastMsg(msg);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToastMsg(null), 3000);
  }, []);

  // ── Fetch & analyse ──────────────────────────────────────────────────────────
  const handleStart = useCallback(async (coinAddress: string) => {
    setState((p) => ({ ...p, phase: "fetching", coinAddress, marketData: [], fetchProgress: [], error: undefined }));
    setInitialChartData([]);
    tickHistoryRef.current = [];
    setLiveSnapshot(null);

    try {
      // Try new token-scan endpoint first (comprehensive backend integration)
      let dexData, gmgnData, twitterData;
      let prediction;
      let tokenSymbol = '';
      let useTokenScan = false;

      // Use new token-scan endpoint for comprehensive analysis
      try {
        setState((p) => ({ ...p, fetchProgress: ["token_scan"] }));
        const scanResult = await fetchTokenScan(coinAddress, 'sol', false);
        
        if (scanResult.token && scanResult.token.price > 0) {
          useTokenScan = true;
          const token = scanResult.token;
          const safety = scanResult.safety;
          
          tokenSymbol = token.symbol || '';
          
          // Convert token-scan result to our format
          dexData = {
            price: token.price || 0,
            volume24h: token.volume_24h || 0,
            liquidity: token.liquidity || 0,
            marketCap: token.market_cap || 0,
            priceHistory: [], // Will be populated from price data if available
          };
          
          gmgnData = {
            holderCount: safety.holder_count || 0,
            top10HolderPct: safety.top_10_holder_pct || 0,
            smartMoneyFlow: 'neutral' as const,
            rugScore: safety.overall_risk_score || 50,
            devWalletPct: 0,
            liquidityLocked: safety.liquidity_locked || false,
            lockDaysRemaining: 0,
          };
          
          twitterData = {
            mentions24h: 0,
            sentimentScore: 50,
            influencerMentions: 0,
            trending: false,
            communitySize: 0,
          };
          
          prediction = scanResult.prediction;
          
          setState((p) => ({ ...p, fetchProgress: ["token_scan", "done"] }));
        }
      } catch (e) {
        console.warn("Token-scan endpoint unavailable, falling back to individual endpoints", e);
      }
      
      // Fallback: use individual endpoints if token-scan didn't work
      if (!useTokenScan || !dexData) {
        // Step 1: Token Analysis (DEX + Safety in one call)
        try {
          const analysis = await fetchTokenAnalysis(coinAddress);
          dexData = analysis.dexData;
          gmgnData = analysis.gmgnData;
          tokenSymbol = analysis.symbol;
        } catch {
          console.warn("Backend Token Analysis unavailable, using mock data");
          dexData = await generateDEXData(coinAddress);
          gmgnData = await generateGMGNData(coinAddress);
        }
        setState((p) => ({ ...p, fetchProgress: ["dex", "gmgn"] }));
        
        // Step 2: Twitter/Social data (pass symbol for better search)
        try {
          twitterData = await fetchTwitterDataAPI(coinAddress, tokenSymbol || undefined);
        } catch {
          console.warn("Backend Twitter API unavailable, using mock data");
          twitterData = await generateTwitterData(coinAddress);
        }
        
        // Step 3: RL agent for prediction, fall back to local prediction service
        try {
          const rlResult = await fetchRLAgentAnalysis(coinAddress);
          prediction = rlResult.decision;
        } catch {
          console.warn("Backend RL agent unavailable, using local prediction");
          prediction = null;
        }
        
        setState((p) => ({ ...p, fetchProgress: ["dex", "gmgn", "twitter"] }));
      }

      // Create snapshot from data
      const snap = createTokenSnapshot(coinAddress, dexData!, gmgnData!, twitterData!, 0);
      setState((p) => ({ ...p, phase: "analyzing", dexData: dexData!, gmgnData: gmgnData!, twitterData: twitterData!, marketData: [snap] }));

      // Use prediction from token-scan or generate local prediction
      if (!prediction) {
        prediction = await PredictionService.generatePrediction(snap, snap.price, state.duration);
      }

      // Build price history from DEX data
      const historical = (dexData?.priceHistory || []).map((pt) => ({ time: pt.time, value: pt.price }));
      if (historical.length === 0 || historical[historical.length - 1].value !== snap.price) {
        historical.push({ time: Date.now(), value: snap.price });
      }

      // Store for final save
      tickHistoryRef.current = historical;

      setInitialChartData(historical);
      setLiveSnapshot(snap);

      setState((p) => ({
        ...p,
        phase: "predicted",
        prediction,
        predictedValue: prediction.predictedValue,
        predictedTimestamp: new Date(),
      }));
    } catch (err) {
      setState((p) => ({
        ...p,
        phase: "error",
        error: err instanceof Error ? err.message : "Failed to fetch market data",
      }));
    }
  }, [state.duration]);

  // ── Predicted phase: live tick (subtle market breathing) ─────────────────────
  useEffect(() => {
    if (state.phase !== "predicted") {
      if (liveTickRef.current) { clearInterval(liveTickRef.current); liveTickRef.current = null; }
      return;
    }

    liveTickRef.current = setInterval(() => {
      // Push micro tick to chart
      const history = tickHistoryRef.current;
      if (history.length > 0) {
        const last = history[history.length - 1];
        const change = (Math.random() - 0.48) * last.value * 0.003;
        const newPoint = { time: Date.now(), value: Math.max(0.000001, last.value + change) };
        history.push(newPoint);
        chartRef.current?.pushTick(newPoint);
        setLivePrice(newPoint.value);
      }
      setLiveSnapshot((p) => (p ? nudgeSnapshot(p) : p));
    }, 2000);

    return () => { if (liveTickRef.current) { clearInterval(liveTickRef.current); liveTickRef.current = null; } };
  }, [state.phase]);

  // ── Start simulation ─────────────────────────────────────────────────────────
  const handleStartSimulation = useCallback(() => {
    if (!state.prediction || !state.marketData.length || !engineRef.current) return;

    // Stop predicted-phase ticker
    if (liveTickRef.current) { clearInterval(liveTickRef.current); liveTickRef.current = null; }

    const snap = state.marketData[state.marketData.length - 1];

    setState((p) => ({
      ...p,
      phase: "simulating",
      startTime: new Date(),
      currentTime: new Date(),
      elapsedTime: 0,
      isPaused: false,
    }));

    const durationMs = state.duration * 60 * 1000;

    engineRef.current.run(
      {
        startPrice:     snap.price,
        predictedPrice: state.predictedValue || snap.price,
        duration:       state.duration,
        volatility:     snap.volatility,
        updateInterval: 2,
        entryPrice:     snap.price,
        action:         state.prediction.action,
      },
      (price, elapsed, total, regime) => {
        const point = { time: Date.now(), value: price };
        tickHistoryRef.current.push(point);

        // Imperative push — no state update, no React re-render of chart
        chartRef.current?.pushTick(point);

        setLivePrice(price);
        setElapsedMs(elapsed);
        setState((p) => ({ ...p, currentTime: new Date(), elapsedTime: elapsed }));
        showRegimeToast(regime as string);
      },
      (result: SimulationResult) => {
        const simId = generateId();
        const compressed = compressChartData(
          tickHistoryRef.current.map((p) => ({ time: p.time, value: p.value })),
          10
        );

        SimulationStorage.saveSimulation({
          id:          simId,
          coinAddress: state.coinAddress,
          startedAt:   state.startTime || new Date(),
          completedAt: new Date(),
          duration:    state.duration,
          prediction:  state.prediction!,
          result,
          marketData:  state.marketData,
          chartData:   compressed,
        });

        setState((p) => ({ ...p, phase: "completed", result, simulationId: simId }));
      }
    );
  }, [state, showRegimeToast]);

  const handlePause = useCallback(() => {
    engineRef.current?.pause();
    setState((p) => ({ ...p, isPaused: true }));
  }, []);

  const handleResume = useCallback(() => {
    engineRef.current?.resume();
    setState((p) => ({ ...p, isPaused: false }));
  }, []);

  const handleStop = useCallback(() => {
    engineRef.current?.stop();
    setState((p) => ({ ...p, phase: "idle", isPaused: false }));
  }, []);

  const handleDurationChange = useCallback((duration: number) => {
    setState((p) => ({ ...p, duration }));
  }, []);

  // ── Shared chart element ─────────────────────────────────────────────────────
  const chartElement = (active: boolean) => (
    <Card variant="glass" className="p-4">
      <MarketChart
        ref={chartRef}
        initialData={initialChartData}
        predictedPrice={state.predictedValue}
        entryPrice={state.marketData[0]?.price}
        stopLoss={state.prediction?.stopLoss}
        height={400}
        isTradeActive={active}
      />
    </Card>
  );

  // ── Phase renderer ───────────────────────────────────────────────────────────
  const renderPhase = () => {
    switch (state.phase) {
      case "idle":
        return (
          <div className="space-y-6">
            <SimulationInput onStart={handleStart} defaultAddress={urlAddress} />
            <SimulationHistory />
          </div>
        );

      case "fetching":
        return (
          <div className="space-y-6">
            <SimulationInput onStart={handleStart} defaultAddress={urlAddress} disabled />
            <DataFetchProgress completedSources={state.fetchProgress ?? []} />
          </div>
        );

      case "analyzing":
        return (
          <Card variant="glass" className="p-6">
            <div className="flex items-center justify-center gap-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
              <p className="text-lg font-medium">Analyzing market data…</p>
            </div>
          </Card>
        );

      case "predicted":
        return (
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              {(liveSnapshot ?? state.marketData[0]) && (
                <AnalysisPanel snapshot={liveSnapshot ?? state.marketData[0]} />
              )}
              {chartElement(false)}
            </div>
            <div className="space-y-6">
              {state.prediction && state.marketData[0] && (
                <PredictionCard
                  prediction={state.prediction}
                  currentPrice={livePrice ?? state.marketData[0].price}
                />
              )}
              <SimulationControls
                duration={state.duration}
                onDurationChange={handleDurationChange}
                isRunning={false}
                isPaused={false}
                onStart={handleStartSimulation}
                onPause={handlePause}
                onResume={handleResume}
                onStop={handleStop}
              />
            </div>
          </div>
        );

      case "simulating":
        return (
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              {chartElement(true)}
              {state.marketData[0] && state.prediction && (
                <SimulationMetrics
                  currentPrice={livePrice ?? state.marketData[0].price}
                  entryPrice={state.marketData[0].price}
                  predictedPrice={state.predictedValue || state.marketData[0].price}
                  action={state.prediction.action}
                  elapsedTime={elapsedMs}
                  remainingTime={Math.max(0, state.duration * 60 * 1000 - elapsedMs)}
                />
              )}
            </div>
            <div className="space-y-6">
              {state.prediction && state.marketData[0] && (
                <PredictionCard
                  prediction={state.prediction}
                  currentPrice={livePrice ?? state.marketData[0].price}
                />
              )}
              <SimulationControls
                duration={state.duration}
                onDurationChange={handleDurationChange}
                isRunning={true}
                isPaused={state.isPaused}
                onStart={handleStartSimulation}
                onPause={handlePause}
                onResume={handleResume}
                onStop={handleStop}
              />
            </div>
          </div>
        );

      case "completed":
        return (
          <div className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 space-y-6">
                {chartElement(true)}
                {state.result && <ResultSummary result={state.result} />}
              </div>
              <div className="space-y-6">
                {state.prediction && state.marketData[0] && (
                  <PredictionCard
                    prediction={state.prediction}
                    currentPrice={livePrice ?? state.marketData[0].price}
                  />
                )}
                <SimulationControls
                  duration={state.duration}
                  onDurationChange={handleDurationChange}
                  isRunning={false}
                  isPaused={false}
                  onStart={handleStartSimulation}
                  onPause={handlePause}
                  onResume={handleResume}
                  onStop={handleStop}
                />
              </div>
            </div>
            <SimulationHistory />
          </div>
        );

      case "error":
        return (
          <Card variant="glass" className="p-6 border-red-500/50">
            <div className="text-center space-y-4">
              <p className="text-lg font-semibold text-red-500">Error</p>
              <p className="text-muted-foreground">{state.error || "An error occurred"}</p>
              <button
                onClick={() =>
                  setState({ phase: "idle", coinAddress: "", duration: 15, marketData: [], isPaused: false })
                }
                className="text-primary hover:underline"
              >
                Start Over
              </button>
            </div>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Token Scan</h2>
      </div>

      {renderPhase()}

      {/* Regime toast */}
      {toastMsg && (
        <div
          className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-lg text-sm font-medium
                     bg-zinc-900/90 border border-zinc-700 text-zinc-100 shadow-xl
                     animate-in slide-in-from-bottom-4 fade-in duration-300"
        >
          {toastMsg}
        </div>
      )}
    </div>
  );
}

export default function SimulationPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center p-12">Loading...</div>}>
      <SimulationContent />
    </Suspense>
  );
}
