import '../styles/globals.css';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Aarna AI Terminal',
  description: 'Advanced AI-powered stock prediction and analysis platform',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-background text-text-primary`}>
        {children}
      </body>
    </html>
  );
}
