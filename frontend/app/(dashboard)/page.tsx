"use client";

import { useEffect, useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { 
  generateAgents, 
  generatePortfolioHistory, 
  generatePositions, 
  generateDecisions, 
  generateOrders, 
  generateTrades,
  getChartData
} from "@/lib/mock-data";
import { TimeRange } from "@/lib/types";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { TimeRangeSelector } from "@/components/charts/TimeRangeSelector";
import { AgentRankings } from "@/components/dashboard/AgentRankings";
import { AgentDetails } from "@/components/dashboard/AgentDetails";
import { ModelChat } from "@/components/dashboard/ModelChat";
import { AddAgentModal } from "@/components/modals/AddAgentModal";
import { QuickAnalysis } from "@/components/dashboard/QuickAnalysis";
import { TrendingTokens } from "@/components/dashboard/TrendingTokens";
import { Card } from "@/components/ui/card";

function MarketSentiment() {
  return (
    <div className="surface-high rounded-xl p-5 ghost-border">
      <div className="flex items-center gap-2 mb-3">
        <div className="zen-pulse" />
        <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground" style={{ fontFamily: 'var(--font-inter), sans-serif' }}>Market Sentiment</span>
      </div>
      <p className="text-sm text-muted-foreground leading-relaxed" style={{ fontFamily: 'var(--font-inter), sans-serif' }}>
        The market is showing strong upward momentum driven by institutional inflows. 
        Liquidity is concentrating in Tier 1 assets.
      </p>
    </div>
  );
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const timeRange = (searchParams.get("range") as TimeRange) || "5m";
  
  const [mounted, setMounted] = useState(false);
  
  const { agents, snapshots, positions, decisions, orders, trades } = useMemo(() => {
    const agents = generateAgents();
    const snapshots = generatePortfolioHistory(agents, timeRange);
    const allPositions = agents.flatMap(a => generatePositions(a.id));
    const allDecisions = agents.flatMap(a => generateDecisions(a.id));
    const allOrders = agents.flatMap(a => generateOrders(a.id));
    const allTrades = agents.flatMap(a => generateTrades(a.id));
    
    return { 
      agents, 
      snapshots, 
      positions: allPositions, 
      decisions: allDecisions, 
      orders: allOrders, 
      trades: allTrades 
    };
  }, [timeRange]);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const chartSeries = agents.map(agent => ({
    name: agent.name,
    color: agent.color,
    data: getChartData(snapshots, agent.id)
  }));

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tighter">
            Welcome back, <span style={{ color: '#a7cbeb' }}>Curator Alpha</span>
          </h2>
          <p className="text-sm text-muted-foreground mt-1" style={{ fontFamily: 'var(--font-inter), sans-serif' }}>
            Your personalized intelligence dashboard
          </p>
        </div>
        <div className="flex items-center gap-2">
          <AddAgentModal />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Chart & Rankings */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Market Sentiment */}
          <MarketSentiment />
          
          {/* Performance Chart */}
          <Card variant="glass" className="p-6 gap-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground" style={{ fontFamily: 'var(--font-inter), sans-serif' }}>Performance Orbit</span>
              <TimeRangeSelector value={timeRange} />
            </div>
            <PerformanceChart series={chartSeries} height={360} />
          </Card>
          
          <AgentRankings agents={agents} />
        </div>

        {/* Right Column: Agent Details + Model Chat */}
        <div className="flex flex-col gap-6">
          <div className="h-[400px]">
            <AgentDetails 
              agents={agents}
              positions={positions}
              decisions={decisions}
              orders={orders}
              trades={trades}
            />
          </div>
          
          <div className="h-[350px]">
            <ModelChat />
          </div>

          <QuickAnalysis />
          <TrendingTokens />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center p-12">
        <div className="flex flex-col items-center gap-3">
          <div className="zen-pulse" style={{ width: '10px', height: '10px' }} />
          <span className="text-xs text-muted-foreground" style={{ fontFamily: 'var(--font-inter), sans-serif' }}>Loading intelligence...</span>
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
