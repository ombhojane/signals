"use client";

import { Agent } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
import { Card } from "@/components/ui/card";

interface AgentRankingsProps {
  agents: Agent[];
}

export function AgentRankings({ agents }: AgentRankingsProps) {
  const sortedAgents = [...agents].sort((a, b) => b.accountValue - a.accountValue);
  const topThree = sortedAgents.slice(0, 3);

  if (topThree.length < 3) return null;

  // Podium order: #2, #1, #3
  const podiumOrder = [topThree[1], topThree[0], topThree[2]];
  const positions = [2, 1, 3];
  const heights = [80, 112, 64];

  return (
    <Card variant="glass" className="p-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-8">
        <svg className="h-4 w-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
        </svg>
        <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
          Account Asset Ranking
        </span>
      </div>

      {/* Podium */}
      <div className="flex items-end justify-center gap-3">
        {podiumOrder.map((agent, index) => (
          <div key={agent.id} className="flex flex-col items-center group">
            {/* Avatar */}
            <div
              className="relative mb-3 flex h-12 w-12 items-center justify-center rounded-full transition-transform duration-200 group-hover:scale-105"
              style={{ backgroundColor: `${agent.color}15` }}
            >
              <span
                className="text-sm font-semibold"
                style={{ color: agent.color }}
              >
                {agent.name.substring(0, 2).toUpperCase()}
              </span>
              {positions[index] === 1 && (
                <div className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-amber-500/90 flex items-center justify-center">
                  <svg className="h-2.5 w-2.5 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5 16L3 5L8.5 10L12 4L15.5 10L21 5L19 16H5M19 19C19 19.6 18.6 20 18 20H6C5.4 20 5 19.6 5 19V18H19V19Z" />
                  </svg>
                </div>
              )}
            </div>

            {/* Name & Value */}
            <div className="text-center mb-2">
              <div className="text-xs font-medium text-foreground/90 truncate max-w-[80px]">
                {agent.name.split("-")[0]}
              </div>
              <div className="font-mono text-sm font-semibold tabular-nums text-foreground mt-0.5">
                {formatCurrency(agent.accountValue)}
              </div>
            </div>

            {/* Podium Bar */}
            <div
              className="w-20 rounded-t-md transition-all duration-300 flex items-start justify-center pt-3"
              style={{
                height: `${heights[index]}px`,
                background: `linear-gradient(180deg, ${agent.color}25 0%, ${agent.color}08 100%)`,
              }}
            >
              <span className="text-lg font-bold text-foreground/30">
                {positions[index]}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
