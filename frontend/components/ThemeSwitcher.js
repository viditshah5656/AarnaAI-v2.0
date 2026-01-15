'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { motion, AnimatePresence } from 'framer-motion';

const ThemeSwitcher = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50">
        <div className="flex flex-col gap-2">
            <motion.button
                onClick={() => setTheme('dark')}
                className={`w-12 h-12 rounded-full flex items-center justify-center ${theme === 'dark' ? 'bg-primary' : 'bg-card/50 backdrop-blur-sm'}`}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
            >
               <p className="text-white font-bold">Dark</p>
            </motion.button>
            <motion.button
                onClick={() => setTheme('light')}
                className={`w-12 h-12 rounded-full flex items-center justify-center ${theme === 'light' ? 'bg-primary' : 'bg-card/50 backdrop-blur-sm'}`}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
            >
                <p className="text-white font-bold">Light</p>
            </motion.button>
            <motion.button
                onClick={() => setTheme('synthwave')}
                className={`w-12 h-12 rounded-full flex items-center justify-center ${theme === 'synthwave' ? 'bg-primary' : 'bg-card/50 backdrop-blur-sm'}`}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
            >
                 <p className="text-white font-bold">Synth</p>
            </motion.button>
        </div>
    </div>
  );
};

export default ThemeSwitcher;
