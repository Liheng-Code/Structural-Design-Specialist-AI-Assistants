import type { Config } from "tailwindcss";

// Colours are CSS variables (app/globals.css) so light and dark themes share one set of class names.
const v = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: v("paper"),
        sheet: v("sheet"),
        ink: v("ink"),
        ink2: v("ink-2"),
        rule: v("rule"),
        rule2: v("rule-strong"),
        accent: v("accent"),
        accentsoft: v("accent-soft"),
        ok: v("ok"),
        oksoft: v("ok-soft"),
        warn: v("warn"),
        warnsoft: v("warn-soft"),
        bad: v("bad"),
        badsoft: v("bad-soft"),
      },
      fontFamily: {
        display: ['"Barlow Condensed"', '"Arial Narrow"', "Arial", "sans-serif"],
        sans: ['"IBM Plex Sans"', '"Segoe UI"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "Consolas", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
