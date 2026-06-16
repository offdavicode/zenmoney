import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', 'sans-serif'],
      },
      colors: {
        background: "var(--color-background)",
        surface: "var(--color-surface)",
        'surface-hover': "var(--color-surface-hover)",
        border: "var(--color-border)",
        
        foreground: "var(--color-text-primary)",
        primary: "var(--color-brand-500)",
        secondary: "var(--color-text-secondary)",
        muted: "var(--color-text-muted)",
        
        brand: {
          50: "var(--color-brand-50)",
          100: "var(--color-brand-100)",
          500: "var(--color-brand-500)",
          600: "var(--color-brand-600)",
          900: "var(--color-brand-900)",
        },
        
        emotion: {
          calm: "var(--accent-blue)",
          happy: "var(--accent-green)",
          angry: "var(--accent-red)",
          frustrated: "var(--accent-pink)",
          excited: "var(--accent-amber)",
          anxious: "var(--accent-purple)",
        }
      },
      animation: {
        'fade-in': 'var(--animate-fade-in)',
        'slide-up': 'var(--animate-slide-up)',
        'pulse-slow': 'var(--animate-pulse-slow)',
      }
    },
  },
  plugins: [],
};
export default config;
