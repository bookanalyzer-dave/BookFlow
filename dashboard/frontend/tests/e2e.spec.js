import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('end-to-end test', async ({ page }) => {
  // Navigate to the app
  await page.goto('http://localhost:5173/');

  // Click the "Register" button to show the registration form
  await page.click('button:has-text("Register")');

  // Generate a unique email for each test run
  const randomString = Math.random().toString(36).substring(7);
  const email = `test-${randomString}@example.com`;
  const password = 'password123';

  // Fill in the registration credentials
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);

  // Click the register button
  await page.click('button:has-text("Register")');

  // Wait for registration to complete and login form to appear
  await page.waitForSelector('button:has-text("Login")');

  // Fill in the login credentials
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);

  // Click the login button
  await page.click('button:has-text("Login")');

  // Wait for navigation to the dashboard (or home page)
  // Wait for the logout button to appear, indicating a successful login
  // Expect the logout button to be visible
  await expect(page.locator('button:has-text("Logout")')).toBeVisible({ timeout: 10000 });

  // Select the file for upload
  const filePath = path.resolve(__dirname, '../../../Testbuch1_Foto1.jpg');
  await page.setInputFiles('input[type="file"]', filePath);

  // Click the upload button
  await page.click('button:has-text("Upload")');

  // Wait for the book to appear in the book list
  // Wait for the book to appear in the book list and expect it to be visible
  const bookLocator = page.locator('h3:has-text("Testbuch1_Foto1.jpg")');
  await expect(bookLocator).toBeVisible({ timeout: 60000 });

  // Wait for the status to not be "analysis_failed"
  const bookStatus = page.locator('//h3[contains(text(), "Testbuch1_Foto1.jpg")]/following-sibling::p/i');
  await expect(bookStatus).not.toHaveText('analysis_failed', { timeout: 20000 });
});