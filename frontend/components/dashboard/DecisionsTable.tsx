import { AIDecision } from "@/lib/types";
import { formatCurrency, formatPercent, formatDate, formatTime } from "@/lib/utils";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export function DecisionsTable({ decisions }: { decisions: AIDecision[] }) {
  if (decisions.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
        No decisions recorded
      </div>
    );
  }

  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Operation</TableHead>
            <TableHead>Symbol</TableHead>
            <TableHead>Alloc Change</TableHead>
            <TableHead>Balance</TableHead>
            <TableHead>Executed</TableHead>
            <TableHead className="w-[40%]">Reasoning</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {decisions.map((decision) => (
            <TableRow key={decision.id} className="hover:bg-muted/5">
              <TableCell className="font-mono whitespace-nowrap tabular-nums text-muted-foreground text-xs">
                {formatDate(decision.timestamp)}
                <br />
                {formatTime(decision.timestamp)}
              </TableCell>
              <TableCell>
                <Badge 
                  variant="outline" 
                  className={
                    decision.operation === "BUY" ? "border-green-500/30 text-green-500 bg-green-500/10" :
                    decision.operation === "SELL" ? "border-red-500/30 text-red-500 bg-red-500/10" :
                    "border-zinc-500/30 text-zinc-500 bg-zinc-500/10"
                  }
                >
                  {decision.operation}
                </Badge>
              </TableCell>
              <TableCell className="font-bold">{decision.symbol || "-"}</TableCell>
              <TableCell className="font-mono tabular-nums">
                {decision.operation !== "HOLD" ? (
                  <div className="flex items-center gap-1 text-xs">
                    <span className="text-muted-foreground">{formatPercent(decision.prevPercent)}</span>
                    <span>→</span>
                    <span className="font-medium">{formatPercent(decision.targetPercent)}</span>
                  </div>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell className="font-mono tabular-nums">{formatCurrency(decision.balance)}</TableCell>
              <TableCell>
                <Badge variant={decision.executed ? "default" : "secondary"} className="text-[10px] h-5 px-1.5">
                  {decision.executed ? "Yes" : "No"}
                </Badge>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground italic">
                "{decision.reason}"
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
