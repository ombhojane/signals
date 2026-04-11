import { SimulationResult } from '../types/simulation';

/**
 * Format profit/loss percentage with color indication
 */
export function formatPnlPercent(pnl: number): { value: string; className: string } {
  const sign = pnl >= 0 ? '+' : '';
  const value = `${sign}${pnl.toFixed(2)}%`;
  
  if (Math.abs(pnl) < 0.5) {
    return { value, className: 'text-muted-foreground' };
  } else if (pnl > 0) {
    return { value, className: 'text-green-500' };
  } else {
    return { value, className: 'text-red-500' };
  }
}

/**
 * Format profit/loss amount
 */
export function formatPnl(pnl: number): { value: string; className: string } {
  const sign = pnl >= 0 ? '+' : '';
  const value = `$${sign}${Math.abs(pnl).toFixed(4)}`;
  
  if (Math.abs(pnl) < 0.0001) {
    return { value, className: 'text-muted-foreground' };
  } else if (pnl > 0) {
    return { value, className: 'text-green-500' };
  } else {
    return { value, className: 'text-red-500' };
  }
}

/**
 * Format countdown timer
 */
export function formatCountdown(remainingMs: number): string {
  const totalSeconds = Math.floor(remainingMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Format elapsed time
 */
export function formatElapsedTime(elapsedMs: number): string {
  const totalSeconds = Math.floor(elapsedMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds}s`;
}

/**
 * Get status badge variant
 */
export function getStatusVariant(status: SimulationResult['status']): 'default' | 'destructive' | 'secondary' {
  switch (status) {
    case 'profit':
      return 'default'; // Use default (primary) for profit
    case 'loss':
      return 'destructive';
    case 'equilized':
      return 'secondary';
  }
}

/**
 * Validate coin address format
 */
export function validateCoinAddress(address: string): { valid: boolean; error?: string } {
  if (!address || address.trim().length === 0) {
    return { valid: false, error: 'Coin address is required' };
  }
  
  const trimmed = address.trim();
  
  // Solana address (base58, 32-44 chars)
  if (trimmed.length >= 32 && trimmed.length <= 44 && /^[A-Za-z0-9]+$/.test(trimmed)) {
    return { valid: true };
  }
  
  // Ethereum address (0x + 40 hex chars)
  if (trimmed.startsWith('0x') && trimmed.length === 42 && /^0x[0-9a-fA-F]{40}$/.test(trimmed)) {
    return { valid: true };
  }
  
  return { valid: false, error: 'Invalid coin address format (expected Solana or Ethereum address)' };
}

/**
 * Compress chart data for storage (keep every Nth point)
 */
export function compressChartData(
  data: Array<{ time: number; value: number }>,
  keepEveryNth: number = 10
): Array<{ time: number; value: number }> {
  if (data.length <= 100) {
    return data; // Don't compress small datasets
  }
  
  const compressed: Array<{ time: number; value: number }> = [];
  
  // Always keep first and last points
  compressed.push(data[0]);
  
  for (let i = keepEveryNth; i < data.length - 1; i += keepEveryNth) {
    compressed.push(data[i]);
  }
  
  compressed.push(data[data.length - 1]);
  
  return compressed;
}
