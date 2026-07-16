/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B3B5C",        // deep clinical navy — headings, primary actions
        tealline: "#12877F",   // ECG-trace teal — accents, active states
        canvas: "#F4F7FA",     // page background
        card: "#FFFFFF",
        slateline: "#CBD5E1",
        risk: {
          high: "#B91C1C",
          moderate: "#B45309",
          low: "#15803D",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
}
