import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base -- назва репозиторію на GitHub Pages. Якщо репозиторій називається
// інакше ніж "weather-song-arena", зміни цей рядок (напр. на "/my-repo/").
// Якщо сайт розгортається на *.github.io (репозиторій-профіль), онови на "/".
export default defineConfig({
  plugins: [react()],
  base: "/model_comparison/",
  build: {
    outDir: "../docs",
    emptyOutDir: true,
  },
});
