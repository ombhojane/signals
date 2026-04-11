"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TradeDecision } from "@/lib/types/simulation";
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/utils";

interface PredictionCardProps {
  prediction: TradeDecision;
  currentPrice: number;
}

export function PredictionCard({ prediction, currentPrice }: PredictionCardProps) {
  const isBuy = prediction.action === "BUY";
  const isSell = prediction.action === "SELL";
  const isHold = prediction.action === "HOLD";

  const safePrice = currentPrice || 0.000001;
  const priceChange = prediction.predictedValue - safePrice;
  const priceChangePercent = safePrice > 0 ? (priceChange / safePrice) * 100 : 0;

  return (
    <Card
      variant="glass"
      className={cn(
        "border-2",
        isBuy && "border-green-500/50 bg-green-500/5",
        isSell && "border-red-500/50 bg-red-500/5",
        isHold && "border-yellow-500/50 bg-yellow-500/5"
      )}
    >
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl">Prediction</CardTitle>
          <Badge
            variant={
              isBuy ? "default" : isSell ? "destructive" : "secondary"
            }
            className="text-lg px-4 py-1"
          >
            {prediction.action}
          </Badge>
        </div>
        <CardDescription>AI trading decision with confidence score</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Confidence Meter */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Confidence</span>
            <span className="font-semibold">{prediction.confidence}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
            <div
              className={cn(
                "h-full transition-all duration-500",
                isBuy && "bg-green-500",
                isSell && "bg-red-500",
                isHold && "bg-yellow-500"
              )}
              style={{ width: `${prediction.confidence}%` }}
            />
          </div>
        </div>

        {/* Price Prediction */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Current Price</p>
            <p className="text-lg font-mono font-semibold">{formatCurrency(currentPrice)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Predicted Price</p>
            <p className="text-lg font-mono font-semibold">{formatCurrency(prediction.predictedValue)}</p>
          </div>
        </div>

        {/* Price Change */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
          {isBuy && <TrendingUp className="size-5 text-green-500" />}
          {isSell && <TrendingDown className="size-5 text-red-500" />}
          {isHold && <Minus className="size-5 text-yellow-500" />}
          <div className="flex-1">
            <p className="text-xs text-muted-foreground">Expected Change</p>
            <p
              className={cn(
                "text-lg font-mono font-semibold",
                priceChangePercent > 0 ? "text-green-500" : priceChangePercent < 0 ? "text-red-500" : "text-muted-foreground"
              )}
            >
              {priceChangePercent >= 0 ? "+" : ""}
              {priceChangePercent.toFixed(2)}%
            </p>
          </div>
        </div>

        {/* Reasoning */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Reasoning</p>
          <p className="text-sm text-muted-foreground leading-relaxed">{prediction.reasoning}</p>
        </div>

        {/* Risk Assessment */}
        <div className="space-y-2 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-4 text-yellow-500" />
            <p className="text-sm font-medium">Risk Assessment</p>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{prediction.riskAssessment}</p>
        </div>

        {/* Price Targets */}
        {(prediction.priceTarget || prediction.stopLoss) && (
          <div className="grid grid-cols-2 gap-4 pt-2 border-t">
            {prediction.priceTarget && (
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Price Target</p>
                <p className="text-sm font-mono font-semibold text-green-500">
                  {formatCurrency(prediction.priceTarget)}
                </p>
              </div>
            )}
            {prediction.stopLoss && (
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Stop Loss</p>
                <p className="text-sm font-mono font-semibold text-red-500">
                  {formatCurrency(prediction.stopLoss)}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
