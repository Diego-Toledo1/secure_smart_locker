/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'locker-orange': {
          DEFAULT: '#FF6B00',
          hover: '#E65100',
          light: '#FF9E40'
        },
        'locker-black': {
          DEFAULT: '#0F0F0F',
          surface: '#1A1A1A',
          border: '#333333'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}