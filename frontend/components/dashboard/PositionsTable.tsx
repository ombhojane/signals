import { Position } from "@/lib/types";
import { formatCurrency, formatPercent, formatPnl, formatHoldingTime } from "@/lib/utils";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export function PositionsTable({ positions }: { positions: Position[] }) {
  if (positions.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
        No active positions
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
            <TableHead>Size</TableHead>
            <TableHead>Entry Price</TableHead>
            <TableHead>Mark Price</TableHead>
            <TableHead>Liq. Price</TableHead>
            <TableHead>Unrealized P&L</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {positions.map((position) => {
            const pnl = formatPnl(position.unrealizedPnl);
            const pnlPercent = (position.unrealizedPnl / position.margin) * 100;
            
            return (
              <TableRow key={position.id} className="hover:bg-muted/5">
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    <span className="font-bold">{position.symbol}</span>
                    <Badge variant="outline" className="font-mono tabular-nums h-5 px-1 py-0 text-[10px] text-muted-foreground">
                      {position.leverage}x
                    </Badge>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge 
                    variant={position.side === "LONG" ? "default" : "destructive"}
                    className={position.side === "LONG" ? "border-[rgba(167,203,235,0.3)] text-[#a7cbeb] bg-[rgba(167,203,235,0.1)] hover:bg-[rgba(167,203,235,0.15)]" : "border-[rgba(238,125,119,0.3)] text-[#ee7d77] bg-[rgba(238,125,119,0.1)] hover:bg-[rgba(238,125,119,0.15)]"}
                  >
                    {position.side}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono tabular-nums">{position.quantity}</TableCell>
                <TableCell className="font-mono tabular-nums">{formatCurrency(position.entryPrice)}</TableCell>
                <TableCell className="font-mono tabular-nums">{formatCurrency(position.currentPrice)}</TableCell>
                <TableCell className="font-mono tabular-nums text-orange-500">{formatCurrency(position.liquidationPrice)}</TableCell>
                <TableCell>
                  <div className={`font-mono tabular-nums ${pnl.className}`}>{pnl.text}</div>
                  <div className={`font-mono tabular-nums text-xs ${pnl.className}`}>
                    ({formatPercent(pnlPercent)})
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
