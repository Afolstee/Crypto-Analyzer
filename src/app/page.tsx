"use client"

import { useEffect, useState } from 'react';
import { useSSE } from '@/hooks/useSSE';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';  // Import from local alert component

interface CryptoPrice {
  id: string;
  symbol: string;
  current_price: number;
  price_change_percentage_24h: number;
  total_volume: number;
}

interface NewsItem {
  title: string;
  url: string;
  published_at: string;
  currencies: { code: string }[];
}

interface ChartData {
  name: string;
  price: number;
}

export default function Home() {
  const { data, isConnected, error } = useSSE();
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [chartData, setChartData] = useState<{ [key: string]: ChartData[] }>({});
  const [isLoading, setIsLoading] = useState(true);
  const [lastSuccessfulData, setLastSuccessfulData] = useState<{
    prices: CryptoPrice[];
    news: NewsItem[];
  } | null>(null);

  // Initial data fetch
  useEffect(() => {
    const initializeData = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('http://localhost:5000/crypto-data');
        if (!response.ok) {
          throw new Error('Failed to fetch initial data');
        }
        const initialData = await response.json();
        setPrices(initialData.prices);
        setNews(initialData.news);
        setLastSuccessfulData(initialData);
      } catch (error) {
        console.error('Initial data fetch error:', error);
        if (lastSuccessfulData) {
          setPrices(lastSuccessfulData.prices);
          setNews(lastSuccessfulData.news);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeData();
  }, []);

  // Update data when SSE sends new information
  useEffect(() => {
    if (data) {
      if (data.prices?.length > 0) {
        setPrices(data.prices);
        setLastSuccessfulData(prev => ({
          ...prev!,
          prices: data.prices
        }));
      }
      
      if (data.news?.length > 0) {
        setNews(data.news);
        setLastSuccessfulData(prev => ({
          ...prev!,
          news: data.news
        }));
      }
      
      setChartData(prevChartData => {
        const newChartData = { ...prevChartData };
        data.prices?.forEach((price: CryptoPrice) => {
          if (!newChartData[price.id]) {
            newChartData[price.id] = [];
          }
          newChartData[price.id] = [
            ...newChartData[price.id],
            {
              name: new Date().toLocaleTimeString(),
              price: price.current_price
            }
          ].slice(-30);
        });
        return newChartData;
      });
    }
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Crypto Analytics Dashboard</h1>
      
      {!isConnected && (
        <Alert 
          variant="destructive" 
          className="mb-4"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Connection lost. Displaying last available data. Attempting to reconnect...
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="prices" className="mb-6">
        <TabsList className="w-full border-b">
          <TabsTrigger value="prices" className="px-4 py-2">Prices</TabsTrigger>
          <TabsTrigger value="news" className="px-4 py-2">News</TabsTrigger>
        </TabsList>

        <TabsContent value="prices" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {prices.map(coin => (
              <Card key={coin.id} className="overflow-hidden shadow-lg">
                <CardHeader className="bg-gray-50">
                  <CardTitle className="capitalize">
                    {coin.id} ({coin.symbol.toUpperCase()})
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <div className="mb-4">
                    <p className="text-2xl font-bold">${coin.current_price.toLocaleString()}</p>
                    <p className={`text-sm ${coin.price_change_percentage_24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {coin.price_change_percentage_24h.toFixed(2)}% (24h)
                    </p>
                  </div>
                  {chartData[coin.id] && (
                    <div className="h-48">
                      <LineChart width={300} height={180} data={chartData[coin.id]}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={['auto', 'auto']} />
                        <Tooltip />
                        <Line 
                          type="monotone" 
                          dataKey="price" 
                          stroke="#8884d8" 
                          dot={false}
                          isAnimationActive={false}
                        />
                      </LineChart>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="news" className="mt-4">
          <div className="space-y-4">
            {news.map((item, index) => (
              <Card key={index} className="shadow-md hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <h3 className="font-bold mb-2 text-lg">
                    <a href={item.url} 
                       target="_blank" 
                       rel="noopener noreferrer" 
                       className="text-blue-600 hover:text-blue-800 hover:underline">
                      {item.title}
                    </a>
                  </h3>
                  <p className="text-sm text-gray-500 mb-3">
                    Published: {new Date(item.published_at).toLocaleString()}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {item.currencies.map(currency => (
                      <span key={currency.code} 
                            className="bg-gray-100 text-gray-800 rounded-full px-3 py-1 text-sm font-medium">
                        {currency.code}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}