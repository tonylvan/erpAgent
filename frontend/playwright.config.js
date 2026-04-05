// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  
  // 超时配置
  timeout: 30 * 1000,
  expect: {
    timeout: 5000
  },
  
  // 失败重试
  retries: process.env.CI ? 2 : 0,
  
  // 并行执行
  workers: process.env.CI ? 1 : undefined,
  
  // 报告器
  reporter: 'html',
  
  // 共享配置
  use: {
    // 基础 URL
    baseURL: 'http://localhost:5176',
    
    // 截图
    screenshot: 'only-on-failure',
    
    // 视频
    video: 'retain-on-failure',
    
    // 追踪
    trace: 'retain-on-failure',
  },

  // 浏览器配置
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // 本地服务器配置（可选）
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5176',
  //   reuseExistingServer: !process.env.CI,
  // },
});
