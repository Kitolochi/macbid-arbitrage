import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        profit: {
          high: "#16a34a",
          mid: "#ca8a04",
          low: "#dc2626",
        },
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
export default config;
