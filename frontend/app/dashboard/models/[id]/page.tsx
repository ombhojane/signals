"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Bot, ExternalLink, Share2 } from "lucide-react";
import { MODEL_CONFIGS, AGENT_COLORS, PROVIDER_NAMES } from "@/lib/constants";
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
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { AgentDetails } from "@/components/dashboard/AgentDetails";
import { TimeRangeSelector } from "@/components/charts/TimeRangeSelector";
import { notFound } from "next/navigation";

// Next.js 15/16 params are async
type Params = Promise<{ id: string }>;

export default function ModelDetailsPage({ params }: { params: Params }) {
  // Use React.use() to unwrap params in Client Component (Next.js 16 pattern)
  const { id } = use(params);
  
  const [timeRange, setTimeRange] = useState<TimeRange>("5m");
  const [mounted, setMounted] = useState(false);

  const modelConfig = MODEL_CONFIGS.find(m => m.id === id);
  
  // Simulation data for this specific model
  const data = useMemo(() => {
    if (!modelConfig) return null;
    
    // Create a specific agent instance for this model
    const agent = generateAgents().find(a => a.model === id) || generateAgents()[0];
    agent.model = id; // Force model match if mock gen didn't pick it
    agent.name = modelConfig.name.toUpperCase();
    agent.color = AGENT_COLORS[id];
    
    const snapshots = generatePortfolioHistory([agent], timeRange);
    const positions = generatePositions(agent.id);
    const decisions = generateDecisions(agent.id, 20); // More history
    const orders = generateOrders(agent.id);
    const trades = generateTrades(agent.id, 50); // More history

    return { agent, snapshots, positions, decisions, orders, trades };
  }, [id, modelConfig, timeRange]);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;
  if (!modelConfig || !data) return notFound();

  const chartSeries = [{
    name: data.agent.name,
    color: data.agent.color,
    data: getChartData(data.snapshots, data.agent.id)
  }];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <Link href="/models">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex flex-1 items-center justify-between">
          <div className="flex items-center gap-3">
             <div 
               className="flex h-10 w-10 items-center justify-center rounded-lg border bg-card"
               style={{ borderColor: AGENT_COLORS[id] }}
             >
                <Bot className="h-6 w-6" style={{ color: AGENT_COLORS[id] }} />
             </div>
             <div>
               <h2 className="text-xl font-bold tracking-tight">{modelConfig.name}</h2>
               <div className="flex items-center gap-2">
                 <Badge variant="secondary" className="text-xs font-normal">
                   {PROVIDER_NAMES[modelConfig.provider]}
                 </Badge>
                 <span className="text-xs text-muted-foreground">Automated Trader</span>
               </div>
             </div>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Share2 className="mr-2 h-4 w-4" />
              Share Stats
            </Button>
            <Button variant="outline" size="sm">
              <ExternalLink className="mr-2 h-4 w-4" />
              View Provider
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Performance Chart Section */}
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="mb-4 flex items-center justify-between">
             <h3 className="font-semibold">Performance History</h3>
             <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
          </div>
          <PerformanceChart series={chartSeries} height={350} />
        </div>

        {/* Detailed Stats */}
         <div className="h-[600px] lg:h-auto">
          <AgentDetails 
            agents={[data.agent]}
            positions={data.positions}
            decisions={data.decisions}
            orders={data.orders}
            trades={data.trades}
          />
        </div>
      </div>
    </div>
  );
}
