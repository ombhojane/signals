"use client";

import {
  AreaSeries,
  createChart,
  ColorType,
  IChartApi,
  ISeriesApi,
  UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

export interface VolumePoint {
  time: UTCTimestamp;
  value: number;
}

export function VolumeChart({ data, height = 260 }: { data: VolumePoint[]; height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Helper to get computed CSS variable
    const getCssVar = (name: string) => {
      if (typeof window === 'undefined') return '';
      return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    };

    const primaryHex = getCssVar('--primary') || '#a7cbeb';
    
    // Parse hex to rgb for rgba usage
    const hexToRgb = (hex: string) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '167, 203, 235';
    };
    
    const primaryRgb = hexToRgb(primaryHex);

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#131313" },
        textColor: "#acabaa",
        fontFamily: "var(--font-mono), ui-monospace, monospace",
      },
      grid: {
        vertLines: { color: "rgba(72,72,72,0.2)" },
        horzLines: { color: "rgba(72,72,72,0.2)" },
      },
      timeScale: {
        timeVisible: true,
        borderColor: "rgba(72,72,72,0.3)",
      },
      rightPriceScale: {
        borderColor: "rgba(72,72,72,0.3)",
      },
      crosshair: {
        vertLine: { color: `rgba(${primaryRgb}, 0.3)`, labelBackgroundColor: primaryHex },
        horzLine: { color: `rgba(${primaryRgb}, 0.3)`, labelBackgroundColor: primaryHex },
      },
      width: containerRef.current.clientWidth,
      height,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: primaryHex,
      topColor: `rgba(${primaryRgb}, 0.35)`,
      bottomColor: `rgba(${primaryRgb}, 0.0)`,
      lineWidth: 2,
      priceFormat: {
        type: "price",
        precision: 2,
        minMove: 0.01,
      },
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current) return;
    if (data.length === 0) {
      seriesRef.current.setData([]);
      return;
    }
    seriesRef.current.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return <div ref={containerRef} style={{ width: "100%" }} />;
}
