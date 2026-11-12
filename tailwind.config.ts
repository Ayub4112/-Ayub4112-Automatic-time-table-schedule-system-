import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        vu: {
          navy: "#1f2937",
          blue: "#315f9f",
          sky: "#669bcf",
          red: "#e2282b",
          mist: "#f4f6fa",
          silver: "#a3a3a3",
        },
      },
      boxShadow: {
        "vu": "0 18px 45px rgba(31, 41, 55, 0.18)",
      },
    },
  },
  plugins: [],
};

export default config;
