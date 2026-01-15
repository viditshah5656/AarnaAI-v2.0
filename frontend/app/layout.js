import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "../components/ThemeProvider";
import ParticleBackground from "../components/ParticleBackground";
import ThemeSwitcher from "../components/ThemeSwitcher";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Aarna AI",
  description: "A stock analysis tool from the future.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
            <ParticleBackground />
            {children}
            <ThemeSwitcher />
        </ThemeProvider>
      </body>
    </html>
  );
}
