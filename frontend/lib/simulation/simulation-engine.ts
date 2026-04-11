import { SimulationConfig, PricePoint, SimulationResult } from '../types/simulation';

// ─── Market Regimes ────────────────────────────────────────────────────────────
type Regime = 'accumulation' | 'breakout' | 'pullback' | 'consolidation' | 'dump';

interface RegimeConfig {
  driftPerTick: number;      // directional bias per tick
  volMultiplier: number;     // relative volatility vs base
  tickGapMs: [number, number]; // [min, max] ms between ticks
  jumpChance: number;        // probability of a price jump
  jumpSize: [number, number]; // [min, max] jump magnitude (fraction)
  momentumAlpha: number;     // momentum carry factor 0–1
}

const REGIME_CONFIGS: Record<Regime, RegimeConfig> = {
  accumulation: {
    driftPerTick: 0.0002,
    volMultiplier: 0.4,
    tickGapMs: [2500, 5000],
    jumpChance: 0.005,
    jumpSize: [0.005, 0.02],
    momentumAlpha: 0.15,
  },
  breakout: {
    driftPerTick: 0.006,
    volMultiplier: 2.8,
    tickGapMs: [200, 700],
    jumpChance: 0.08,
    jumpSize: [0.04, 0.18],
    momentumAlpha: 0.55,
  },
  pullback: {
    driftPerTick: -0.004,
    volMultiplier: 2.0,
    tickGapMs: [400, 1200],
    jumpChance: 0.04,
    jumpSize: [0.02, 0.10],
    momentumAlpha: 0.4,
  },
  consolidation: {
    driftPerTick: 0.0001,
    volMultiplier: 0.5,
    tickGapMs: [1500, 4000],
    jumpChance: 0.01,
    jumpSize: [0.005, 0.025],
    momentumAlpha: 0.1,
  },
  dump: {
    driftPerTick: -0.007,
    volMultiplier: 3.0,
    tickGapMs: [300, 900],
    jumpChance: 0.07,
    jumpSize: [0.04, 0.20],
    momentumAlpha: 0.5,
  },
};

function rng(): number {
  return Math.random();
}

