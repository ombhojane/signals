"use client";

import { useEffect, useState, useRef } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MODEL_CONFIGS, AGENT_COLORS, DECISION_REASONS } from "@/lib/constants";
import { Card } from "@/components/ui/card";

interface ChatMessage {
  id: string;
  model: string;
  modelName: string;
  color: string;
  timestamp: Date;
  message: string;
}

function generateRandomMessage(): ChatMessage {
  const model = MODEL_CONFIGS[Math.floor(Math.random() * MODEL_CONFIGS.length)];
  const operations = ["BUY", "SELL", "HOLD"] as const;
  const operation = operations[Math.floor(Math.random() * operations.length)];
  const reasons = DECISION_REASONS[operation];
  const reason = reasons[Math.floor(Math.random() * reasons.length)];

  return {
    id: Date.now().toString() + Math.random(),
    model: model.id,
    modelName: model.name,
    color: AGENT_COLORS[model.id] || "#888",
    timestamp: new Date(),
    message: reason,
  };
}

export function ModelChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [filter, setFilter] = useState<string>("ALL");
  const [mounted, setMounted] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    const initial: ChatMessage[] = [];
    for (let i = 0; i < 6; i++) {
      const msg = generateRandomMessage();
      msg.timestamp = new Date(Date.now() - (6 - i) * 60000);
      initial.push(msg);
    }
    setMessages(initial);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const interval = setInterval(() => {
      setMessages((prev) => {
        const newMsg = generateRandomMessage();
        return [...prev, newMsg].slice(-15);
      });
    }, 6000 + Math.random() * 4000);
    return () => clearInterval(interval);
  }, [mounted]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const filteredMessages =
    filter === "ALL" ? messages : messages.filter((m) => m.model === filter);

  const formatTime = (date: Date) =>
    date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });

  if (!mounted) return null;

  return (
    <Card variant="glass" className="h-full flex flex-col overflow-hidden p-0 gap-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/20">
        <div className="flex items-center gap-2">
          <span className="flex h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
          <svg
            className="h-4 w-4 text-muted-foreground"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span className="text-sm font-medium">Model Chat</span>
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-[130px] h-7 text-xs border-border/30 bg-background/50">
            <SelectValue placeholder="All Models" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Models</SelectItem>
            {MODEL_CONFIGS.slice(0, 5).map((model) => (
              <SelectItem key={model.id} value={model.id}>
                {model.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {filteredMessages.map((msg) => (
          <div key={msg.id} className="group">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium" style={{ color: msg.color }}>
                {msg.modelName}
              </span>
              <span className="font-mono text-[10px] text-muted-foreground/50 tabular-nums">
                {formatTime(msg.timestamp)}
              </span>
            </div>
            <p className="text-[11px] leading-relaxed text-muted-foreground/70">
              {msg.message}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}
