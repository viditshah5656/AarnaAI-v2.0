/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#000000',
        foreground: '#e0e0e0',
        card: 'rgba(10, 10, 10, 0.5)',
        'card-foreground': '#e0e0e0',
        popover: '#0a0a0a',
        'popover-foreground': '#e0e0e0',
        primary: '#007BFF',
        'primary-foreground': '#ffffff',
        secondary: '#6C757D',
        'secondary-foreground': '#ffffff',
        muted: '#1a1a1a',
        'muted-foreground': '#a0a0a0',
        accent: '#007BFF',
        'accent-foreground': '#ffffff',
        destructive: '#dc3545',
        'destructive-foreground': '#ffffff',
        border: 'rgba(255, 255, 255, 0.1)',
        input: 'rgba(255, 255, 255, 0.05)',
        ring: '#007BFF',
      },
      borderRadius: {
        lg: '0.75rem',
        md: '0.5rem',
        sm: '0.25rem',
      },
      keyframes: {
        'fade-in-down': {
          '0%': {
            opacity: '0',
            transform: 'translateY(-20px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        'fade-in-up': {
            '0%': {
              opacity: '0',
              transform: 'translateY(20px)',
            },
            '100%': {
              opacity: '1',
              transform: 'translateY(0)',
            },
          }
      },
      animation: {
        'fade-in-down': 'fade-in-down 0.5s ease-out forwards',
        'fade-in-up': 'fade-in-up 0.5s ease-out forwards',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};