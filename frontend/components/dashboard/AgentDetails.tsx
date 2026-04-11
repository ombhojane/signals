"use client";

import { useState } from "react";
import { Agent, Position, Trade, AIDecision, Order } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PositionsTable } from "./PositionsTable";
import { DecisionsTable } from "./DecisionsTable";
import { OrdersTable } from "./OrdersTable";
import { TradesTable } from "./TradesTable";
import { Card } from "@/components/ui/card";

interface AgentDetailsProps {
  agents: Agent[];
  positions: Position[];
  decisions: AIDecision[];
  orders: Order[];
  trades: Trade[];
}

const TABS = [
  { id: "positions", label: "Positions" },
  { id: "decisions", label: "AI Decisions" },
  { id: "orders", label: "Orders" },
  { id: "trades", label: "Trades" },
] as const;

export function AgentDetails({
  agents,
  positions,
  decisions,
  orders,
  trades,
}: AgentDetailsProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0]?.id || "");
  const [activeTab, setActiveTab] = useState<string>("positions");
  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  const agentPositions = positions.filter((p) => p.agentId === selectedAgentId);
  const agentDecisions = decisions.filter((d) => d.agentId === selectedAgentId);
  const agentOrders = orders.filter((o) => o.agentId === selectedAgentId);
  const agentTrades = trades.filter((t) => t.agentId === selectedAgentId);

  return (
    <Card variant="glass" className="h-full flex flex-col overflow-hidden p-0 gap-0">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border/20">
        <div className="flex items-center justify-between">
          <Select value={selectedAgentId} onValueChange={setSelectedAgentId}>
            <SelectTrigger className="w-[160px] h-8 text-sm border-border/30 bg-background/50">
              <SelectValue placeholder="Select Agent" />
            </SelectTrigger>
            <SelectContent>
              {agents.map((agent) => (
                <SelectItem key={agent.id} value={agent.id}>
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: agent.color }}
                    />
                    <span>{agent.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="font-mono text-sm font-medium tabular-nums text-muted-foreground">
            {selectedAgent ? formatCurrency(selectedAgent.accountValue) : "$0.00"}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-4 py-2 border-b border-border/20">
        <div className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150 ${
                activeTab === tab.id
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === "positions" && <PositionsTable positions={agentPositions} />}
        {activeTab === "decisions" && <DecisionsTable decisions={agentDecisions} />}
        {activeTab === "orders" && <OrdersTable orders={agentOrders} />}
        {activeTab === "trades" && <TradesTable trades={agentTrades} />}
      </div>
    </Card>
  );
}
