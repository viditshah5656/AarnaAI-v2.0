'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { TypeAnimation } from 'react-type-animation';

const LandingPage = () => {
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col justify-center items-center text-center text-white p-4">
        <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-4xl"
        >
            <h1 className="text-6xl md:text-8xl font-bold mb-4 tracking-wider">
              Aarna <span className="text-primary">AI</span>
            </h1>
            <TypeAnimation
              sequence={[
                'Analyze stocks with the power of AI.',
                2000,
                'Get real-time market insights.',
                2000,
                'Make data-driven investment decisions.',
                2000,
              ]}
              wrapper="h2"
              speed={50}
              className="text-2xl md:text-3xl text-muted-foreground mb-12"
              repeat={Infinity}
            />

            <motion.div 
                className="p-8 bg-card/50 backdrop-blur-sm rounded-xl shadow-lg border border-border mb-12"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.5 }}
            >
                <h3 className="text-3xl font-bold mb-4">About Aarna AI</h3>
                <p className="text-lg text-muted-foreground">
                    Aarna AI is a futuristic stock analysis tool that leverages artificial intelligence to provide you with a competitive edge in the market. Our platform offers real-time data, advanced charting, and AI-powered insights to help you navigate the complexities of stock trading. Whether you're an experienced investor or just starting, Aarna AI is your partner in making smarter, more informed decisions.
                </p>
            </motion.div>

            <motion.button
              onClick={() => router.push('/analysis')}
              className="px-10 py-4 bg-primary text-white font-bold text-xl rounded-lg hover:bg-primary/80 transition-all duration-300 shadow-lg shadow-primary/30"
              whileHover={{ scale: 1.05, boxShadow: "0px 0px 30px rgba(217, 91, 59, 0.5)" }}
              whileTap={{ scale: 0.95 }}
            >
              Get Started
            </motion.button>
        </motion.div>
    </div>
  );
};

export default LandingPage;
