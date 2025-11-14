import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for MSW Mock Handler Testing
 *
 * Purpose: Browser-based integration and E2E testing of MSW service workers
 * Prerequisites: Test frontend app running on http://localhost:5173
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/playwright',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'reports/playwright' }],
    ['list'],
    ['json', { outputFile: 'reports/playwright/test-results.json' }]
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL for navigation */
    baseURL: 'http://localhost:5173',

    /* Collect trace on failure for debugging */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'retain-on-failure',

    /* Maximum time each action can take */
    actionTimeout: 10000,

    /* Maximum navigation timeout */
    navigationTimeout: 30000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        /* Browser context options */
        viewport: { width: 1280, height: 720 },
        /* Enable localStorage for token storage testing */
        storageState: undefined,
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 },
      },
    },

    /* Mobile testing (optional, enable when needed) */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
  ],

  /* Run local dev server before starting tests (when test frontend is ready) */
  // webServer: {
  //   command: 'cd test-frontend && npm run dev',
  //   url: 'http://localhost:5173',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120000,
  // },

  /* Global timeout for each test */
  timeout: 60000,

  /* Maximum time expect() should wait for condition */
  expect: {
    timeout: 10000,
  },

  /* Output directory for test artifacts */
  outputDir: 'reports/playwright/test-results',
});
