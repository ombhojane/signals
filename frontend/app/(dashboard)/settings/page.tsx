"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useSettings } from "@/lib/settings-context";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Moon,
  Sun,
  Monitor,
  AlertTriangle,
  Shield,
  Wallet,
  Bell,
  Activity,
  Check,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface APIKeyState {
  key: string;
  connected: boolean;
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { settings, updateSetting } = useSettings();
  const [mounted, setMounted] = useState(false);
  const [apiKeys, setApiKeys] = useState<Record<string, APIKeyState>>({
    OpenAI: { key: "", connected: false },
    Anthropic: { key: "", connected: false },
    "Google Vertex": { key: "", connected: false },
    DeepSeek: { key: "", connected: false },
  });
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [tempKey, setTempKey] = useState("");

  useEffect(() => {
    setMounted(true);
    // Load API keys from localStorage
    const storedKeys = localStorage.getItem("HypeScan-api-keys");
    if (storedKeys) {
      try {
        setApiKeys(JSON.parse(storedKeys));
      } catch (e) {
        console.error("Failed to parse API keys:", e);
      }
    }
  }, []);

  const handleSaveApiKey = (provider: string) => {
    const newKeys = {
      ...apiKeys,
      [provider]: { key: tempKey, connected: tempKey.length > 10 },
    };
    setApiKeys(newKeys);
    localStorage.setItem("HypeScan-api-keys", JSON.stringify(newKeys));
    setEditingProvider(null);
    setTempKey("");
  };

  const handleDisconnect = (provider: string) => {
    const newKeys = {
      ...apiKeys,
      [provider]: { key: "", connected: false },
    };
    setApiKeys(newKeys);
    localStorage.setItem("HypeScan-api-keys", JSON.stringify(newKeys));
  };

  if (!mounted) return null;

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
          <p className="text-muted-foreground">
            Manage appearance, simulation parameters, and API keys
          </p>
        </div>
      </div>

      {/* Appearance */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Appearance
          </CardTitle>
          <CardDescription>
            Customize the look and feel of the dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div className="space-y-0.5">
              <div className="font-medium">Theme Preference</div>
              <div className="text-sm text-muted-foreground">
                Select your preferred interface theme
              </div>
            </div>
            <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-md">
              <Button
                variant={theme === "light" ? "default" : "ghost"}
                size="sm"
                className="h-8 w-8 px-0"
                onClick={() => setTheme("light")}
              >
                <Sun className="h-4 w-4" />
              </Button>
              <Button
                variant={theme === "system" ? "default" : "ghost"}
                size="sm"
                className="h-8 w-8 px-0"
                onClick={() => setTheme("system")}
              >
                <Monitor className="h-4 w-4" />
              </Button>
              <Button
                variant={theme === "dark" ? "default" : "ghost"}
                size="sm"
                className="h-8 w-8 px-0"
                onClick={() => setTheme("dark")}
              >
                <Moon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Simulation */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Simulation Control
          </CardTitle>
          <CardDescription>
            Configure the parameters for the AI trading simulation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div className="space-y-0.5">
              <div className="font-medium">Global Auto-Trading</div>
              <div className="text-sm text-muted-foreground">
                Enable or disable trading for all active agents
              </div>
            </div>
            <Switch
              checked={settings.autoTrading}
              onCheckedChange={(v) => updateSetting("autoTrading", v)}
            />
          </div>

          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div className="space-y-0.5">
              <div className="font-medium">Simulation Speed</div>
              <div className="text-sm text-muted-foreground">
                Accelerate time for backtesting visualization
              </div>
            </div>
            <div className="flex items-center gap-2">
              {[0.5, 1, 2, 5].map((speed) => (
                <Button
                  key={speed}
                  variant={settings.simulationSpeed === speed ? "default" : "outline"}
                  size="sm"
                  onClick={() => updateSetting("simulationSpeed", speed)}
                  className="w-12"
                >
                  {speed}x
                </Button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div className="space-y-0.5">
              <div className="font-medium">Price Alerts</div>
              <div className="text-sm text-muted-foreground">
                Receive notifications for significant price movements
              </div>
            </div>
            <Switch
              checked={settings.notifications}
              onCheckedChange={(v) => updateSetting("notifications", v)}
            />
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            API Configuration
          </CardTitle>
          <CardDescription>
            Connect your own LLM providers for real inference
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg bg-yellow-500/10 border border-yellow-500/20 p-4">
            <div className="flex items-center gap-2 text-yellow-500 font-medium mb-1">
              <AlertTriangle className="h-4 w-4" />
              Demo Mode Active
            </div>
            <p className="text-sm text-yellow-500/80">
              API keys are stored locally. For production, use server-side key management.
            </p>
          </div>

          {Object.entries(apiKeys).map(([provider, state]) => (
            <div
              key={provider}
              className="flex items-center justify-between rounded-lg border border-border p-4"
            >
              <div className="flex items-center gap-3">
                <div className="font-medium">{provider}</div>
                {state.connected && (
                  <Badge variant="outline" className="text-green-500 border-green-500/50">
                    <Check className="h-3 w-3 mr-1" />
                    Connected
                  </Badge>
                )}
              </div>

              {editingProvider === provider ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="password"
                    placeholder="sk-..."
                    value={tempKey}
                    onChange={(e) => setTempKey(e.target.value)}
                    className="h-8 w-48 text-xs"
                  />
                  <Button size="sm" onClick={() => handleSaveApiKey(provider)}>
                    Save
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setEditingProvider(null);
                      setTempKey("");
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : state.connected ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleDisconnect(provider)}
                >
                  Disconnect
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditingProvider(provider)}
                >
                  Connect
                </Button>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Wallet */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            Connected Wallet
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" className="w-full">
            Connect Solana Wallet
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
