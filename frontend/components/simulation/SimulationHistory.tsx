"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SimulationStorage } from "@/lib/simulation/storage";
import { StoredSimulation } from "@/lib/types/simulation";
import { formatPnlPercent, getStatusVariant } from "@/lib/utils/simulation-helpers";
import { formatDate } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, Trash2, Eye } from "lucide-react";
import { cn } from "@/lib/utils";

interface SimulationHistoryProps {
  onViewSimulation?: (id: string) => void;
}

export function SimulationHistory({ onViewSimulation }: SimulationHistoryProps) {
  const [simulations, setSimulations] = useState<StoredSimulation[]>([]);
  const [stats, setStats] = useState(SimulationStorage.getStats());

  useEffect(() => {
    loadSimulations();
  }, []);

  const loadSimulations = () => {
    const stored = SimulationStorage.getAllSimulations();
    setSimulations(stored);
    setStats(SimulationStorage.getStats());
  };

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this analysis?")) {
      SimulationStorage.deleteSimulation(id);
      loadSimulations();
    }
  };

  if (simulations.length === 0) {
    return (
      <Card variant="glass">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">History</CardTitle>
          <CardDescription className="text-xs">Your past token analyses will appear here</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground text-center py-4">
            No analyses yet. Scan a token to see results here.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="glass">
      <CardHeader className="pb-3">
        <div className="space-y-2">
          <CardTitle className="text-base">History</CardTitle>
          <CardDescription className="text-xs">
            {stats.total} analyses • {stats.winRate.toFixed(1)}% win rate • Avg {stats.averagePnl >= 0 ? "+" : ""}{stats.averagePnl.toFixed(2)}%
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {simulations.slice(0, 10).map((sim) => {
            const pnlFormatted = formatPnlPercent(sim.result.profitLossPercent);
            const statusVariant = getStatusVariant(sim.result.status);
            const isProfit = sim.result.status === "profit";
            const isLoss = sim.result.status === "loss";
            const isEquilized = sim.result.status === "equilized";

            return (
              <div
                key={sim.id}
                className={cn(
                  "p-2.5 sm:p-3 rounded-lg border text-xs sm:text-sm transition-colors",
                  isProfit && "bg-green-500/5 border-green-500/20",
                  isLoss && "bg-red-500/5 border-red-500/20",
                  isEquilized && "bg-yellow-500/5 border-yellow-500/20"
                )}
              >
                <div className="flex items-start justify-between gap-2 sm:gap-4 flex-wrap">
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <code className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded">
                        {sim.coinAddress.slice(0, 6)}...
                      </code>
                      <Badge variant={statusVariant} className="text-xs shrink-0 px-1.5 py-0">
                        {isProfit && <TrendingUp className="size-2.5 mr-0.5" />}
                        {isLoss && <TrendingDown className="size-2.5 mr-0.5" />}
                        {isEquilized && <Minus className="size-2.5 mr-0.5" />}
                        {sim.result.action}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-xs flex-wrap">
                      <span className={cn("font-mono font-semibold", pnlFormatted.className)}>
                        {pnlFormatted.value}
                      </span>
                      <span className="text-muted-foreground">
                        {sim.result.accuracy.toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(sim.completedAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {onViewSimulation && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onViewSimulation(sim.id)}
                        className="h-7 w-7 p-0"
                      >
                        <Eye className="size-3" />
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(sim.id)}
                      className="h-7 w-7 p-0"
                    >
                      <Trash2 className="size-3" />
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
