"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, X } from "lucide-react";

interface Account {
  id: string;
  name: string;
  model: string;
  baseUrl: string;
}

export function AddAgentModal() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [showAddForm, setShowAddForm] = useState(true);
  
  // Form state
  const [accountName, setAccountName] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");

  const handleAddAccount = () => {
    if (!accountName || !model) return;
    
    setLoading(true);
    setTimeout(() => {
      setAccounts([
        ...accounts,
        {
          id: Date.now().toString(),
          name: accountName,
          model,
          baseUrl: baseUrl || "https://api.openai.com/v1",
        },
      ]);
      // Reset form
      setAccountName("");
      setModel("");
      setBaseUrl("");
      setApiKey("");
      setShowAddForm(false);
      setLoading(false);
    }, 500);
  };

  const handleClose = () => {
    setOpen(false);
    setShowAddForm(true);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default" className="gap-2">
          <Plus className="h-4 w-4" />
          Create Agent
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px] bg-card border-border">
        <DialogHeader>
          <DialogTitle>AI Trader Accounts</DialogTitle>
          <DialogDescription>
            Manage your AI trader accounts. Each account has its own portfolio and AI model configuration.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Existing accounts list */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Accounts</span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowAddForm(true)}
              className="gap-1"
            >
              <Plus className="h-3 w-3" /> Add Account
            </Button>
          </div>
          
          {accounts.length === 0 && !showAddForm && (
            <div className="py-4 text-center text-sm text-muted-foreground">
              No accounts yet. Add your first AI trader.
            </div>
          )}
          
          {accounts.length > 0 && (
            <div className="space-y-2">
              {accounts.map((account) => (
                <div 
                  key={account.id}
                  className="flex items-center justify-between rounded-md border border-border bg-muted/30 px-3 py-2"
                >
                  <div>
                    <div className="font-medium">{account.name}</div>
                    <div className="text-xs text-muted-foreground">{account.model}</div>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-6 w-6"
                    onClick={() => setAccounts(accounts.filter(a => a.id !== account.id))}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* Add account form */}
          {showAddForm && (
            <div className="space-y-4 rounded-lg border border-border bg-muted/20 p-4">
              <div className="text-sm font-medium">Add New Account</div>
              
              <div className="grid gap-3">
                <div className="grid gap-1.5">
                  <Label htmlFor="name" className="text-xs text-muted-foreground">
                    Account Name (e.g., GPT, Claude)
                  </Label>
                  <Input 
                    id="name"
                    placeholder="GPT" 
                    value={accountName}
                    onChange={(e) => setAccountName(e.target.value)}
                    className="h-9 bg-background"
                  />
                </div>
                
                <div className="grid gap-1.5">
                  <Label htmlFor="model" className="text-xs text-muted-foreground">
                    Model (e.g., gpt-4, claude-3)
                  </Label>
                  <Input 
                    id="model"
                    placeholder="gpt-4" 
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="h-9 bg-background"
                  />
                </div>
                
                <div className="grid gap-1.5">
                  <Label htmlFor="baseUrl" className="text-xs text-muted-foreground">
                    Base URL (e.g., https://api.openai.com/v1)
                  </Label>
                  <Input 
                    id="baseUrl"
                    placeholder="https://api.openai.com/v1" 
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    className="h-9 bg-background"
                  />
                </div>
                
                <div className="grid gap-1.5">
                  <Label htmlFor="apiKey" className="text-xs text-muted-foreground">
                    API Key
                  </Label>
                  <Input 
                    id="apiKey"
                    type="password"
                    placeholder="sk-..." 
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="h-9 bg-background"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          {showAddForm && (
            <Button 
              variant="default"
              onClick={handleAddAccount} 
              disabled={loading || !accountName || !model}
            >
              {loading ? "Adding..." : "Add Account"}
            </Button>
          )}
          <Button variant="outline" onClick={handleClose}>
            {showAddForm ? "Cancel" : "Close"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
