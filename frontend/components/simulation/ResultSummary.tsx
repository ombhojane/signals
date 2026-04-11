"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SimulationResult } from "@/lib/types/simulation";
import { formatPnlPercent, formatPnl, getStatusVariant } from "@/lib/utils/simulation-helpers";
import { formatCurrency } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, Target, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResultSummaryProps {
  result: SimulationResult;
}

export function ResultSummary({ result }: ResultSummaryProps) {
  const pnlFormatted = formatPnlPercent(result.profitLossPercent);
  const pnlAmountFormatted = formatPnl(result.profitLoss);
  const statusVariant = getStatusVariant(result.status);

  const isProfit = result.status === "profit";
  const isLoss = result.status === "loss";
  const isEquilized = result.status === "equilized";

  return (
    <Card
      variant="glass"
      className={cn(
        "border-2",
        isProfit && "border-green-500/50 bg-green-500/5",
        isLoss && "border-red-500/50 bg-red-500/5",
        isEquilized && "border-yellow-500/50 bg-yellow-500/5"
      )}
    >
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl">Analysis Complete</CardTitle>
          <Badge variant={statusVariant} className="text-lg px-4 py-1">
            {isProfit && <TrendingUp className="size-4 mr-1" />}
            {isLoss && <TrendingDown className="size-4 mr-1" />}
            {isEquilized && <Minus className="size-4 mr-1" />}
            {result.status.toUpperCase()}
          </Badge>
        </div>
        <CardDescription>Final results and P&L metrics</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* P&L Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Profit/Loss</p>
            <p className={cn("text-2xl font-mono font-bold", pnlFormatted.className)}>
              {pnlFormatted.value}
            </p>
            <p className={cn("text-sm font-mono", pnlAmountFormatted.className)}>
              {pnlAmountFormatted.value}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Prediction Accuracy</p>
            <p
              className={cn(
                "text-2xl font-mono font-bold",
                result.accuracy > 80
                  ? "text-green-500"
                  : result.accuracy > 60
                  ? "text-yellow-500"
                  : "text-red-500"
              )}
            >
              {result.accuracy.toFixed(1)}%
            </p>
            <p className="text-xs text-muted-foreground">
              {Math.abs(result.actualPrice - result.predictedPrice) < result.predictedPrice * 0.05
                ? "Very accurate"
                : Math.abs(result.actualPrice - result.predictedPrice) < result.predictedPrice * 0.1
                ? "Accurate"
                : "Needs improvement"}
            </p>
          </div>
        </div>

        {/* Price Comparison */}
        <div className="space-y-3 p-4 rounded-lg bg-muted/50">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Entry Price</span>
            <span className="font-mono font-semibold">{formatCurrency(result.entryPrice)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Exit Price</span>
            <span className="font-mono font-semibold">{formatCurrency(result.exitPrice)}</span>
          </div>
          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-sm text-muted-foreground flex items-center gap-2">
              <Target className="size-4" />
              Predicted Price
            </span>
            <span className="font-mono font-semibold">{formatCurrency(result.predictedPrice)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground flex items-center gap-2">
              <CheckCircle2 className="size-4" />
              Actual Price
            </span>
            <span className="font-mono font-semibold">{formatCurrency(result.actualPrice)}</span>
          </div>
        </div>

        {/* Price Change */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
          {isProfit && <TrendingUp className="size-5 text-green-500" />}
          {isLoss && <TrendingDown className="size-5 text-red-500" />}
          {isEquilized && <Minus className="size-5 text-yellow-500" />}
          <div className="flex-1">
            <p className="text-sm text-muted-foreground">Price Change</p>
            <p
              className={cn(
                "text-lg font-mono font-semibold",
                result.priceChangePercent > 0
                  ? "text-green-500"
                  : result.priceChangePercent < 0
                  ? "text-red-500"
                  : "text-muted-foreground"
              )}
            >
              {result.priceChangePercent >= 0 ? "+" : ""}
              {result.priceChangePercent.toFixed(2)}%
            </p>
          </div>
        </div>

        {/* Action & Duration */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Action</p>
            <Badge variant={result.action === "BUY" ? "default" : result.action === "SELL" ? "destructive" : "secondary"}>
              {result.action}
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Duration</p>
            <p className="text-sm font-semibold">{result.duration} minutes</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
