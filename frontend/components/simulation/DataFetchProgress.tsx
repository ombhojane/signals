"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

const SOURCES = [
  { name: "dex", label: "DexScreener + RugCheck" },
  { name: "gmgn", label: "Safety Analysis" },
  { name: "twitter", label: "Twitter API" },
];

interface DataFetchProgressProps {
  completedSources: string[];
}

export function DataFetchProgress({ completedSources }: DataFetchProgressProps) {
  const progress = (completedSources.length / SOURCES.length) * 100;
  const allCompleted = completedSources.length === SOURCES.length;

  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle>Fetching Market Data</CardTitle>
        <CardDescription>Collecting data from multiple sources...</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Progress bar */}
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Data sources */}
          <div className="space-y-3">
            {SOURCES.map((source, index) => {
              const completed = completedSources.includes(source.name);
              const loading = !completed && completedSources.length === index;
              return (
              <div
                key={source.name}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border transition-colors",
                  completed
                    ? "bg-green-500/10 border-green-500/20"
                    : loading
                    ? "bg-primary/10 border-primary/20"
                    : "bg-muted/50 border-border"
                )}
              >
                {completed ? (
                  <CheckCircle2 className="size-5 text-green-500" />
                ) : loading ? (
                  <Loader2 className="size-5 text-primary animate-spin" />
                ) : (
                  <Circle className="size-5 text-muted-foreground" />
                )}
                <div className="flex-1">
                  <p className="font-medium text-sm">{source.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {completed ? "Data fetched successfully" : loading ? "Fetching..." : "Waiting..."}
                  </p>
                </div>
              </div>
            );
            })}
          </div>

          {allCompleted && (
            <div className="pt-2 text-center">
              <p className="text-sm text-green-500 font-medium">
                All data sources fetched successfully!
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
