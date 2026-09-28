import {defineConfig} from '@playwright/test';

export default defineConfig({
  testDir:'tests/browser', workers:1, timeout:30000,
  use:{baseURL:'http://127.0.0.1:4173', launchOptions:process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {}},
  webServer:{command:'node tests/browser/server.mjs', url:'http://127.0.0.1:4173/admin/', reuseExistingServer:!process.env.CI}
});
