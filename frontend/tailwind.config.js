/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Outfit", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        kick: {
          "0%, 100%": { transform: "translateY(0) rotate(0deg)" },
          "50%": { transform: "translateY(-22px) rotate(180deg)" },
        },
        loadbar: {
          "0%": { transform: "translateX(-130%)" },
          "100%": { transform: "translateX(280%)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.45s ease-out",
        kick: "kick 0.9s ease-in-out infinite",
        loadbar: "loadbar 1.3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
