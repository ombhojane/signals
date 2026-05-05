import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Format number as currency — auto-scales decimal places for crypto prices
export function formatCurrency(value: number): string {
  if (!value || isNaN(value)) return "$0.0000";
  const abs = Math.abs(value);
  let decimals: number;
  if (abs >= 1) decimals = 4;  // e.g. $1.2345
  else if (abs >= 0.01) decimals = 6;  // e.g. $0.001234
  else decimals = 8;  // e.g. $0.00001234

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

// Format number as percentage
export function formatPercent(value: number): string {
  return `${value >= 0 ? "" : ""}${value.toFixed(2)}%`;
}

// Format P&L with color class (Stitch design tokens: sapphire positive, muted-crimson negative)
export function formatPnl(value: number): { text: string; className: string } {
  const formatted = formatCurrency(Math.abs(value));
  if (value >= 0) {
    return { text: `+${formatted}`, className: "text-primary" };
  }
  return { text: `-${formatted}`, className: "text-[#ee7d77]" };
}

// Format relative time (e.g., "23H 32M")
export function formatHoldingTime(ms: number): string {
  const hours = Math.floor(ms / (1000 * 60 * 60));
  const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) {
    return `${hours}H ${minutes}M`;
  }
  return `${minutes}M`;
}

// Format date for display
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

// Format time only
export function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

// Generate a random ID
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}
