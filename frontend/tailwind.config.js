/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'background': '#1a1a1a',
        'sidebar': '#2c2c2c',
        'card': '#252525',
        'card-alt': '#1e1e1e',
        'accent': '#4f46e5',
        'accent-hover': '#4338ca',
        'text-primary': '#ffffff',
        'text-secondary': '#a1a1aa',
        'border': '#3f3f46',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
