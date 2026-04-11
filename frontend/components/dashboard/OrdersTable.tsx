import { Order } from "@/lib/types";
import { formatCurrency, formatDate, formatTime } from "@/lib/utils";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export function OrdersTable({ orders }: { orders: Order[] }) {
  if (orders.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
        No open orders
      </div>
    );
  }

  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Symbol</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Side</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Quantity</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.map((order) => (
            <TableRow key={order.id} className="hover:bg-muted/5">
              <TableCell className="font-mono whitespace-nowrap tabular-nums text-muted-foreground text-xs">
                 {formatDate(order.createdAt)}
                 <br />
                 {formatTime(order.createdAt)}
              </TableCell>
              <TableCell className="font-bold">{order.symbol}</TableCell>
              <TableCell className="text-xs">{order.type}</TableCell>
              <TableCell>
                <span className={order.side === "LONG" ? "text-green-500 font-medium" : "text-red-500 font-medium"}>
                  {order.side}
                </span>
              </TableCell>
              <TableCell className="font-mono tabular-nums">{formatCurrency(order.price)}</TableCell>
              <TableCell className="font-mono tabular-nums">{order.quantity}</TableCell>
              <TableCell>
                <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                  {order.status}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
