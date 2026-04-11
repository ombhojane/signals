import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:ring-[#a7cbeb]/30 focus-visible:ring-[3px] transition-colors overflow-hidden uppercase tracking-[0.08em]",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-[#a7cbeb]/15 text-[#a7cbeb]",
        secondary:
          "border-transparent bg-[#252626] text-[#acabaa]",
        destructive:
          "border-transparent bg-[#ee7d77]/15 text-[#ee7d77]",
        outline:
          "border-[rgba(72,72,72,0.3)] bg-transparent text-[#acabaa]",
        success:
          "border-transparent bg-[#a7cbeb]/10 text-[#a7cbeb]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
