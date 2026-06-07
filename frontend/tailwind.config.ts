import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#102326",
        navy: "#18324a",
        teal: "#0f766e",
        panel: "#ffffff",
        line: "#d9e2e3",
      },
      boxShadow: {
        soft: "0 16px 40px rgba(20, 46, 54, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

