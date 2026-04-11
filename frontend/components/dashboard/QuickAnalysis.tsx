"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, ArrowRight, Loader2, Shield, TrendingUp, TrendingDown } from "lucide-react";
import { fetchTokenAnalysis } from "@/lib/api/client";
import { useApiStatus } from "@/lib/contexts/ApiStatusContext";
import Link from "next/link";

interface AnalysisResult {
  price: number;
  volume24h: number;
  marketCap: number;
  liquidity: number;
  rugScore: number;
  symbol: string;
  name: string;
  priceChange24h: number;
}

export function QuickAnalysis() {
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { isBackendOnline } = useApiStatus();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim() || !isBackendOnline) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await fetchTokenAnalysis(address.trim());
      const priceHistory = data.dexData.priceHistory;
      const firstPrice = priceHistory[0]?.price || data.dexData.price;
      const priceChange24h = firstPrice > 0
        ? ((data.dexData.price - firstPrice) / firstPrice) * 100
        : 0;

      setResult({
        price: data.dexData.price,
        volume24h: data.dexData.volume24h,
        marketCap: data.dexData.marketCap,
        liquidity: data.dexData.liquidity,
        rugScore: data.gmgnData.rugScore,
        symbol: data.symbol,
        name: data.name,
        priceChange24h,
      });
    } catch {
      setError("Failed to fetch token data. Check the address and try again.");
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevel = (score: number) => {
    if (score <= 30) return { label: "Low Risk", color: "text-[#a7cbeb]" };
    if (score <= 60) return { label: "Medium Risk", color: "text-[#acabaa]" };
    return { label: "High Risk", color: "text-[#ee7d77]" };
  };

  const formatCompact = (n: number) => {
    if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
    if (n >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
    return `$${n.toFixed(2)}`;
  };

  return (
    <Card variant="glass">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Search className="size-4" />
          Quick Token Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex gap-2 mb-3">
          <Input
            type="text"
            placeholder={isBackendOnline ? "Token address..." : "Backend offline"}
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            disabled={!isBackendOnline || loading}
            className="font-mono text-xs"
          />
          <Button type="submit" size="sm" disabled={!address.trim() || loading || !isBackendOnline}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
          </Button>
        </form>

        {error && <p className="text-xs text-red-500 mb-2">{error}</p>}

        {result && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-semibold text-sm">{result.name || 'Unknown'}</span>
                {result.symbol && (
                  <Badge variant="outline" className="ml-2 text-[10px]">{result.symbol}</Badge>
                )}
              </div>
              <div className="flex items-center gap-1">
                <Shield className="size-3" />
                <span className={`text-xs font-medium ${getRiskLevel(result.rugScore).color}`}>
                  {getRiskLevel(result.rugScore).label}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-muted/50 rounded-md p-2">
                <div className="text-muted-foreground">Price</div>
                <div className="font-mono font-bold">${result.price < 0.01 ? result.price.toFixed(8) : result.price.toFixed(4)}</div>
                <div className={`font-mono text-[10px] flex items-center gap-0.5 ${result.priceChange24h >= 0 ? 'text-[#a7cbeb]' : 'text-[#ee7d77]'}`}>
                  {result.priceChange24h >= 0 ? <TrendingUp className="size-2.5" /> : <TrendingDown className="size-2.5" />}
                  {result.priceChange24h >= 0 ? '+' : ''}{result.priceChange24h.toFixed(2)}%
                </div>
              </div>
              <div className="bg-muted/50 rounded-md p-2">
                <div className="text-muted-foreground">Volume 24h</div>
                <div className="font-mono font-bold">{formatCompact(result.volume24h)}</div>
              </div>
              <div className="bg-muted/50 rounded-md p-2">
                <div className="text-muted-foreground">Market Cap</div>
                <div className="font-mono font-bold">{formatCompact(result.marketCap)}</div>
              </div>
              <div className="bg-muted/50 rounded-md p-2">
                <div className="text-muted-foreground">Liquidity</div>
                <div className="font-mono font-bold">{formatCompact(result.liquidity)}</div>
              </div>
            </div>

            <Link
              href={`/simulation?address=${encodeURIComponent(address.trim())}`}
              className="flex items-center justify-center gap-2 w-full text-xs font-medium text-primary hover:underline py-1.5"
            >
              Full Scan <ArrowRight className="size-3" />
            </Link>
          </div>
        )}

        {!result && !error && !loading && (
          <p className="text-xs text-muted-foreground text-center py-2">
            {isBackendOnline ? "Enter a token address for quick analysis" : "Connect backend for live analysis"}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
