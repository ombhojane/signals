"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TIME_RANGES } from "@/lib/constants";
import { TimeRange } from "@/lib/types";

export function TimeRangeSelector({ 
  value = "5m", 
  onChange 
}: { 
  value?: TimeRange; 
  onChange?: (value: TimeRange) => void 
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const handleValueChange = (val: string) => {
    const newValue = val as TimeRange;
    if (onChange) {
      onChange(newValue);
    } else {
      // Default to URL state if no handler provided
      const params = new URLSearchParams(searchParams);
      params.set("range", newValue);
      router.replace(`${pathname}?${params.toString()}`);
    }
  };

  return (
    <Tabs value={value} onValueChange={handleValueChange} className="w-auto">
      <TabsList className="grid h-9 w-64 grid-cols-3 bg-muted/50 p-1">
        {(Object.keys(TIME_RANGES) as TimeRange[]).map((range) => (
          <TabsTrigger 
            key={range} 
            value={range}
            className="text-xs transition-all duration-150 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm data-[state=active]:border-l-2 data-[state=active]:border-primary"
          >
            {TIME_RANGES[range].label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
