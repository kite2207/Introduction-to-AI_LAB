import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      // Allow importing the graph data from the project root (../data),
      // which lives outside the frontend/ Vite root.
      allow: [fileURLToPath(new URL("..", import.meta.url))],
    },
  },
});
