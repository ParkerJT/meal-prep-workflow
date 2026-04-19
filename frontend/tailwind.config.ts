import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        utilitarian: {
          background: "#6B705C",
          text: "#1A1A1A",
          accent: "#FF5722",
          input: "#2B2B2B",
          surface: "#8D927D",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Arial", "Helvetica", "sans-serif"],
        heading: ["var(--font-bebas-neue)", "Impact", "sans-serif"],
      },
      boxShadow: {
        stamp: "2px 2px 0 #000000",
      },
      borderWidth: {
        3: "3px",
      },
    },
  },
};

export default config;
