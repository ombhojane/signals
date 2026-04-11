"use client";

import { Suspense, useState, useMemo, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  generateAgents,
  generatePortfolioHistory,
  generatePositions,
  generateDecisions,
  generateOrders,
  generateTrades,
  getChartData,
  calculateAgentStats,
} from "@/lib/mock-data";
import { TimeRange, Agent, Position, Trade, AIDecision, Order } from "@/lib/types";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { TimeRangeSelector } from "@/components/charts/TimeRangeSelector";
import { PositionsTable } from "@/components/dashboard/PositionsTable";
import { TradesTable } from "@/components/dashboard/TradesTable";
import { DecisionsTable } from "@/components/dashboard/DecisionsTable";
import { OrdersTable } from "@/components/dashboard/OrdersTable";
import { Card } from "@/components/ui/card";
import { formatCurrency, formatPercent, formatPnl } from "@/lib/utils";

// ── Portfolio Summary Cards ─────────────────────────────────────────────────
function PortfolioSummary({ agents }: { agents: Agent[] }) {
  const totalValue = agents.reduce((sum, a) => sum + a.accountValue, 0);
  const totalCash = agents.reduce((sum, a) => sum + a.availableCash, 0);
  const deployed = totalValue - totalCash;
  const avgPerformance = agents.length > 0
    ? (agents.reduce((sum, a) => sum + ((a.accountValue - 10000) / 10000), 0) / agents.length) * 100
    : 0;

  const stats = [
    {
      label: "Total Portfolio Value",
      value: formatCurrency(totalValue),
      change: "+12.4%",
      changeColor: "#a7cbeb",
      subtext: "All time",
    },
    {
      label: "Available Cash",
      value: formatCurrency(totalCash),
      change: `${((totalCash / totalValue) * 100).toFixed(1)}%`,
      changeColor: "#acabaa",
      subtext: "of portfolio",
    },
    {
      label: "Capital Deployed",
      value: formatCurrency(deployed),
      change: `${((deployed / totalValue) * 100).toFixed(1)}%`,
      changeColor: "#acabaa",
      subtext: "across positions",
    },
    {
      label: "Avg. Agent Performance",
      value: `${avgPerformance > 0 ? "+" : ""}${avgPerformance.toFixed(2)}%`,
      change: "+5.2%",
      changeColor: "#a7cbeb",
      subtext: "vs benchmark",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl p-6 transition-all duration-200 hover:scale-[1.02]"
          style={{ backgroundColor: "#131313" }}
        >
          <span
            className="text-[10px] uppercase tracking-widest font-medium"
            style={{ color: "#acabaa" }}
          >
            {stat.label}
          </span>
          <div className="mt-3 flex items-baseline gap-3">
            <span className="text-2xl font-semibold tracking-tight" style={{ color: "#e7e5e5" }}>
              {stat.value}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs font-medium" style={{ color: stat.changeColor }}>
              {stat.change}
            </span>
            <span className="text-[10px]" style={{ color: "#525252" }}>
              {stat.subtext}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Agent Allocation Chart ─────────────────────────────────────────────────
function AgentAllocation({ agents }: { agents: Agent[] }) {
  const totalValue = agents.reduce((sum, a) => sum + a.accountValue, 0);

  return (
    <div
      className="rounded-xl p-6 flex flex-col"
      style={{ backgroundColor: "#131313", minHeight: "320px" }}
    >
      <div className="flex items-center justify-between mb-6">
        <h3
          className="text-sm font-bold uppercase"
          style={{ letterSpacing: "0.2em", color: "#acabaa" }}
        >
          Capital Allocation
        </h3>
        <span className="material-symbols-outlined" style={{ color: "#a7cbeb", fontSize: "1.25rem" }}>
          pie_chart
        </span>
      </div>

      <div className="flex-1 flex flex-col gap-3">
        {agents.map((agent) => {
          const percentage = (agent.accountValue / totalValue) * 100;
          return (
            <div key={agent.id} className="flex items-center gap-4">
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: `${agent.color}20` }}>
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: agent.color }} />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium" style={{ color: "#e7e5e5" }}>
                    {agent.name}
                  </span>
                  <span className="text-sm font-mono" style={{ color: "#acabaa" }}>
                    {percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ backgroundColor: "#252626" }}>
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%`, backgroundColor: agent.color }}
                  />
                </div>
              </div>
              <span className="text-sm font-mono tabular-nums" style={{ color: "#e7e5e5", minWidth: "100px", textAlign: "right" }}>
                {formatCurrency(agent.accountValue)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Performance Metrics ────────────────────────────────────────────────────
function PerformanceMetrics({ trades }: { trades: Trade[] }) {
  const stats = useMemo(() => calculateAgentStats(trades), [trades]);
  const pnl = formatPnl(stats.netRealized);

  const metrics = [
    { label: "Total P&L", value: pnl.text, className: pnl.className },
    { label: "Win Rate", value: `${stats.holdTimes.long}%`, className: "text-[#a7cbeb]" },
    { label: "Avg Confidence", value: `${stats.averageConfidence.toFixed(1)}%`, className: "text-[#e7e5e5]" },
    { label: "Biggest Win", value: formatCurrency(stats.biggestWin), className: "text-[#a7cbeb]" },
    { label: "Biggest Loss", value: formatCurrency(stats.biggestLoss), className: "text-[#ee7d77]" },
    { label: "Total Fees", value: formatCurrency(stats.totalFees), className: "text-[#acabaa]" },
  ];

  return (
    <div
      className="rounded-xl p-6"
      style={{ backgroundColor: "#131313" }}
    >
      <div className="flex items-center justify-between mb-6">
        <h3
          className="text-sm font-bold uppercase"
          style={{ letterSpacing: "0.2em", color: "#acabaa" }}
        >
          Performance Metrics
        </h3>
        <span className="material-symbols-outlined" style={{ color: "#a7cbeb", fontSize: "1.25rem" }}>
          monitoring
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="p-4 rounded-lg" style={{ backgroundColor: "#191a1a" }}>
            <span className="text-[10px] uppercase tracking-widest" style={{ color: "#525252" }}>
              {metric.label}
            </span>
            <div className={`text-lg font-semibold mt-1 font-mono tabular-nums ${metric.className}`}>
              {metric.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Tab Navigation ─────────────────────────────────────────────────────────
type TabId = "positions" | "trades" | "orders" | "decisions";

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: "positions", label: "Positions", icon: "show_chart" },
  { id: "trades", label: "Trade History", icon: "history" },
  { id: "orders", label: "Open Orders", icon: "schedule" },
  { id: "decisions", label: "AI Decisions", icon: "psychology" },
];

function TabButton({
  id,
  label,
  icon,
  isActive,
  onClick,
}: {
  id: TabId;
  label: string;
  icon: string;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all duration-200 rounded-lg"
      style={{
        backgroundColor: isActive ? "#252626" : "transparent",
        color: isActive ? "#a7cbeb" : "#acabaa",
      }}
      onMouseEnter={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = "#1a1a1a";
      }}
      onMouseLeave={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = "transparent";
      }}
    >
      <span className="material-symbols-outlined" style={{ fontSize: "1.1rem" }}>
        {icon}
      </span>
      {label}
    </button>
  );
}

// ── Main Content ─────────────────────────────────────────────────────────────
function PortfolioContent() {
  const searchParams = useSearchParams();
  const timeRange = (searchParams.get("range") as TimeRange) || "5m";
  const [activeTab, setActiveTab] = useState<TabId>("positions");
  const [mounted, setMounted] = useState(false);

  const { agents, snapshots, positions, trades, orders, decisions } = useMemo(() => {
    const agents = generateAgents();
    const snapshots = generatePortfolioHistory(agents, timeRange);
    const allPositions = agents.flatMap((a) => generatePositions(a.id));
    const allTrades = agents.flatMap((a) => generateTrades(a.id, 15));
    const allOrders = agents.flatMap((a) => generateOrders(a.id));
    const allDecisions = agents.flatMap((a) => generateDecisions(a.id, 8));

    return {
      agents,
      snapshots,
      positions: allPositions,
      trades: allTrades,
      orders: allOrders,
      decisions: allDecisions,
    };
  }, [timeRange]);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const chartSeries = agents.map((agent) => ({
    name: agent.name,
    color: agent.color,
    data: getChartData(snapshots, agent.id),
  }));

  const renderTabContent = () => {
    switch (activeTab) {
      case "positions":
        return <PositionsTable positions={positions} />;
      case "trades":
        return <TradesTable trades={trades} />;
      case "orders":
        return <OrdersTable orders={orders} />;
      case "decisions":
        return <DecisionsTable decisions={decisions} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span
            className="text-xs uppercase font-medium"
            style={{ color: "#a7cbeb", letterSpacing: "0.3em" }}
          >
            Portfolio Overview
          </span>
          <h2 className="text-4xl font-bold tracking-tight mt-2" style={{ color: "#e7e5e5" }}>
            Your <span style={{ color: "#acabaa" }}>Positions</span>
          </h2>
        </div>
        <TimeRangeSelector value={timeRange} />
      </div>

      {/* Summary Cards */}
      <PortfolioSummary agents={agents} />

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Chart */}
        <div
          className="lg:col-span-2 rounded-xl p-6 flex flex-col"
          style={{ backgroundColor: "#191a1a", minHeight: "400px" }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3
              className="text-sm font-bold uppercase"
              style={{ letterSpacing: "0.2em", color: "#e7e5e5" }}
            >
              Performance History
            </h3>
            <span className="material-symbols-outlined" style={{ color: "#a7cbeb" }}>
              timeline
            </span>
          </div>
          <div className="flex-1 min-h-0">
            <PerformanceChart series={chartSeries} height={320} />
          </div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col gap-6">
          <AgentAllocation agents={agents} />
          <PerformanceMetrics trades={trades} />
        </div>
      </div>

      {/* Tabbed Content */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 p-1 rounded-xl" style={{ backgroundColor: "#131313" }}>
          {TABS.map((tab) => (
            <TabButton
              key={tab.id}
              {...tab}
              isActive={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
            />
          ))}
        </div>

        <div
          className="rounded-xl p-6"
          style={{ backgroundColor: "#131313", minHeight: "300px" }}
        >
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

// ── Loading State ───────────────────────────────────────────────────────────
function PortfolioSkeleton() {
  return (
    <div className="flex flex-col gap-8 animate-pulse">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 rounded" style={{ backgroundColor: "#252626" }} />
          <div className="h-10 w-64 rounded mt-2" style={{ backgroundColor: "#252626" }} />
        </div>
        <div className="h-8 w-32 rounded" style={{ backgroundColor: "#252626" }} />
      </div>

      {/* Stats Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 rounded-xl" style={{ backgroundColor: "#191a1a" }} />
        ))}
      </div>

      {/* Chart Skeleton */}
      <div className="h-96 rounded-xl" style={{ backgroundColor: "#191a1a" }} />
    </div>
  );
}

// ── Page Export ─────────────────────────────────────────────────────────────
export default function PortfolioPage() {
  return (
    <Suspense fallback={<PortfolioSkeleton />}>
      <PortfolioContent />
    </Suspense>
  );
}
