"use client";

import { useEffect, useMemo, useState } from "react";
import { formatCurrency, formatPercent, formatDate } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Trophy, Crown, ChevronDown, History, TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { generateAgents, generateTrades, calculateAgentStats } from "@/lib/mock-data";
import { SimulationStorage } from "@/lib/simulation/storage";
import { StoredSimulation } from "@/lib/types/simulation";
import { cn } from "@/lib/utils";

const COMPETITIONS = [
  { id: "aggregate", label: "Aggregate Index" },
  { id: "baseline", label: "New Baseline" },
  { id: "monk", label: "Monk Mode" },
  { id: "awareness", label: "Situational Awareness" },
  { id: "leverage", label: "Max Leverage" },
];

export default function LeaderboardPage() {
  const [competition, setCompetition] = useState("aggregate");
  const [showAverage, setShowAverage] = useState(false);
  const [activeTab, setActiveTab] = useState<"arena" | "scans">("arena");
  const [scans, setScans] = useState<StoredSimulation[]>([]);
  const [scanStats, setScanStats] = useState(SimulationStorage.getStats());

  useEffect(() => {
    const stored = SimulationStorage.getAllSimulations();
    setScans(stored);
    setScanStats(SimulationStorage.getStats());
  }, []);

  const leaderboardData = useMemo(() => {
    const agents = generateAgents();

    return agents.map(agent => {
      const trades = generateTrades(agent.id, 50);
      const stats = calculateAgentStats(trades);
      const returnPct = ((agent.accountValue - 10000) / 10000) * 100;
      const fees = trades.reduce((sum, t) => sum + t.totalFees, 0);
      const sharpe = (returnPct / 15) * (Math.random() * 0.5 + 0.5);

      return {
        ...agent,
        stats,
        returnPct: Math.round(returnPct * 100) / 100,
        fees: Math.round(fees * 100) / 100,
        sharpe: Math.round(sharpe * 1000) / 1000,
        trades: trades.length,
      };
    }).sort((a, b) => b.accountValue - a.accountValue);
  }, [competition]);

  const winner = leaderboardData[0];

  const bestScan = scans.length > 0
    ? scans.reduce((best, s) => s.result.profitLossPercent > best.result.profitLossPercent ? s : best, scans[0])
    : null;
  const worstScan = scans.length > 0
    ? scans.reduce((worst, s) => s.result.profitLossPercent < worst.result.profitLossPercent ? s : worst, scans[0])
    : null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Leaderboard</h2>
          <p className="text-muted-foreground">Top performing AI agents by P&L and ROI</p>
        </div>
      </div>

      {/* Main Tab Switch */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "arena" | "scans")}>
        <TabsList className="h-9">
          <TabsTrigger value="arena" className="text-xs px-4 gap-1.5">
            <Trophy className="size-3.5" /> AI Arena
          </TabsTrigger>
          <TabsTrigger value="scans" className="text-xs px-4 gap-1.5">
            <History className="size-3.5" /> My Scans
            {scans.length > 0 && (
              <Badge variant="secondary" className="ml-1 text-[10px] px-1.5 py-0">{scans.length}</Badge>
            )}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {activeTab === "arena" && (
        <>
          {/* Competition Filters */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="font-medium">COMPETITION:</span>
              <Tabs value={competition} onValueChange={setCompetition}>
                <TabsList className="h-8">
                  {COMPETITIONS.map((c) => (
                    <TabsTrigger key={c.id} value={c.id} className="text-xs px-3 h-6">
                      {c.label}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <Checkbox
                id="average"
                checked={showAverage}
                onCheckedChange={(v) => setShowAverage(!!v)}
              />
              <label htmlFor="average" className="text-muted-foreground cursor-pointer">
                AVERAGE
              </label>
            </div>
          </div>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-500" />
                Live Rankings
              </CardTitle>
              <CardDescription>
                Real-time performance metrics of all active trading agents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader className="bg-muted/30">
                  <TableRow>
                    <TableHead className="w-[50px]">Rank</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Account Value</TableHead>
                    <TableHead>Return %</TableHead>
                    <TableHead>Total P&L</TableHead>
                    <TableHead>Fees</TableHead>
                    <TableHead>Win Rate</TableHead>
                    <TableHead>Biggest Win</TableHead>
                    <TableHead>Biggest Loss</TableHead>
                    <TableHead>Sharpe</TableHead>
                    <TableHead>Trades</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaderboardData.map((data, index) => {
                    const rank = index + 1;
                    const winRate = 50 + (data.stats.totalPnl > 0 ? Math.random() * 15 : -Math.random() * 10);

                    return (
                      <TableRow key={data.id} className="hover:bg-muted/5">
                        <TableCell className="font-mono font-medium tabular-nums text-muted-foreground">
                          {rank}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div
                              className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold"
                              style={{ backgroundColor: `${data.color}30`, color: data.color }}
                            >
                              {data.model.substring(0, 2).toUpperCase()}
                            </div>
                            <span className="font-medium">{data.name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono font-bold tabular-nums">
                          {formatCurrency(data.accountValue)}
                        </TableCell>
                        <TableCell className={`font-mono tabular-nums ${data.returnPct >= 0 ? "text-green-500" : "text-red-500"}`}>
                          {data.returnPct >= 0 ? "+" : ""}{data.returnPct.toFixed(2)}%
                        </TableCell>
                        <TableCell className={`font-mono tabular-nums ${data.stats.totalPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                          {data.stats.totalPnl >= 0 ? "+" : ""}{formatCurrency(data.stats.totalPnl)}
                        </TableCell>
                        <TableCell className="font-mono tabular-nums text-muted-foreground">
                          {formatCurrency(data.fees)}
                        </TableCell>
                        <TableCell className="font-mono tabular-nums">
                          {formatPercent(winRate)}
                        </TableCell>
                        <TableCell className="font-mono tabular-nums text-green-500">
                          {formatCurrency(data.stats.biggestWin)}
                        </TableCell>
                        <TableCell className="font-mono tabular-nums text-red-500">
                          {formatCurrency(data.stats.biggestLoss)}
                        </TableCell>
                        <TableCell className="font-mono tabular-nums">
                          {data.sharpe.toFixed(3)}
                        </TableCell>
                        <TableCell className="font-mono tabular-nums text-muted-foreground">
                          {data.trades}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Winning Model Summary */}
          <Card className="border-border bg-card">
            <CardContent className="pt-6">
              <Collapsible defaultOpen={false} className="group">
                <div className="flex items-start gap-8">
                  <div className="flex-shrink-0">
                    <div className="text-orange-500 text-sm font-medium mb-1">WINNING MODEL</div>
                    <div className="flex items-center gap-2">
                      <Crown className="h-5 w-5 text-orange-500" />
                      <span className="text-xl font-bold">{winner.name}</span>
                    </div>
                    <div className="mt-2 text-muted-foreground text-sm">TOTAL EQUITY</div>
                    <div className="font-mono text-2xl font-bold tabular-nums">{formatCurrency(winner.accountValue)}</div>
                    <CollapsibleTrigger asChild>
                      <Button variant="ghost" size="sm" className="mt-3 gap-1.5 text-muted-foreground">
                        <ChevronDown className="h-4 w-4 transition-transform duration-150 group-data-[state=open]:rotate-180" />
                        <span>Expand details</span>
                      </Button>
                    </CollapsibleTrigger>
                  </div>

                  <div className="flex-1 flex items-end gap-2 h-32">
                    {leaderboardData.slice(0, 8).map((agent, i) => {
                      const height = ((agent.accountValue - 9000) / 2000) * 100;
                      return (
                        <div key={agent.id} className="flex-1 flex flex-col items-center gap-1">
                          <div className="font-mono text-[10px] font-bold tabular-nums">
                            {formatCurrency(agent.accountValue).replace("$", "")}
                          </div>
                          <div
                            className="w-full rounded-t transition-all"
                            style={{
                              height: `${Math.max(20, Math.min(100, height))}%`,
                              backgroundColor: agent.color
                            }}
                          />
                          <div className="text-[9px] text-muted-foreground text-center truncate w-full">
                            {agent.name.split("-")[0]}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                <CollapsibleContent>
                  <div className="mt-6 pt-6 border-t border-border grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Return %</div>
                      <div className={`font-mono font-medium tabular-nums ${winner.returnPct >= 0 ? "text-success" : "text-destructive"}`}>
                        {winner.returnPct >= 0 ? "+" : ""}{winner.returnPct.toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Total P&L</div>
                      <div className={`font-mono font-medium tabular-nums ${winner.stats.totalPnl >= 0 ? "text-success" : "text-destructive"}`}>
                        {winner.stats.totalPnl >= 0 ? "+" : ""}{formatCurrency(winner.stats.totalPnl)}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Fees</div>
                      <div className="font-mono font-medium tabular-nums">{formatCurrency(winner.fees)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Trades</div>
                      <div className="font-mono font-medium tabular-nums">{winner.trades}</div>
                    </div>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </CardContent>
          </Card>
        </>
      )}

      {activeTab === "scans" && (
        <>
          {/* Scan Stats Summary */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card className="border-border bg-card">
              <CardContent className="pt-4 pb-4">
                <div className="text-xs text-muted-foreground">Total Scans</div>
                <div className="font-mono text-xl font-bold tabular-nums">{scanStats.total}</div>
              </CardContent>
            </Card>
            <Card className="border-border bg-card">
              <CardContent className="pt-4 pb-4">
                <div className="text-xs text-muted-foreground">Win Rate</div>
                <div className={cn(
                  "font-mono text-xl font-bold tabular-nums",
                  scanStats.winRate >= 50 ? "text-green-500" : "text-red-500"
                )}>
                  {scanStats.winRate.toFixed(1)}%
                </div>
              </CardContent>
            </Card>
            <Card className="border-border bg-card">
              <CardContent className="pt-4 pb-4">
                <div className="text-xs text-muted-foreground">Avg P&L</div>
                <div className={cn(
                  "font-mono text-xl font-bold tabular-nums",
                  scanStats.averagePnl >= 0 ? "text-green-500" : "text-red-500"
                )}>
                  {scanStats.averagePnl >= 0 ? "+" : ""}{scanStats.averagePnl.toFixed(2)}%
                </div>
              </CardContent>
            </Card>
            <Card className="border-border bg-card">
              <CardContent className="pt-4 pb-4">
                <div className="text-xs text-muted-foreground">Best Scan</div>
                <div className="font-mono text-xl font-bold tabular-nums text-green-500">
                  {bestScan ? `+${bestScan.result.profitLossPercent.toFixed(2)}%` : '--'}
                </div>
              </CardContent>
            </Card>
            <Card className="border-border bg-card">
              <CardContent className="pt-4 pb-4">
                <div className="text-xs text-muted-foreground">Worst Scan</div>
                <div className="font-mono text-xl font-bold tabular-nums text-red-500">
                  {worstScan ? `${worstScan.result.profitLossPercent.toFixed(2)}%` : '--'}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Scan History Table */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5 text-primary" />
                Scan History
              </CardTitle>
              <CardDescription>
                {scans.length > 0
                  ? `${scans.length} completed scans from your simulation sessions`
                  : "Run some token scans to see your history here"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {scans.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <History className="size-8 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No scans yet. Go to the Simulation page to scan tokens.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader className="bg-muted/30">
                    <TableRow>
                      <TableHead>Token</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Entry Price</TableHead>
                      <TableHead>Exit Price</TableHead>
                      <TableHead>P&L %</TableHead>
                      <TableHead>Accuracy</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {scans.map((sim) => {
                      const isProfit = sim.result.status === "profit";
                      const isLoss = sim.result.status === "loss";
                      return (
                        <TableRow key={sim.id} className="hover:bg-muted/5">
                          <TableCell>
                            <code className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded">
                              {sim.coinAddress.slice(0, 6)}...{sim.coinAddress.slice(-4)}
                            </code>
                          </TableCell>
                          <TableCell>
                            <Badge variant={sim.result.action === 'BUY' ? 'default' : sim.result.action === 'SELL' ? 'destructive' : 'secondary'} className="text-[10px]">
                              {sim.result.action}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono tabular-nums text-xs">
                            ${sim.result.entryPrice < 0.01 ? sim.result.entryPrice.toFixed(8) : sim.result.entryPrice.toFixed(4)}
                          </TableCell>
                          <TableCell className="font-mono tabular-nums text-xs">
                            ${sim.result.exitPrice < 0.01 ? sim.result.exitPrice.toFixed(8) : sim.result.exitPrice.toFixed(4)}
                          </TableCell>
                          <TableCell className={cn(
                            "font-mono font-bold tabular-nums",
                            isProfit ? "text-green-500" : isLoss ? "text-red-500" : "text-yellow-500"
                          )}>
                            {sim.result.profitLossPercent >= 0 ? "+" : ""}{sim.result.profitLossPercent.toFixed(2)}%
                          </TableCell>
                          <TableCell className="font-mono tabular-nums text-xs">
                            {sim.result.accuracy.toFixed(1)}%
                          </TableCell>
                          <TableCell className="font-mono tabular-nums text-xs text-muted-foreground">
                            {sim.duration}m
                          </TableCell>
                          <TableCell>
                            <div className={cn(
                              "inline-flex items-center gap-1 text-[10px] font-medium",
                              isProfit ? "text-green-500" : isLoss ? "text-red-500" : "text-yellow-500"
                            )}>
                              {isProfit && <TrendingUp className="size-3" />}
                              {isLoss && <TrendingDown className="size-3" />}
                              {!isProfit && !isLoss && <Minus className="size-3" />}
                              {sim.result.status}
                            </div>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {formatDate(sim.completedAt)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
