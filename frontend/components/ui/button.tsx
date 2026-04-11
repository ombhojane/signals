import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-semibold transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-[#a7cbeb]/30 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 aria-invalid:border-destructive tracking-wide",
  {
    variants: {
      variant: {
        default:
          "bg-[#a7cbeb] text-[#1e435e] hover:bg-[#b5d9f9] active:scale-95",
        destructive:
          "bg-destructive text-white hover:bg-destructive/90",
        outline:
          "border border-[rgba(72,72,72,0.3)] bg-transparent text-[#e7e5e5] hover:bg-[#191a1a] hover:border-[rgba(167,203,235,0.3)]",
        secondary:
          "bg-[#252626] text-[#acabaa] hover:bg-[#2b2c2c] hover:text-[#e7e5e5]",
        ghost:
          "bg-transparent text-[#acabaa] hover:bg-[#1f2020] hover:text-[#e7e5e5]",
        link:
          "text-[#a7cbeb] underline-offset-4 hover:underline bg-transparent",
      },
      size: {
        default: "h-10 px-6 py-2",
        sm: "h-8 px-4 text-xs",
        lg: "h-12 px-8 text-base",
        icon: "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
