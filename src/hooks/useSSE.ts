import { useEffect, useState } from 'react';

interface UseSSEReturn {
  data: any;
  isConnected: boolean;
  error: string | null;
}

export const useSSE = (): UseSSEReturn => {
  const [data, setData] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const eventSource = new EventSource('http://localhost:5000/crypto-stream');

    eventSource.onopen = () => {
      console.log('SSE connection opened');
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        if (parsedData.error) {
          setError(parsedData.error);
        } else {
          setData(parsedData);
          setError(null);
        }
      } catch (e) {
        setError('Failed to parse data');
      }
    };

    eventSource.onerror = (event) => {
      console.error('SSE connection error:', event);
      setIsConnected(false);
      setError('Connection error. Attempting to reconnect...');
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, []);

  return { data, isConnected, error };
};