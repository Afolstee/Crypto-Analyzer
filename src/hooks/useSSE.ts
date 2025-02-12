import { useState, useEffect } from 'react';
import { API_CONFIG } from '@/config/api';

interface SSEData {
  prices: {
    id: string;
    symbol: string;
    current_price: number;
    price_change_percentage_24h: number;
    total_volume: number;
  }[];
  news: {
    title: string;
    url: string;
    published_at: string;
    currencies: { code: string }[];
  }[];
}

export function useSSE() {
  const [data, setData] = useState<SSEData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const eventSource = new EventSource(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stream}`
    );

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(parsedData);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to parse SSE data'));
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      setError(new Error('SSE connection failed'));
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, []);

  return { data, isConnected, error };
}