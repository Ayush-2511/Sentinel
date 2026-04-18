/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: "#080F17",
        navyMid: "#0D1B2A",
        navyCard: "#0F2030",
        navyBorder: "#1A3045",
        teal: "#00D4B8",
        tealDim: "#007A6B",
        tealGlow: "rgba(0,212,184,0.12)",
        danger: "#FF3D5A",
        dangerDim: "rgba(255,61,90,0.15)",
        warning: "#FFB020",
        warningDim: "rgba(255,176,32,0.15)",
        success: "#00E57A",
        successDim: "rgba(0,229,122,0.1)",
        white: "#E8F4F8",
        muted: "#4A7090",
        muted2: "#2A4560"
      },
      fontFamily: {
        mono: ['Share Tech Mono', 'monospace'],
        ui: ['Barlow Condensed', 'sans-serif'],
        data: ['Rajdhani', 'sans-serif']
      }
    },
  },
  plugins: [],
}
