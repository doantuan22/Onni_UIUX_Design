import type { Config } from "tailwindcss";
export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: { extend: { colors: { brand: { 500: "#4f46e5", 600: "#4338ca" } }, fontFamily: { sans: ["var(--font-inter)"] } } },
} satisfies Config;
