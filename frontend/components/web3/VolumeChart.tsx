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
        vertLine: { color: "rgba(167,203,235,0.3)", labelBackgroundColor: "#a7cbeb" },
        horzLine: { color: "rgba(167,203,235,0.3)", labelBackgroundColor: "#a7cbeb" },
      },
      width: containerRef.current.clientWidth,
      height,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: "#a7cbeb",
      topColor: "rgba(167,203,235,0.35)",
      bottomColor: "rgba(167,203,235,0.0)",
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
