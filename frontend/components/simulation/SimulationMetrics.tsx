"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPnlPercent, formatCountdown } from "@/lib/utils/simulation-helpers";
import { formatCurrency } from "@/lib/utils";
import { TrendingUp, TrendingDown, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface SimulationMetricsProps {
  currentPrice: number;
  entryPrice: number;
  predictedPrice: number;
  action: "BUY" | "SELL" | "HOLD";
  elapsedTime: number;
  remainingTime: number;
}

export function SimulationMetrics({
  currentPrice,
  entryPrice,
  predictedPrice,
  action,
  elapsedTime,
  remainingTime,
}: SimulationMetricsProps) {
  const priceChange = currentPrice - entryPrice;
  const priceChangePercent = (priceChange / entryPrice) * 100;

  let pnl = 0;
  let pnlPercent = 0;

  if (action === "BUY") {
    pnl = priceChange;
    pnlPercent = priceChangePercent;
  } else if (action === "SELL") {
    pnl = -priceChange;
    pnlPercent = -priceChangePercent;
  }

  const pnlFormatted = formatPnlPercent(pnlPercent);
  const predictionDiff = ((currentPrice - predictedPrice) / predictedPrice) * 100;

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {/* Current Price & P&L */}
      <Card variant="glass">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Current Price</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <p className="text-2xl font-mono font-bold">{formatCurrency(currentPrice)}</p>
            <div className="flex items-center gap-2">
              {pnlPercent > 0 && <TrendingUp className="size-4 text-green-500" />}
              {pnlPercent < 0 && <TrendingDown className="size-4 text-red-500" />}
              <span className={cn("text-sm font-mono", pnlFormatted.className)}>
                {pnlFormatted.value}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Entry: {formatCurrency(entryPrice)}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Prediction Accuracy */}
      <Card variant="glass">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Prediction Accuracy</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <p className="text-2xl font-mono font-bold">
              {formatCurrency(predictedPrice)}
            </p>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "text-sm font-mono",
                  Math.abs(predictionDiff) < 5
                    ? "text-green-500"
                    : Math.abs(predictionDiff) < 10
                    ? "text-yellow-500"
                    : "text-red-500"
                )}
              >
                {predictionDiff >= 0 ? "+" : ""}
                {predictionDiff.toFixed(2)}% vs predicted
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Target: {formatCurrency(predictedPrice)}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Time Remaining */}
      <Card variant="glass">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Time Remaining</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Clock className="size-5 text-primary" />
              <p className="text-2xl font-mono font-bold">
                {formatCountdown(remainingTime)}
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              Elapsed: {Math.floor(elapsedTime / 60000)}m {Math.floor((elapsedTime % 60000) / 1000)}s
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
