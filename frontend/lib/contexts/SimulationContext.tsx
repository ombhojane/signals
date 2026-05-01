import { createContext, useContext, ReactNode, useEffect, useState, useCallback } from "react";
import { SimulationState, TokenSnapshot, SimulationResult } from "@/lib/types/simulation";

interface SimulationPersistedState {
  state: SimulationState;
  liveSnapshot: TokenSnapshot | null;
  livePrice: number | null;
  initialChartData: Array<{ time: number; value: number }>;
  coinAddress: string;
  timestamp: number;
}

interface SimulationContextType {
  persistedState: SimulationPersistedState | null;
  saveState: (state: SimulationState, liveSnapshot: TokenSnapshot | null, livePrice: number | null, initialChartData: Array<{ time: number; value: number }>, coinAddress: string) => void;
  clearState: () => void;
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

const STORAGE_KEY = "simulationState";

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [persistedState, setPersistedState] = useState<SimulationPersistedState | null>(null);
  const [isClient, setIsClient] = useState(false);

  // Restore from localStorage on mount
  useEffect(() => {
    setIsClient(true);
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as SimulationPersistedState;
        setPersistedState(parsed);
      }
    } catch (err) {
      console.error("Failed to restore simulation state:", err);
    }
  }, []);

  const saveState = useCallback((
    state: SimulationState,
    liveSnapshot: TokenSnapshot | null,
    livePrice: number | null,
    initialChartData: Array<{ time: number; value: number }>,
    coinAddress: string
  ) => {
    try {
      const toSave: SimulationPersistedState = {
        state,
        liveSnapshot,
        livePrice,
        initialChartData,
        coinAddress,
        timestamp: Date.now(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
      setPersistedState(toSave);
    } catch (err) {
      console.error("Failed to save simulation state:", err);
    }
  }, []);

  const clearState = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
      setPersistedState(null);
    } catch (err) {
      console.error("Failed to clear simulation state:", err);
    }
  }, []);

  if (!isClient) return <>{children}</>;

  return (
    <SimulationContext.Provider value={{ persistedState, saveState, clearState }}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulationState() {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error("useSimulationState must be used within SimulationProvider");
  }
  return context;
}
