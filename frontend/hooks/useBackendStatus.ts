import { useState, useEffect } from 'react';

export type BackendStatus = 'online' | 'offline' | 'checking';

export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>('checking');

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const checkBackendStatus = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`, {
          method: 'GET',
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (isMounted) {
          setStatus(response.ok ? 'online' : 'offline');
        }
      } catch (error) {
        if (isMounted) {
          setStatus('offline');
        }
      }
    };

    // Check immediately
    checkBackendStatus();

    // Check every 30 seconds
    timeoutId = setInterval(checkBackendStatus, 30000);

    return () => {
      isMounted = false;
      clearInterval(timeoutId);
    };
  }, []);

  return status;
}
