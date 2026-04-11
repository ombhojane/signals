"use client";

import { MODEL_CONFIGS, AGENT_COLORS, PROVIDER_NAMES } from "@/lib/constants";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bot, Zap, Brain, Activity, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function ModelsPage() {
  return (
    <div className="flex flex-col gap-6">
       <div className="flex items-center justify-between">
        <div>
           <h2 className="text-2xl font-bold tracking-tight">AI Models</h2>
           <p className="text-muted-foreground">Explore the LLMs powering our autonomous traders</p>
        </div>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {MODEL_CONFIGS.map((model) => (
          <Card key={model.id} className="group overflow-hidden border-border bg-card transition-all hover:border-primary/50 hover:shadow-lg">
            <div 
              className="h-2 w-full" 
              style={{ backgroundColor: AGENT_COLORS[model.id] || "#888" }} 
            />
            <CardHeader>
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="mb-2 w-fit">
                  {PROVIDER_NAMES[model.provider]}
                </Badge>
                <Bot className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              <CardTitle className="text-xl">{model.name}</CardTitle>
              <CardDescription>
                High-performance foundational model optimized for market analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1 rounded-lg bg-muted/50 p-3">
                   <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Zap className="h-3 w-3" /> Speed
                   </div>
                   <div className="font-bold">~45 t/s</div>
                </div>
                <div className="flex flex-col gap-1 rounded-lg bg-muted/50 p-3">
                   <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Brain className="h-3 w-3" /> Context
                   </div>
                   <div className="font-bold">128k</div>
                </div>
                <div className="flex flex-col gap-1 rounded-lg bg-muted/50 p-3">
                   <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Activity className="h-3 w-3" /> Active Agents
                   </div>
                   <div className="font-bold">{Math.floor(Math.random() * 20) + 5}</div>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Link href={`/models/${model.id}`} className="w-full">
                <Button variant="outline" className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                  View Performance
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}
