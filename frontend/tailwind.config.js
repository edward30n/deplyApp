/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        recway: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        }
      },
      animation: {
        'gradient-x': 'gradient-x 15s ease infinite',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'pulse-glow': 'pulse-glow 2s infinite',
      },
      keyframes: {
        'gradient-x': {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          }
        },
        'fadeIn': {
          'from': {
            'opacity': '0',
            'transform': 'translateY(-20px)'
          },
          'to': {
            'opacity': '1',
            'transform': 'translateY(0)'
          }
        },
        'pulse-glow': {
          '0%': {
            'box-shadow': '0 0 15px 5px rgba(255, 255, 255, 0.3), 0 0 30px 15px rgba(255, 255, 255, 0.1)'
          },
          '50%': {
            'box-shadow': '0 0 20px 10px rgba(255, 255, 255, 0.4), 0 0 40px 20px rgba(255, 255, 255, 0.15)'
          },
          '100%': {
            'box-shadow': '0 0 15px 5px rgba(255, 255, 255, 0.3), 0 0 30px 15px rgba(255, 255, 255, 0.1)'
          }
        }
      }
    },
  },
  plugins: [],
}
