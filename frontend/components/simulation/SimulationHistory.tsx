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
        <CardHeader>
        <CardTitle>History</CardTitle>
        <CardDescription>Your past token analyses will appear here</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            No analyses yet. Scan a token to see results here.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
          <CardTitle>History</CardTitle>
          <CardDescription>
            {stats.total} analyses • {stats.winRate.toFixed(1)}% win rate • Avg P&L:{" "}
              {stats.averagePnl >= 0 ? "+" : ""}
              {stats.averagePnl.toFixed(2)}%
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {simulations.map((sim) => {
            const pnlFormatted = formatPnlPercent(sim.result.profitLossPercent);
            const statusVariant = getStatusVariant(sim.result.status);
            const isProfit = sim.result.status === "profit";
            const isLoss = sim.result.status === "loss";
            const isEquilized = sim.result.status === "equilized";

            return (
              <div
                key={sim.id}
                className={cn(
                  "p-4 rounded-lg border transition-colors",
                  isProfit && "bg-green-500/5 border-green-500/20",
                  isLoss && "bg-red-500/5 border-red-500/20",
                  isEquilized && "bg-yellow-500/5 border-yellow-500/20"
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <code className="text-xs font-mono bg-muted px-2 py-1 rounded">
                        {sim.coinAddress.slice(0, 8)}...
                      </code>
                      <Badge variant={statusVariant} className="text-xs">
                        {isProfit && <TrendingUp className="size-3 mr-1" />}
                        {isLoss && <TrendingDown className="size-3 mr-1" />}
                        {isEquilized && <Minus className="size-3 mr-1" />}
                        {sim.result.action}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {sim.result.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className={cn("font-mono font-semibold", pnlFormatted.className)}>
                        {pnlFormatted.value}
                      </span>
                      <span className="text-muted-foreground">
                        Accuracy: {sim.result.accuracy.toFixed(1)}%
                      </span>
                      <span className="text-muted-foreground">
                        {sim.duration}m duration
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(sim.completedAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {onViewSimulation && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onViewSimulation(sim.id)}
                      >
                        <Eye className="size-4" />
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(sim.id)}
                    >
                      <Trash2 className="size-4" />
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
