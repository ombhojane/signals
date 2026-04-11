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
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Open Alpha Arena</h2>
        <div className="flex items-center gap-2">
           <AddAgentModal />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Chart & Rankings */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card variant="glass" className="p-4 gap-4 py-4">
             <div className="mb-4">
               <TimeRangeSelector value={timeRange} />
             </div>
             <PerformanceChart series={chartSeries} height={320} />
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
    <Suspense fallback={<div className="flex items-center justify-center p-12">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
