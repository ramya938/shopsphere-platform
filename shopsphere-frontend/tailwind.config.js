/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bgLight: '#f8fafc',
        bgDark: '#0b0f19',
        cardLight: '#ffffff',
        cardDark: '#131924',
        borderLight: '#e2e8f0',
        borderDark: '#222d42',
        textLight: '#1e293b',
        textDark: '#f1f5f9',
        primary: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
        },
        secondary: {
          DEFAULT: '#06b6d4',
          hover: '#0891b2',
        },
      },
      fontFamily: {
        heading: ['Outfit', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        premium: '0 10px 30px -10px rgba(0,0,0,0.1)',
        glass: '0 8px 32px 0 rgba(0, 0, 0, 0.2)',
      }
    },
  },
  plugins: [],
}
