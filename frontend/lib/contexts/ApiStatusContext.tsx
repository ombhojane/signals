"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { checkHealth } from "@/lib/api/client";

interface ApiStatusContextValue {
  isBackendOnline: boolean;
}

const ApiStatusContext = createContext<ApiStatusContextValue>({ isBackendOnline: false });

export function ApiStatusProvider({ children }: { children: ReactNode }) {
  const [isBackendOnline, setIsBackendOnline] = useState(false);

  const check = useCallback(async () => {
    const online = await checkHealth();
    setIsBackendOnline(online);
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, 30_000);
    return () => clearInterval(interval);
  }, [check]);

  return (
    <ApiStatusContext.Provider value={{ isBackendOnline }}>
      {children}
    </ApiStatusContext.Provider>
  );
}

export function useApiStatus() {
  return useContext(ApiStatusContext);
}
