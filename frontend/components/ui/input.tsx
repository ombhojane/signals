import * as React from "react"
import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-9 w-full min-w-0 rounded-full px-4 py-1.5 text-sm transition-all duration-200 outline-none",
        "bg-input text-foreground placeholder:text-muted-foreground",
        "border border-border",
        "focus:border-primary/30 focus:ring-[2px] focus:ring-primary/10",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        "file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
        "selection:bg-primary/20 selection:text-foreground",
        className
      )}
      {...props}
    />
  )
}

export { Input }
