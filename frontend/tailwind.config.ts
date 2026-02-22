import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        'matte-black':    '#0a0a0a',
        'deep-charcoal':  '#121212',
        'electric-blue':  '#00f0ff',
        'champagne-gold': '#d4af37',
        'surface':        '#1a1a1a',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-blue':  'glowBlue 2s ease-in-out infinite alternate',
        'glow-gold':  'glowGold 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glowBlue: {
          '0%':   { boxShadow: '0 0 5px rgba(0,240,255,0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0,240,255,0.5)' },
        },
        glowGold: {
          '0%':   { boxShadow: '0 0 5px rgba(212,175,55,0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(212,175,55,0.5)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
