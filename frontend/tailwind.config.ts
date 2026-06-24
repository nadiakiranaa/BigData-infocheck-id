import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        ink: '#060914',
        panel: '#0d1424',
        panelSoft: '#111b2f',
        line: '#20314d',
        cyanSignal: '#22d3ee',
        amberSignal: '#fbbf24',
        dangerSignal: '#fb7185',
      },
      boxShadow: {
        glow: '0 0 32px rgba(34, 211, 238, 0.18)',
      },
    },
  },
  plugins: [],
} satisfies Config;
