import { Trade } from "@/lib/types";
import { formatCurrency, formatPnl } from "@/lib/utils";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export function TradesTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
        No trade history
      </div>
    );
  }

  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead>Symbol</TableHead>
            <TableHead>Side</TableHead>
            <TableHead>Entry Price</TableHead>
            <TableHead>Exit Price</TableHead>
            <TableHead>Quantity</TableHead>
            <TableHead>Holding Time</TableHead>
            <TableHead>Fees</TableHead>
            <TableHead>Net P&L</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {trades.map((trade) => {
            const pnl = formatPnl(trade.netPnl);
            
            return (
              <TableRow key={trade.id} className="hover:bg-muted/5">
                <TableCell className="font-bold">{trade.symbol}</TableCell>
                <TableCell>
                  <span className={trade.side === "LONG" ? "text-green-500 font-medium" : "text-red-500 font-medium"}>
                    {trade.side}
                  </span>
                </TableCell>
                <TableCell className="font-mono tabular-nums">{formatCurrency(trade.entryPrice)}</TableCell>
                <TableCell className="font-mono tabular-nums">{formatCurrency(trade.exitPrice)}</TableCell>
                <TableCell className="font-mono tabular-nums">{trade.quantity}</TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">{trade.holdingTime}</TableCell>
                <TableCell className="font-mono tabular-nums text-muted-foreground text-xs">{formatCurrency(trade.totalFees)}</TableCell>
                <TableCell className={`font-mono tabular-nums font-medium ${pnl.className}`}>
                  {pnl.text}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
