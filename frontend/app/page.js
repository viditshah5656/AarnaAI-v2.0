'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import KPI from '../components/KPI';
import AIAnalysis from '../components/AIAnalysis';
import MarketNews from '../components/MarketNews';
import TopMovers from '../components/TopMovers';

const DynamicMainChart = dynamic(() => import('../components/MainChart'), { ssr: false });

export default function Home() {
  const [stockData, setStockData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [news, setNews] = useState([]);
  const [topMovers, setTopMovers] = useState([]);
  const [kpiData, setKpiData] = useState({
    predictionAccuracy: '--',
    modelConfidence: '--',
    marketBias: '--',
    volatility: '--',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (ticker) => {
    setLoading(true);
    setError(null);
    setStockData(null);
    setAnalysis(null);
    setNews([]);

    try {
      const res = await fetch(`/api/stock/${ticker}`);
      if (!res.ok) {
        throw new Error('Failed to fetch stock data');
      }
      const data = await res.json();
      
      setStockData(data.chart_data);
      setAnalysis(data.ai_analysis);
      setNews(data.market_news);
      setTopMovers(data.top_movers);
      setKpiData({
        predictionAccuracy: data.kpi_data.prediction_accuracy,
        modelConfidence: data.kpi_data.model_confidence,
        marketBias: data.kpi_data.market_bias,
        volatility: data.kpi_data.volatility,
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onSearch={handleSearch} />
        <main className="flex-1 overflow-y-auto p-8">
          {loading && <p className="text-center">Loading data...</p>}
          {error && <p className="text-center text-red-500">{error}</p>}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <KPI title="Prediction Accuracy" value={kpiData.predictionAccuracy} />
            <KPI title="Model Confidence" value={kpiData.modelConfidence} />
            <KPI title="Market Bias" value={kpiData.marketBias} />
            <KPI title="Volatility" value={kpiData.volatility} />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <DynamicMainChart data={stockData} />
            </div>
            <div>
              <AIAnalysis content={analysis} />
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
            <MarketNews articles={news} />
            <TopMovers movers={topMovers} />
          </div>
        </main>
      </div>
    </div>
  );
}
