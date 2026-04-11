"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Flame, ExternalLink, Loader2 } from "lucide-react";
import { fetchTrendingTokens } from "@/lib/api/client";
import { useApiStatus } from "@/lib/contexts/ApiStatusContext";
import Link from "next/link";

interface TrendingToken {
  tokenAddress: string;
  name: string;
  symbol: string;
  url?: string;
  icon?: string;
}

export function TrendingTokens() {
  const [tokens, setTokens] = useState<TrendingToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const { isBackendOnline } = useApiStatus();

  const fetchData = useCallback(async () => {
    if (!isBackendOnline) {
      setLoading(false);
      setError(false);
      setTokens([]);
      return;
    }

    try {
      setLoading(true);
      const data = await fetchTrendingTokens('sol', 10);
      setTokens(data.trending_tokens || []);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [isBackendOnline]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 120_000); // 2 minutes
    return () => clearInterval(interval);
  }, [fetchData]);

  const truncateAddress = (addr: string) =>
    addr ? `${addr.slice(0, 6)}...${addr.slice(-4)}` : '';

  return (
    <Card variant="glass">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Flame className="size-4 text-orange-500" />
          Trending Tokens
          <Badge variant="outline" className="text-[10px] ml-auto">SOL</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {!loading && !isBackendOnline && (
          <p className="text-xs text-muted-foreground text-center py-4">
            Connect backend for trending tokens
          </p>
        )}

        {!loading && isBackendOnline && error && (
          <p className="text-xs text-red-500 text-center py-4">
            Failed to load trending tokens
          </p>
        )}

        {!loading && tokens.length > 0 && (
          <div className="space-y-1.5">
            {tokens.map((token, i) => (
              <div
                key={token.tokenAddress || i}
                className="flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-muted/50 transition-colors group"
              >
                <span className="text-[10px] text-muted-foreground font-mono w-4">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium truncate">
                    {token.name || 'Unknown'}
                  </div>
                  <code className="text-[10px] text-muted-foreground font-mono">
                    {truncateAddress(token.tokenAddress)}
                  </code>
                </div>
                <Link
                  href={`/simulation?address=${encodeURIComponent(token.tokenAddress)}`}
                  className="text-[10px] font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5"
                >
                  Scan <ExternalLink className="size-2.5" />
                </Link>
              </div>
            ))}
          </div>
        )}

        {!loading && isBackendOnline && !error && tokens.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-4">
            No trending tokens found
          </p>
        )}
      </CardContent>
    </Card>
  );
}
