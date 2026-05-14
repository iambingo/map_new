import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 10_000,
  retries: 0,
  reporter: "html",
  use: {
    baseURL: "http://localhost:8001",
  },
});
