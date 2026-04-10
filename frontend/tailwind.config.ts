import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--bg-primary)",
        foreground: "var(--text-primary)",
        primary: "var(--accent-blue)",
        success: "var(--accent-green)",
        danger: "var(--accent-red)",
        warning: "var(--accent-amber)",
        surface: "var(--bg-secondary)",
        border: "var(--border)",
        muted: "var(--text-muted)",
        secondaryText: "var(--text-secondary)"
      },
    },
  },
  plugins: [],
};
export default config;
