"use client";

import { useEffect, useRef, useImperativeHandle, forwardRef } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, Time, LineSeries } from "lightweight-charts";
import { formatCurrency } from "@/lib/utils";
import { cn } from "@/lib/utils";

export interface ChartDataPoint {
  time: number;
  value: number;
}

// Imperative handle so the parent can push individual ticks without re-rendering
export interface MarketChartHandle {
  pushTick: (point: ChartDataPoint, colour?: string) => void;
}

interface MarketChartProps {
  /** Initial / historical data loaded once on mount */
  initialData: ChartDataPoint[];
  predictedPrice?: number;
  entryPrice?: number;
  stopLoss?: number;
  height?: number;
  className?: string;
  isTradeActive?: boolean;
}

export const MarketChart = forwardRef<MarketChartHandle, MarketChartProps>(function MarketChart(
  {
    initialData,
    predictedPrice,
    entryPrice,
    stopLoss,
    height = 400,
    className,
    isTradeActive = false,
  },
  ref
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const priceLinesRef = useRef<Map<string, any>>(new Map());
  const lastPriceRef = useRef<number | null>(null);
  // Live badge element
  const badgeRef = useRef<HTMLDivElement | null>(null);

  // ── Initialise chart ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
        fontFamily: "JetBrains Mono, ui-monospace, monospace",
      },
      grid: {
        vertLines: { color: "rgba(39,39,42,0.5)" },
        horzLines: { color: "rgba(39,39,42,0.5)" },
      },
      rightPriceScale: {
        borderColor: "rgba(39,39,42,1)",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "rgba(39,39,42,1)",
        timeVisible: true,
        secondsVisible: true,
      },
      crosshair: {
        vertLine: { color: "#71717a", labelBackgroundColor: "#27272a" },
        horzLine: { color: "#71717a", labelBackgroundColor: "#27272a" },
      },
      localization: {
        priceFormatter: (p: number) => formatCurrency(p),
      },
    });

    chartRef.current = chart;

    const series = chart.addSeries(LineSeries, {
      color: "#3b82f6",
      lineWidth: 2,
      title: "Price",
      priceFormat: { type: "price", precision: 8, minMove: 0.00000001 },
      lastValueVisible: true,
      priceLineVisible: false,
    });

    seriesRef.current = series;

    // Resize
    const onResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      priceLinesRef.current.clear();
    };
  }, [height]);

  // ── Load initial / historical data once ─────────────────────────────────────
  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart || initialData.length === 0) return;

    const sorted = [...initialData]
      .sort((a, b) => a.time - b.time)
      .map((d) => ({ time: d.time as Time, value: d.value }));

    series.setData(sorted);
    chart.timeScale().fitContent();

    // Init last price
    lastPriceRef.current = sorted[sorted.length - 1].value;
  }, [initialData]);

  // ── Price lines (entry / predicted / stop loss) ─────────────────────────────
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    priceLinesRef.current.forEach((line) => {
      try { series.removePriceLine(line); } catch {}
    });
    priceLinesRef.current.clear();

    if (!isTradeActive) return;

    if (entryPrice) {
      priceLinesRef.current.set("entry", series.createPriceLine({
        price: entryPrice, color: "#10b981", lineWidth: 2, lineStyle: 2,
        axisLabelVisible: true, title: "Entry",
      }));
    }
    if (predictedPrice) {
      priceLinesRef.current.set("predicted", series.createPriceLine({
        price: predictedPrice, color: "#f59e0b", lineWidth: 2, lineStyle: 2,
        axisLabelVisible: true, title: "Target",
      }));
    }
    if (stopLoss) {
      priceLinesRef.current.set("stopLoss", series.createPriceLine({
        price: stopLoss, color: "#ef4444", lineWidth: 2, lineStyle: 2,
        axisLabelVisible: true, title: "Stop Loss",
      }));
    }
  }, [entryPrice, predictedPrice, stopLoss, isTradeActive]);

  // ── Imperative handle: pushTick ─────────────────────────────────────────────
  useImperativeHandle(ref, () => ({
    pushTick(point: ChartDataPoint, colour?: string) {
      const series = seriesRef.current;
      const chart = chartRef.current;
      if (!series || !chart) return;

      // Use series.update() — only sends the new single point, no full rebuild
      series.update({ time: point.time as Time, value: point.value });

      // Keep time scale scrolled to latest
      chart.timeScale().scrollToRealTime();

      // Trend colour
      const prev = lastPriceRef.current;
      if (prev !== null) {
        const trendUp = point.value >= prev;
        const newColour = colour ?? (trendUp ? "#10b981" : "#ef4444");
        series.applyOptions({ color: newColour });
      }
      lastPriceRef.current = point.value;

      // Update live price badge
      if (badgeRef.current) {
        const prev2 = lastPriceRef.current;
        const up = prev !== null ? point.value >= prev : true;
        badgeRef.current.textContent = formatCurrency(point.value);
        badgeRef.current.style.background = up
          ? "rgba(16,185,129,0.15)"
          : "rgba(239,68,68,0.15)";
        badgeRef.current.style.color = up ? "#10b981" : "#ef4444";
        badgeRef.current.style.borderColor = up
          ? "rgba(16,185,129,0.4)"
          : "rgba(239,68,68,0.4)";
      }
    },
  }), []);

  return (
    <div className={cn("relative w-full", className)}>
      <div
        ref={containerRef}
        className="w-full rounded-lg border border-border bg-card"
        style={{ height: `${height}px` }}
      />
      {/* Live price badge */}
      <div
        ref={badgeRef}
        className="absolute top-3 right-3 px-2 py-0.5 rounded text-xs font-mono font-semibold border transition-colors duration-300"
        style={{
          background: "rgba(59,130,246,0.1)",
          color: "#3b82f6",
          borderColor: "rgba(59,130,246,0.3)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
});
