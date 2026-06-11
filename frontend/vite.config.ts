import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ["react-plotly.js", "plotly.js-dist-min"],
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  preview: {
    // vite >=5.4.12 rejects unknown Host headers by default; allow the Railway domain
    allowedHosts: true,
  },
});
