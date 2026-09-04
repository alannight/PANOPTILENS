import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(0, 0%, 8%)",
        foreground: "hsl(0, 0%, 95%)",
        card: "hsl(0, 0%, 12%)",
        "card-foreground": "hsl(0, 0%, 95%)",
        popover: "hsl(0, 0%, 10%)",
        "popover-foreground": "hsl(0, 0%, 95%)",
        primary: "hsl(0, 0%, 95%)",
        "primary-foreground": "hsl(0, 0%, 8%)",
        secondary: "hsl(0, 0%, 16%)",
        "secondary-foreground": "hsl(0, 0%, 95%)",
        muted: "hsl(0, 0%, 16%)",
        "muted-foreground": "hsl(0, 0%, 60%)",
        accent: "hsl(12, 75%, 55%)",
        "accent-foreground": "hsl(0, 0%, 95%)",
        destructive: "hsl(0, 84%, 60%)",
        "destructive-foreground": "hsl(0, 0%, 95%)",
        border: "hsl(0, 0%, 20%)",
        input: "hsl(0, 0%, 20%)",
        ring: "hsl(12, 75%, 55%)",
        success: "hsl(142, 76%, 36%)",
        warning: "hsl(38, 92%, 50%)",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "SF Mono", "Menlo", "Consolas", "Liberation Mono", "monospace"],
      },
      borderRadius: {
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
      },
    },
  },
  plugins: [],
};

export default config;
