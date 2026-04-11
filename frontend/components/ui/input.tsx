import * as React from "react"
import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-9 w-full min-w-0 rounded-full px-4 py-1.5 text-sm transition-all duration-200 outline-none",
        "bg-[#252626] text-[#e7e5e5] placeholder:text-[#525252]",
        "border border-[rgba(72,72,72,0.2)]",
        "focus:border-[rgba(167,203,235,0.35)] focus:ring-[2px] focus:ring-[rgba(167,203,235,0.12)]",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        "file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[#e7e5e5]",
        "selection:bg-[#a7cbeb]/20 selection:text-[#e7e5e5]",
        className
      )}
      {...props}
    />
  )
}

export { Input }
