"use client";

import { useEffect, useRef, useCallback } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, Time, LineSeries } from "lightweight-charts";
import { formatCurrency } from "@/lib/utils";

interface ChartData {
  time: number;
  value: number;
}

interface SeriesData {
  name: string;
  color: string;
  data: ChartData[];
}

interface PerformanceChartProps {
  series: SeriesData[];
  height?: number;
}

export function PerformanceChart({ series, height = 400 }: PerformanceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());

  // Single effect to handle chart lifecycle
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
        fontFamily: "JetBrains Mono, ui-monospace, monospace",
      },
      grid: {
        vertLines: { color: "rgba(39, 39, 42, 0.5)" },
        horzLines: { color: "rgba(39, 39, 42, 0.5)" },
      },
      rightPriceScale: {
        borderColor: "rgba(39, 39, 42, 1)",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "rgba(39, 39, 42, 1)",
        timeVisible: true,
        secondsVisible: false,
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

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };
    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      seriesRefs.current.clear();
      chart.remove();
      chartRef.current = null;
    };
  }, [height]);

  // Update series data when series prop changes
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    // Clear old series
    seriesRefs.current.forEach((s) => {
      try {
        chart.removeSeries(s);
      } catch (e) {
        // Series may already be removed
      }
    });
    seriesRefs.current.clear();

    // Add new series
    series.forEach((s) => {
      if (s.data.length === 0) return;

      const lineSeries = chart.addSeries(LineSeries, {
        color: s.color,
        lineWidth: 2,
        title: s.name,
        priceFormat: { type: "price", precision: 2, minMove: 0.01 },
        lastValueVisible: true,
        priceLineVisible: false,
      });

      // Sort data by time and set
      const sortedData = [...s.data]
        .sort((a, b) => a.time - b.time)
        .map((d) => ({ time: d.time as Time, value: d.value }));

      lineSeries.setData(sortedData);
      seriesRefs.current.set(s.name, lineSeries);
    });

    // Fit content after data is set
    if (series.length > 0 && series.some((s) => s.data.length > 0)) {
      chart.timeScale().fitContent();
    }
  }, [series]);

  return (
    <div className="relative w-full">
      {/* Legend */}
      <div className="mb-4 flex flex-wrap items-center gap-4">
        {series.map((s) => (
          <div key={s.name} className="flex items-center gap-2 text-xs font-medium">
            <span
              className="h-3 w-3 rounded-sm"
              style={{ backgroundColor: s.color }}
            />
            <span className="text-foreground">{s.name}</span>
          </div>
        ))}
      </div>
      {/* Chart container */}
      <div
        ref={chartContainerRef}
        className="w-full rounded-lg border border-border bg-card"
        style={{ height: `${height}px` }}
      />
    </div>
  );
}
