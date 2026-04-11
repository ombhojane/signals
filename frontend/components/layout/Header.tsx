"use client";

import { useEffect, useState } from "react";
import { Bell, RefreshCw, Search, TrendingUp, TrendingDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useApiStatus } from "@/lib/contexts/ApiStatusContext";

interface TickerPrice {
  symbol: string;
  price: number;
  change: number;
}

const INITIAL_PRICES: TickerPrice[] = [
  { symbol: "BTC", price: 95234.58, change: 2.34 },
  { symbol: "ETH", price: 3524.19, change: -1.12 },
  { symbol: "SOL", price: 185.46, change: 5.67 },
  { symbol: "NVDA", price: 459.09, change: 1.23 },
  { symbol: "MSFT", price: 237.44, change: -0.45 },
  { symbol: "GOOGL", price: 327.82, change: 0.89 },
];

export function Header() {
  const [prices, setPrices] = useState<TickerPrice[]>(INITIAL_PRICES);
  const [mounted, setMounted] = useState(false);
  const { isBackendOnline } = useApiStatus();

  useEffect(() => {
    setMounted(true);
    
    // Simulate price updates every 3 seconds
    const interval = setInterval(() => {
      setPrices((prev) =>
        prev.map((p) => {
          const changeAmount = (Math.random() - 0.5) * p.price * 0.002;
          const newPrice = p.price + changeAmount;
          const newChange = p.change + (Math.random() - 0.5) * 0.5;
          return {
            ...p,
            price: Math.round(newPrice * 100) / 100,
            change: Math.round(newChange * 100) / 100,
          };
        })
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  if (!mounted) return null;

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-4">
      {/* Left: Title */}
      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-md border border-border/50 bg-muted/30 px-2.5 py-1 md:flex">
          <span className={`flex h-1.5 w-1.5 rounded-full ${isBackendOnline ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
          <span className="text-xs font-medium text-foreground">{isBackendOnline ? 'Live' : 'Demo'}</span>
        </div>
      </div>

      {/* Center: Price Ticker */}
      <div className="hidden lg:flex items-center gap-4 overflow-hidden mx-4">
        {prices.map((ticker) => (
          <div key={ticker.symbol} className="flex items-center gap-1.5 text-xs whitespace-nowrap">
            <span className="font-medium text-muted-foreground">{ticker.symbol}</span>
            <span className="font-mono font-bold tabular-nums">
              ${ticker.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className={`font-mono tabular-nums flex items-center gap-0.5 text-[10px] ${ticker.change >= 0 ? "text-green-500" : "text-red-500"}`}>
              {ticker.change >= 0 ? <TrendingUp className="h-2.5 w-2.5" /> : <TrendingDown className="h-2.5 w-2.5" />}
              {ticker.change >= 0 ? "+" : ""}{ticker.change.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>

      {/* Right: Controls */}
      <div className="flex items-center gap-2">
        <div className="relative hidden md:block">
          <Search className="absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search agents..."
            className="h-8 w-48 rounded-md border border-input bg-muted/50 pl-7 pr-3 text-xs outline-none focus:ring-1 focus:ring-ring"
          />
        </div>

        <Button variant="ghost" size="icon" className="h-8 w-8">
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>

        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Bell className="h-3.5 w-3.5" />
        </Button>

        <div className="flex items-center gap-2 border-l border-border pl-3 ml-1">
          <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-bold text-primary">
            OM
          </div>
        </div>
      </div>
    </header>
  );
}
