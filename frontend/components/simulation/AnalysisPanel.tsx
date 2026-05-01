"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TokenSnapshot } from "@/lib/types/simulation";
import { TrendingUp, TrendingDown, Shield, MessageSquare, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

interface AnalysisPanelProps {
  snapshot: TokenSnapshot;
}

export function AnalysisPanel({ snapshot }: AnalysisPanelProps) {
  const [flash, setFlash] = useState(false);
  const prevRef = useRef<TokenSnapshot | null>(null);

  useEffect(() => {
    if (prevRef.current && prevRef.current !== snapshot) {
      setFlash(true);
      const t = setTimeout(() => setFlash(false), 400);
      return () => clearTimeout(t);
    }
    prevRef.current = snapshot;
  }, [snapshot]);

  const getRSIColor = (rsi: number) => {
    if (rsi < 30) return "text-green-500";
    if (rsi > 70) return "text-red-500";
    return "text-yellow-500";
  };

  const getRugScoreColor = (score: number) => {
    if (score < 30) return "text-green-500";
    if (score > 70) return "text-red-500";
    return "text-yellow-500";
  };

  const getSentimentColor = (score: number) => {
    if (score > 70) return "text-green-500";
    if (score < 30) return "text-red-500";
    return "text-yellow-500";
  };

  return (
    <Card variant="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Market Analysis</CardTitle>
            <CardDescription>Technical, on-chain, and social indicators</CardDescription>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-green-400 font-medium">
            <span className="relative flex size-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full size-2 bg-green-500" />
            </span>
            Live
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-3 overflow-hidden">
          {/* Technical Indicators */}
          <div className="space-y-3 overflow-hidden">
            <div className="flex items-center gap-2 min-w-0">
              <BarChart3 className="size-4 text-primary shrink-0" />
              <h3 className="font-semibold text-sm truncate">Technical</h3>
            </div>
            <div className="space-y-2 text-sm overflow-hidden">
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">RSI (14)</span>
                <span className={cn("font-mono font-medium shrink-0", getRSIColor(snapshot.rsi))}>
                  {snapshot.rsi.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">MACD</span>
                <span className={cn("font-mono shrink-0", snapshot.macd > snapshot.macdSignal ? "text-green-500" : "text-red-500")}>
                  {snapshot.macd > snapshot.macdSignal ? "↑ Bullish" : "↓ Bearish"}
                </span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Bollinger</span>
                <span className="font-mono text-xs shrink-0">
                  {snapshot.bollingerPosition > 0.8
                    ? "Upper Band"
                    : snapshot.bollingerPosition < -0.8
                    ? "Lower Band"
                    : "Mid Range"}
                </span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Volatility</span>
                <span className="font-mono shrink-0">{(snapshot.volatility * 100).toFixed(2)}%</span>
              </div>
            </div>
          </div>

          {/* On-Chain Safety */}
          <div className="space-y-3 overflow-hidden">
            <div className="flex items-center gap-2 min-w-0">
              <Shield className="size-4 text-primary shrink-0" />
              <h3 className="font-semibold text-sm truncate">On-Chain</h3>
            </div>
            <div className="space-y-2 text-sm overflow-hidden">
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Rug Score</span>
                <span className={cn("font-mono font-medium shrink-0", getRugScoreColor(snapshot.rugScore))}>
                  {snapshot.rugScore}/100
                </span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Smart Money</span>
                <Badge
                  variant={
                    snapshot.smartMoneyFlow === "buying"
                      ? "default"
                      : snapshot.smartMoneyFlow === "selling"
                      ? "destructive"
                      : "secondary"
                  }
                  className="text-xs shrink-0"
                >
                  {snapshot.smartMoneyFlow}
                </Badge>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Liquidity Lock</span>
                <Badge variant={snapshot.liquidityLocked ? "default" : "destructive"} className="text-xs shrink-0">
                  {snapshot.liquidityLocked ? "Locked" : "Unlocked"}
                </Badge>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Holders</span>
                <span className="font-mono shrink-0">{snapshot.holderCount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Top 10%</span>
                <span className="font-mono shrink-0">{snapshot.top10HolderPct.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Social Sentiment */}
          <div className="space-y-3 overflow-hidden">
            <div className="flex items-center gap-2 min-w-0">
              <MessageSquare className="size-4 text-primary shrink-0" />
              <h3 className="font-semibold text-sm truncate">Social</h3>
            </div>
            <div className="space-y-2 text-sm overflow-hidden">
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Sentiment</span>
                <span className={cn("font-mono font-medium shrink-0", getSentimentColor(snapshot.sentimentScore))}>
                  {snapshot.sentimentScore}/100
                </span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Mentions (24h)</span>
                <span className="font-mono shrink-0">{snapshot.mentions24h.toLocaleString()}</span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Influencers</span>
                <span className="font-mono shrink-0">{snapshot.influencerMentions}</span>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Trending</span>
                <Badge variant={snapshot.trending ? "default" : "secondary"} className="text-xs shrink-0">
                  {snapshot.trending ? "Yes" : "No"}
                </Badge>
              </div>
              <div className="flex justify-between min-w-0">
                <span className="text-muted-foreground truncate">Community</span>
                <span className="font-mono shrink-0">{snapshot.communitySize.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Overall Risk Assessment */}
        <div className="mt-6 pt-4 border-t overflow-hidden">
          <div className="flex items-center justify-between gap-2 min-w-0">
            <span className="text-sm font-medium truncate">Overall Risk Assessment</span>
            <Badge
              variant={
                snapshot.rugScore < 30 && snapshot.liquidityLocked
                  ? "default"
                  : snapshot.rugScore > 70
                  ? "destructive"
                  : "secondary"
              }
              className="shrink-0"
            >
              {snapshot.rugScore < 30 && snapshot.liquidityLocked
                ? "Low Risk"
                : snapshot.rugScore > 70
                ? "High Risk"
                : "Moderate Risk"}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
