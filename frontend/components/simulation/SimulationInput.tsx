"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { validateCoinAddress } from "@/lib/utils/simulation-helpers";
import { Search } from "lucide-react";
import { useApiStatus } from "@/lib/contexts/ApiStatusContext";

interface SimulationInputProps {
  onStart: (coinAddress: string) => void;
  disabled?: boolean;
  defaultAddress?: string;
}

export function SimulationInput({ onStart, disabled, defaultAddress }: SimulationInputProps) {
  const [address, setAddress] = useState(defaultAddress || "");
  const [error, setError] = useState<string | undefined>();
  const { isBackendOnline } = useApiStatus();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(undefined);

    const validation = validateCoinAddress(address);
    if (!validation.valid) {
      setError(validation.error);
      return;
    }

    onStart(address.trim());
  };

  return (
    <Card variant="glass">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>Scan Token</CardTitle>
          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
            isBackendOnline
              ? 'bg-green-500/10 text-green-500 border border-green-500/20'
              : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${isBackendOnline ? 'bg-green-500' : 'bg-yellow-500'}`} />
            {isBackendOnline ? 'Live' : 'Demo'}
          </span>
        </div>
        <CardDescription>
          {isBackendOnline
            ? 'Real-time analysis via DexScreener, RugCheck & AI'
            : 'Simulated data — start backend for live analysis'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Input
              type="text"
              placeholder="Enter coin address (Solana or Ethereum)"
              value={address}
              onChange={(e) => {
                setAddress(e.target.value);
                setError(undefined);
              }}
              disabled={disabled}
              aria-invalid={error ? "true" : "false"}
              className="font-mono text-sm"
            />
            {error && (
              <p className="text-sm text-red-500">{error}</p>
            )}
          </div>
          <Button
            type="submit"
            disabled={disabled || !address.trim()}
            className="w-full"
          >
            <Search className="size-4" />
            Scan Token
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
