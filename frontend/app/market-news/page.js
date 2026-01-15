'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

const MarketNewsPage = () => {
    const router = useRouter();

    const articles = [
        { title: 'Global Markets Surge as Economic Outlook Brightens', source: 'Financial Times', sentiment: 'Positive' },
        { title: 'Tech Sector Hits New Highs Amid Innovation Wave', source: 'The Verge', sentiment: 'Positive' },
        { title: 'Cryptocurrency Faces Regulatory Headwinds', source: 'CoinDesk', sentiment: 'Negative' },
        { title: 'Central Banks Signal Cautious Approach to Monetary Policy', source: 'Reuters', sentiment: 'Neutral' },
    ];

    const getSentimentColor = (sentiment) => {
        switch (sentiment) {
            case 'Positive': return 'text-green-300';
            case 'Negative': return 'text-red-300';
            default: return 'text-gray-300';
        }
    };

    return (
        <div className="min-h-screen container mx-auto p-8 text-white">
            <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="flex items-center mb-12"
            >
                 <motion.button 
                    onClick={() => router.back()} 
                    className="p-2 rounded-full hover:bg-white/10 transition-colors mr-6"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                </motion.button>
                <h1 className="text-5xl font-bold tracking-wider">Market News</h1>
            </motion.div>

            <motion.div 
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
            >
                {articles.map((article, index) => (
                    <motion.div 
                        key={index} 
                        className="bg-card/50 backdrop-blur-sm rounded-lg overflow-hidden shadow-lg border border-border transition-all duration-300 hover:shadow-primary/50 hover:-translate-y-1"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: index * 0.1 }}
                        whileHover={{ scale: 1.03, transition: { duration: 0.2 } }}
                    >
                        <div className="p-6">
                            <h2 className="text-xl font-bold mb-3">{article.title}</h2>
                            <p className="text-muted-foreground mb-4">{article.source}</p>
                            <p className={`font-semibold text-lg ${getSentimentColor(article.sentiment)}`}>
                                {article.sentiment} Sentiment
                            </p>
                        </div>
                    </motion.div>
                ))}
            </motion.div>
        </div>
    );
};

export default MarketNewsPage;
