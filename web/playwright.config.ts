import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "e2e",
  workers: 1,
  use: {
    baseURL: process.env.SCE_REPORT_URL || "http://127.0.0.1:8765",
    viewport: { width: 1600, height: 1000 },
    launchOptions: {
      executablePath:
        process.env.CHROME_PATH ||
        (process.env.CI
          ? undefined
          : "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    },
  },
  reporter: "list",
});