function randn(): number {
  // Box-Muller transform for Gaussian random number
  let u = 0, v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

function randomBetween(min: number, max: number): number {
  return min + rng() * (max - min);
}

// ─── Regime Sequence Generator ─────────────────────────────────────────────────
function buildRegimeSequence(
  action: 'BUY' | 'SELL' | 'HOLD',
  totalTicks: number
): Array<{ regime: Regime; ticks: number }> {
  // Weighted regime pools by prediction action
  const pools: Record<string, Regime[]> = {
    BUY: ['accumulation', 'breakout', 'pullback', 'consolidation', 'breakout'],
    SELL: ['consolidation', 'pullback', 'dump', 'consolidation', 'dump'],
    HOLD: ['accumulation', 'consolidation', 'pullback', 'consolidation', 'accumulation'],
  };

  const pool = pools[action] ?? pools.HOLD;
  const sequence: Array<{ regime: Regime; ticks: number }> = [];
  let remaining = totalTicks;

  while (remaining > 0) {
    const regime = pool[Math.floor(rng() * pool.length)];
    // Each regime lasts 8–25% of total ticks
    const pct = randomBetween(0.08, 0.25);
    const ticks = Math.max(2, Math.min(remaining, Math.round(totalTicks * pct)));
    sequence.push({ regime, ticks });
    remaining -= ticks;
  }

  return sequence;
}

// ─── Tick Array Builder ─────────────────────────────────────────────────────────
export interface RealisticTick {
  /** Wall-clock timestamp (ms) relative to simulation start */
  relativeMs: number;
  price: number;
  regime: Regime;
  volume: number;
}

export function buildTickArray(
  startPrice: number,
  predictedPrice: number,
  durationMs: number,
  baseVolatility: number,
  action: 'BUY' | 'SELL' | 'HOLD'
): RealisticTick[] {
  // Estimate total ticks (avg ~1.5s gaps → ~durationMs/1500)
  const estimatedTicks = Math.round(durationMs / 1500);
  const regimeSeq = buildRegimeSequence(action, estimatedTicks);

  const ticks: RealisticTick[] = [];
  let price = startPrice;
  let prevReturn = 0;
  let currentVolatility = baseVolatility;
  let elapsedMs = 0;
  let totalTicks = 0;

  // Count total ticks across regimes
  for (const seg of regimeSeq) totalTicks += seg.ticks;

  // Drift that gently pulls toward predicted price over the full duration
  const overallDriftPerTick = Math.log(predictedPrice / startPrice) / totalTicks * 0.4;

  for (const seg of regimeSeq) {
    const cfg = REGIME_CONFIGS[seg.regime];

    for (let i = 0; i < seg.ticks; i++) {
      // ── Tick gap (variable speed) ──
      const gapMs = Math.round(randomBetween(cfg.tickGapMs[0], cfg.tickGapMs[1]));
      elapsedMs += gapMs;
      if (elapsedMs > durationMs) break;

      // ── Volatility clustering (GARCH-lite) ──
      currentVolatility = baseVolatility * cfg.volMultiplier
        * (1 + 0.45 * Math.abs(prevReturn) / (baseVolatility + 0.0001));
      currentVolatility = Math.min(currentVolatility, baseVolatility * 5); // cap

      // ── Brownian component ──
      const dt = gapMs / 60000; // normalise to minute
      const brownian = currentVolatility * Math.sqrt(dt) * randn();

      // ── Momentum carry ──
      const momentum = cfg.momentumAlpha * prevReturn;

      // ── Regime drift ──
      const regimeDrift = cfg.driftPerTick;

      // ── Global drift toward predicted price ──
      const globalDrift = overallDriftPerTick;

      // ── Jump component ──
      let jump = 0;
      if (rng() < cfg.jumpChance) {
        const magnitude = randomBetween(cfg.jumpSize[0], cfg.jumpSize[1]);
        jump = (rng() > 0.5 ? 1 : -1) * magnitude;
      }

      // ── Combine ──
      const totalReturn = regimeDrift + globalDrift + brownian + momentum + jump;
      price = Math.max(0.000001, price * (1 + totalReturn));
      prevReturn = totalReturn;

      // ── Volume (correlated to volatility) ──
      const baseVol = 100000;
      const volume = baseVol * cfg.volMultiplier * (1 + Math.abs(totalReturn) * 20) * (0.5 + rng());

      ticks.push({
        relativeMs: elapsedMs,
        price,
        regime: seg.regime,
        volume,
      });
    }
  }

  // Anchor last tick to predicted price ± 5%
  if (ticks.length > 0) {
    const variance = (rng() - 0.5) * 0.1;
    ticks[ticks.length - 1].price = predictedPrice * (1 + variance);
  }

  return ticks;
}

// ─── Simulation Engine ──────────────────────────────────────────────────────────
export class SimulationEngine {
  private timeoutId: NodeJS.Timeout | null = null;
  private isRunning = false;
  private isPaused = false;
  private pausedAt = 0;
  private totalPausedMs = 0;
  private scheduleNextRef: (() => void) | null = null;

  async run(
    config: SimulationConfig,
    onUpdate: (price: number, elapsed: number, totalDuration: number, regime: Regime) => void,
    onComplete: (result: SimulationResult) => void
  ): Promise<void> {
    if (this.isRunning) throw new Error('Simulation already running');

    this.isRunning = true;
    this.isPaused = false;
    this.totalPausedMs = 0;
    this.scheduleNextRef = null;

    const durationMs = config.duration * 60 * 1000;

    // Build the full tick array upfront
    const ticks = buildTickArray(
      config.startPrice,
      config.predictedPrice,
      durationMs,
      config.volatility,
      config.action
    );

    if (ticks.length === 0) {
      this.isRunning = false;
      return;
    }

    const wallStart = Date.now();
    let tickIndex = 0;

    const scheduleNext = () => {
      if (!this.isRunning || this.isPaused) return;

      const tick = ticks[tickIndex];
      const wallNow = Date.now();
      const effectiveElapsed = wallNow - wallStart - this.totalPausedMs;

      // Wait until the tick's scheduled relative time
      const delay = Math.max(0, tick.relativeMs - effectiveElapsed);

      this.timeoutId = setTimeout(() => {
        if (!this.isRunning || this.isPaused) return;

        const elapsed = Date.now() - wallStart - this.totalPausedMs;
        onUpdate(tick.price, elapsed, durationMs, tick.regime);

        tickIndex++;

        if (tickIndex >= ticks.length || elapsed >= durationMs) {
          this.isRunning = false;
          const finalPrice = ticks[ticks.length - 1].price;
          onComplete(this.calculateResult(config, config.startPrice, finalPrice, config.predictedPrice));
          return;
        }

        scheduleNext();
      }, delay);
    };

    // Store reference so resume() can restart the loop
    this.scheduleNextRef = scheduleNext;

    scheduleNext();
  }

  pause(): void {
    if (this.isRunning && !this.isPaused) {
      this.isPaused = true;
      this.pausedAt = Date.now();
      if (this.timeoutId) clearTimeout(this.timeoutId);
    }
  }

  resume(): void {
    if (this.isRunning && this.isPaused) {
      this.totalPausedMs += Date.now() - this.pausedAt;
      this.isPaused = false;
      // Restart the scheduling loop from where we left off
      if (this.scheduleNextRef) this.scheduleNextRef();
    }
  }

  stop(): void {
    this.isRunning = false;
    this.isPaused = false;
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }

  getRunning(): boolean { return this.isRunning; }
  getPaused(): boolean { return this.isPaused; }

  private calculateResult(
    config: SimulationConfig,
    entryPrice: number,
    exitPrice: number,
    predictedPrice: number
  ): SimulationResult {
    const priceChange = exitPrice - entryPrice;
    const priceChangePercent = (priceChange / entryPrice) * 100;

    let profitLoss = 0;
    let profitLossPercent = 0;

    if (config.action === 'BUY') {
      profitLoss = priceChange;
      profitLossPercent = priceChangePercent;
    } else if (config.action === 'SELL') {
      profitLoss = -priceChange;
      profitLossPercent = -priceChangePercent;
    }

    let status: 'profit' | 'loss' | 'equilized';
    if (Math.abs(profitLossPercent) < 0.5) status = 'equilized';
    else if (profitLossPercent > 0) status = 'profit';
    else status = 'loss';

    const predictionError = Math.abs(exitPrice - predictedPrice) / predictedPrice;
    const accuracy = Math.max(0, Math.min(100, (1 - predictionError) * 100));

    return {
      action: config.action,
      entryPrice,
      exitPrice,
      predictedPrice,
      actualPrice: exitPrice,
      priceChange,
      priceChangePercent,
      profitLoss,
      profitLossPercent,
      status,
      accuracy,
      duration: config.duration,
      completedAt: new Date(),
    };
  }
}
