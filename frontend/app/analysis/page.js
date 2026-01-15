'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import StockChart from '../../components/StockChart';
import { fetchStockData } from '../../utils/api';
import { motion, AnimatePresence } from 'framer-motion';

export default function AnalysisPage() {
  const [ticker, setTicker] = useState('AAPL');
  const [tradeMode, setTradeMode] = useState('Intraday');
  const [chartData, setChartData] = useState({ labels: [], prices: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const router = useRouter();

  const handleSearch = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchStockData(ticker);
      if (data.labels.length > 0) {
        setChartData(data);
      } else {
        setError('Could not fetch data for this ticker. Please try another one.');
        setChartData({ labels: [], prices: [] }); // Clear chart on error
      }
    } catch (err) {
      setError('An error occurred while fetching data.');
      setChartData({ labels: [], prices: [] }); // Clear chart on error
    }
    setIsLoading(false);
  };

  useEffect(() => {
    handleSearch(); // Fetch initial data for AAPL
  }, []);

  return (
    <div className="min-h-screen container mx-auto p-4 sm:p-8 text-white">
        <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex justify-between items-center mb-12"
        >
            <h1 className="text-5xl font-bold text-white tracking-wider">AarnaAI</h1>
            <div className="flex gap-4">
                <motion.button 
                    onClick={() => router.push('/market-news')}
                    className="px-6 py-2 bg-transparent border border-primary text-white font-semibold rounded-lg hover:bg-primary/20 transition-all duration-300"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    Market News
                </motion.button>
                <motion.button 
                    onClick={() => router.push('/saved-reports')}
                    className="px-6 py-2 bg-transparent border border-primary text-white font-semibold rounded-lg hover:bg-primary/20 transition-all duration-300"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    Saved Reports
                </motion.button>
            </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Controls */}
            <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="lg:col-span-1 space-y-8"
            >
                <motion.div 
                    className="p-6 bg-card/50 backdrop-blur-sm rounded-xl shadow-lg border border-border"
                    whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
                >
                    <h2 className="text-3xl font-bold mb-6">Analysis</h2>
                    <div className="flex gap-4">
                        <input 
                            type="text" 
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            placeholder="Stock Ticker"
                            className="w-full p-3 bg-input/50 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all duration-300"
                        />
                        <motion.button 
                            onClick={handleSearch}
                            disabled={isLoading}
                            className="p-3 bg-primary/80 text-white font-bold rounded-lg hover:bg-primary transition-all duration-300 disabled:bg-muted"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                        >
                            {isLoading ? '...' : 'Go'}
                        </motion.button>
                    </div>
                </motion.div>

                <motion.div 
                    className="p-6 bg-card/50 backdrop-blur-sm rounded-xl shadow-lg border border-border"
                    whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
                >
                    <h3 className="text-2xl font-semibold mb-4">Trade Mode</h3>
                    <div className="grid grid-cols-2 gap-4">
                        {['Swing', 'Scalp', 'Intraday', 'Delivery'].map(mode => (
                            <motion.button 
                                key={mode}
                                onClick={() => setTradeMode(mode)}
                                className={`px-4 py-3 rounded-lg transition-all duration-300 font-semibold ${
                                    tradeMode === mode 
                                    ? 'bg-primary text-white shadow-lg' 
                                    : 'bg-muted/50 hover:bg-secondary/50'
                                }`}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                {mode}
                            </motion.button>
                        ))}
                    </div>
                </motion.div>
            </motion.div>

            {/* Right Column: Chart and Analysis */}
            <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="lg:col-span-2 p-6 bg-card/50 backdrop-blur-sm rounded-xl shadow-lg border border-border"
            >
                <h2 className="text-3xl font-bold mb-4 tracking-wider">{ticker} Price Chart</h2>
                <AnimatePresence>
                    {error && 
                        <motion.p 
                            className="text-red-400 text-center mb-4"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            {error}
                        </motion.p>
                    }
                </AnimatePresence>
                {isLoading ? (
                    <div className="flex justify-center items-center h-96">
                        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={ticker} // force re-render on ticker change
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                        >
                            <StockChart data={chartData} />
                        </motion.div>
                    </AnimatePresence>
                )}
            </motion.div>
        </div>
    </div>
  );
}
