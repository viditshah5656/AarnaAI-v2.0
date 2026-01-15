'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

const SavedReportsPage = () => {
    const router = useRouter();

    const reports = [
        { id: 1, name: 'AAPL - Intraday Analysis', date: '2024-07-29' },
        { id: 2, name: 'GOOGL - Swing Trade Report', date: '2024-07-28' },
        { id: 3, name: 'TSLA - Scalp Opportunity', date: '2024-07-27' },
    ];

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
                <h1 className="text-5xl font-bold tracking-wider">Saved Reports</h1>
            </motion.div>

            <motion.div 
                className="space-y-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
            >
                {reports.map((report, index) => (
                    <motion.div 
                        key={report.id} 
                        className="flex justify-between items-center p-6 bg-card/50 backdrop-blur-sm rounded-lg shadow-lg border border-border transition-all duration-300 hover:shadow-primary/50"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: index * 0.1 }}
                        whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
                    >
                        <div>
                            <p className="text-xl font-semibold">{report.name}</p>
                            <p className="text-muted-foreground text-md">{report.date}</p>
                        </div>
                        <div className="flex gap-4">
                            <motion.button 
                                className="px-6 py-2 bg-primary/80 text-white font-semibold rounded-lg hover:bg-primary transition-all duration-300"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                View
                            </motion.button>
                            <motion.button 
                                className="px-6 py-2 bg-destructive/80 text-white font-semibold rounded-lg hover:bg-destructive transition-all duration-300"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                Delete
                            </motion.button>
                        </div>
                    </motion.div>
                ))}
            </motion.div>
        </div>
    );
};

export default SavedReportsPage;
