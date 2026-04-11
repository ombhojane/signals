"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Play, Pause, Square } from "lucide-react";

interface SimulationControlsProps {
  duration: number;
  onDurationChange: (duration: number) => void;
  isRunning: boolean;
  isPaused: boolean;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  disabled?: boolean;
}

const DURATION_OPTIONS = [
  { value: 5, label: "5 minutes" },
  { value: 10, label: "10 minutes" },
  { value: 15, label: "15 minutes" },
  { value: 30, label: "30 minutes" },
  { value: 60, label: "1 hour" },
];

export function SimulationControls({
  duration,
  onDurationChange,
  isRunning,
  isPaused,
  onStart,
  onPause,
  onResume,
  onStop,
  disabled,
}: SimulationControlsProps) {
  return (
    <Card variant="glass">
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium mb-2 block">Time Horizon</label>
            <Select
              value={duration.toString()}
              onValueChange={(value) => onDurationChange(parseInt(value))}
              disabled={disabled || isRunning}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DURATION_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value.toString()}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            {!isRunning ? (
              <Button onClick={onStart} disabled={disabled} size="lg">
                <Play className="size-4" />
                Run Analysis
              </Button>
            ) : (
              <>
                {isPaused ? (
                  <Button onClick={onResume} variant="outline" size="lg">
                    <Play className="size-4" />
                    Resume
                  </Button>
                ) : (
                  <Button onClick={onPause} variant="outline" size="lg">
                    <Pause className="size-4" />
                    Pause
                  </Button>
                )}
                <Button onClick={onStop} variant="destructive" size="lg">
                  <Square className="size-4" />
                  Stop
                </Button>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
