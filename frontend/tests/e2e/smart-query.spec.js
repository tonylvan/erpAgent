/**
 * GSD 智能问数 E2E 端到端测试
 * 覆盖：完整用户流程、页面交互、API 集成
 * 总计 11 个测试用例
 */
import { test, expect } from '@playwright/test';

test.describe('GSD Smart Query E2E Tests', () => {
  // 测试前准备
  test.beforeEach(async ({ page }) => {
    // 访问智能问数页面
    await page.goto('http://localhost:5176/smart-query');
    await page.waitForLoadState('networkidle');
  });

  // ==================== 页面加载测试 (2 个) ====================

  test('should load smart query page successfully', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/GSD/);
    
    // 验证主标题存在
    const header = page.locator('h2');
    await expect(header).toContainText('智能问数');
  });

  test('should display welcome message', async ({ page }) => {
    // 验证欢迎消息
    const welcomeMessage = page.locator('.welcome-message');
    await expect(welcomeMessage).toBeVisible();
    await expect(welcomeMessage).toContainText('你好！我是 GSD 智能问数助手');
  });

  // ==================== 快速问题测试 (2 个) ====================

  test('should display quick questions', async ({ page }) => {
    // 验证快速问题标签存在
    const quickQuestions = page.locator('.question-tag');
    await expect(quickQuestions).toHaveCount({ min: 3 });
  });

  test('should send query on quick question click', async ({ page }) => {
    // 点击第一个快速问题
    const firstQuestion = page.locator('.question-tag').first();
    const questionText = await firstQuestion.textContent();
    
    await firstQuestion.click();
    
    // 等待消息发送
    await page.waitForTimeout(2000);
    
    // 验证用户消息已显示
    const userMessages = page.locator('.message-item.user');
    await expect(userMessages).toHaveCount({ min: 1 });
  });

  // ==================== 消息发送测试 (3 个) ====================

  test('should send message via input', async ({ page }) => {
    // 输入消息
    const input = page.locator('input[placeholder*="输入"]');
    await input.fill('销售趋势');
    
    // 点击发送按钮
    const sendButton = page.locator('button[type="primary"]').first();
    await sendButton.click();
    
    // 等待响应
    await page.waitForTimeout(3000);
    
    // 验证消息已发送
    const messages = page.locator('.message-item');
    await expect(messages).toHaveCount({ min: 2 });
  });

  test('should send message on Enter key', async ({ page }) => {
    const input = page.locator('input[placeholder*="输入"]');
    await input.fill('客户排行');
    await input.press('Enter');
    
    await page.waitForTimeout(3000);
    
    const userMessages = page.locator('.message-item.user');
    await expect(userMessages).toHaveCount({ min: 1 });
  });

  test('should not send empty message', async ({ page }) => {
    const input = page.locator('input[placeholder*="输入"]');
    await input.fill('');
    await input.press('Enter');
    
    await page.waitForTimeout(1000);
    
    // 空消息不应该发送
    const messages = page.locator('.message-item');
    const count = await messages.count();
    expect(count).toBeLessThanOrEqual(1); // 最多只有欢迎消息
  });

  // ==================== 响应展示测试 (2 个) ====================

  test('should display assistant response', async ({ page }) => {
    // 发送查询
    const input = page.locator('input[placeholder*="输入"]');
    await input.fill('库存预警');
    await input.press('Enter');
    
    // 等待响应
    await page.waitForTimeout(3000);
    
    // 验证 AI 响应存在
    const assistantMessages = page.locator('.message-item.assistant');
    await expect(assistantMessages).toHaveCount({ min: 1 });
    
    // 验证响应内容包含文字
    const messageContent = assistantMessages.locator('.message-text');
    await expect(messageContent.first()).toBeVisible();
  });

  test('should display loading indicator', async ({ page }) => {
    // 发送查询
    const input = page.locator('input[placeholder*="输入"]');
    await input.fill('统计概览');
    
    // 在请求完成前检查加载状态
    await input.press('Enter');
    
    // 验证加载指示器出现
    const loadingIndicator = page.locator('.loading-indicator');
    await expect(loadingIndicator).toBeVisible({ timeout: 2000 });
  });

  // ==================== 反馈功能测试 (1 个) ====================

  test('should display feedback buttons', async ({ page }) => {
    // 发送查询获取响应
    const input = page.locator('input[placeholder*="输入"]');
    await input.fill('销售数据');
    await input.press('Enter');
    
    await page.waitForTimeout(3000);
    
    // 验证反馈按钮存在
    const feedbackButtons = page.locator('.feedback-buttons button');
    await expect(feedbackButtons.first()).toBeVisible();
  });

  // ==================== 推荐问题测试 (1 个) ====================

  test('should display recommended questions in sidebar', async ({ page }) => {
    // 验证侧边栏存在
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).toBeVisible();
    
    // 验证推荐问题存在
    const recommendedQuestions = page.locator('.recommended-questions button');
    await expect(recommendedQuestions).toHaveCount({ min: 3 });
  });

  // ==================== 错误处理测试 (1 个) ====================

  test('should handle network error gracefully', async ({ page }) => {
    // 模拟网络错误（通过拦截请求）
    await page.route('**/api/v1/query', route => route.abort('failed'));
    
    // 发送查询
    const input = page.locator('input[placeholder*="输入"]');
    await input.fill('测试错误处理');
    await input.press('Enter');
    
    // 等待
    await page.waitForTimeout(3000);
    
    // 页面不应该崩溃
    await expect(page).toHaveURL(/smart-query/);
  });
});
