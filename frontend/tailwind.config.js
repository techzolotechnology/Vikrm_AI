/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(240 10% 6%)",
        surface: "hsl(240 8% 10%)",
        border: "hsl(240 6% 18%)",
        primary: {
          DEFAULT: "#7C3AED",
          hover: "#8B5CF6",
        },
        accent: "#22D3EE",
        success: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        sans: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      backgroundImage: {
        "gradient-brand": "linear-gradient(135deg, #7C3AED 0%, #22D3EE 100%)",
        "gradient-aurora": "linear-gradient(135deg, #7C3AED 0%, #EC4899 40%, #22D3EE 100%)",
        "gradient-subtle": "linear-gradient(180deg, rgba(124,58,237,0.08) 0%, transparent 100%)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.8" },
          "70%": { transform: "scale(1.6)", opacity: "0" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
        "trace": {
          to: { strokeDashoffset: "0" },
        },
        "aurora": {
          "0%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
          "100%": { backgroundPosition: "0% 50%" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        "float-delayed": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: "0.5", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.05)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "flow-down": {
          "0%": { strokeDashoffset: "100", opacity: "0" },
          "20%": { opacity: "1" },
          "100%": { strokeDashoffset: "0", opacity: "1" },
        },
        "particle-float": {
          "0%": { transform: "translateY(100vh) translateX(0)", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { transform: "translateY(-10vh) translateX(30px)", opacity: "0" },
        },
        "gradient-shift": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        "border-glow": {
          "0%, 100%": { borderColor: "rgba(124,58,237,0.3)" },
          "50%": { borderColor: "rgba(34,211,238,0.6)" },
        },
        "count-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "node-pulse": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(124,58,237,0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(124,58,237,0)" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.2,0.6,0.4,1) infinite",
        "trace": "trace 2.4s linear infinite",
        "aurora": "aurora 8s ease infinite",
        "float": "float 6s ease-in-out infinite",
        "float-delayed": "float-delayed 8s ease-in-out infinite 2s",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
        "slide-up": "slide-up 0.6s ease-out forwards",
        "gradient-shift": "gradient-shift 6s ease infinite",
        "border-glow": "border-glow 3s ease-in-out infinite",
        "node-pulse": "node-pulse 2s ease-in-out infinite",
      },
      boxShadow: {
        "glow-sm": "0 0 15px rgba(124,58,237,0.3)",
        "glow-md": "0 0 30px rgba(124,58,237,0.4)",
        "glow-lg": "0 0 60px rgba(124,58,237,0.5)",
        "glow-accent": "0 0 30px rgba(34,211,238,0.3)",
        "glow-success": "0 0 20px rgba(34,197,94,0.3)",
        "card-hover": "0 20px 60px rgba(0,0,0,0.5), 0 0 30px rgba(124,58,237,0.15)",
        "glass": "0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
      },
    },
  },
  plugins: [],
};
