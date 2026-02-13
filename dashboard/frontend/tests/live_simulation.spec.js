import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('Live Simulation User Flow', async ({ page }) => {
  // Increase test timeout to 5 minutes to allow full agent chain execution
  test.setTimeout(300000); 
  const LIVE_URL = 'https://project-52b2fab8-15a1-4b66-9f3.web.app';
  
  // 1. Generate unique email
  const timestamp = Date.now();
  const email = `test-${timestamp}@simulation.com`;
  const password = 'Password123!'; // Stronger password just in case

  console.log(`Starting simulation with user: ${email}`);

  // Capture browser console logs
  page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));

  try {
    // 2. Navigation & Registration
    console.log(`Navigating to ${LIVE_URL}...`);
    await page.goto(LIVE_URL);
    await page.waitForLoadState('networkidle');

    // Check if we are already on /register
    if (!page.url().includes('/register')) {
        console.log('Not on register page, looking for Register link...');
        
        // Try to find the link more robustly
        const registerLink = page.locator('a[href="/register"]');
        
        if (await registerLink.count() > 0 && await registerLink.isVisible()) {
            console.log('Clicking Register link...');
            await registerLink.click();
            await page.waitForURL('**/register');
        } else {
             // Maybe we are logged in?
             if (await page.locator('button:has-text("Logout")').isVisible()) {
                 console.log('User already logged in, logging out first...');
                 await page.click('button:has-text("Logout")');
                 await page.waitForSelector('a[href="/register"]');
                 await page.click('a[href="/register"]');
                 await page.waitForURL('**/register');
             } else {
                 // Force navigation if link not found
                 console.log('Register link not found, forcing navigation to /register...');
                 await page.goto(`${LIVE_URL}/register`);
             }
        }
    }
    
    console.log('On Register page, filling form...');

    // Fill Registration
    await page.waitForSelector('input[type="email"]');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    
    // Click the Register button (on the register page, it is a button)
    // Wait for it to be visible first
    const submitButton = page.locator('button:has-text("Register")');
    await submitButton.waitFor();
    await submitButton.click();

    // 3. Verify Login
    // Strategy: Wait for Login button to appear (indicating successful reg -> redirect to login), 
    // then login, OR check if auto-logged in.
    
    try {
        await page.waitForSelector('button:has-text("Login")', { timeout: 10000 });
        console.log('Registration successful, proceeding to login...');
        
        // Perform Login
        await page.fill('input[type="email"]', email);
        await page.fill('input[type="password"]', password);
        await page.click('button:has-text("Login")');
    } catch (e) {
        console.log('Login button did not appear, checking if auto-logged in...');
    }

    // Verify we are logged in (Logout button visible)
    await expect(page.locator('button:has-text("Logout")')).toBeVisible({ timeout: 15000 });
    console.log('Login verified.');

    // 4. Navigate to /upload if necessary
    // Check if upload input is visible
    const fileInput = page.locator('input[type="file"]');
    if (!(await fileInput.isVisible())) {
        console.log('Upload form not visible, navigating to /upload...');
        await page.goto(`${LIVE_URL}/upload`);
    }

    // 5. Upload Image
    const imagePath = path.resolve(__dirname, '../../../test_books/Testbuch1_Foto1.jpg');
    await page.setInputFiles('input[type="file"]', imagePath);

    // 6. Start Analysis
    // Match "Analyse starten" or "Upload & Analyse starten"
    await page.click('button:has-text("Analyse starten")');
    console.log('Analysis started...');

    // Wait for the upload/analysis to finish on the Upload page
    console.log('Waiting for initial analysis to complete on Upload page...');
    await page.waitForSelector('text=Erfolgreich analysiert!', { timeout: 60000 });
    console.log('Upload and initial analysis complete.');

    // Navigate to the Book List to see the result
    console.log('Navigating to Book List...');
    await page.click('a[href="/"]');
    await page.waitForURL(`${LIVE_URL}/`);

    // 7. Wait for Processing and Price
    console.log('Waiting for book to appear and price to be calculated (up to 4 minutes)...');

    // First wait for any book card to appear (means ingestion started/finished)
    // The list is initially empty for a new user.
    const bookCard = page.locator('div[style*="box-shadow"]').first(); // Assuming the card style from BookList.jsx
    await bookCard.waitFor({ state: 'visible', timeout: 60000 });
    console.log('Book card appeared in list.');

    // Now wait specifically for the price in the book card.
    // The price is rendered as: <p ...>€X.XX</p>
    // We look for text matching "€" inside the book card.
    const priceLocator = bookCard.locator('text=/€\\d+,?\\d*/');
    
    // Polling/Waiting for price
    try {
        await priceLocator.waitFor({ state: 'visible', timeout: 240000 }); // Wait up to 4 more minutes for price
        console.log('Price found!');
        
        const priceText = await priceLocator.textContent();
        console.log(`Detected Price: ${priceText}`);
        
        // Additional check: Ensure it's not €0.00 unless valid (usually we expect a real price)
        if (priceText.includes('€0.00')) {
             console.warn('Warning: Price is €0.00. This might indicate failure to find a price, but strictly speaking it IS a price.');
        }

    } catch (e) {
        console.error('Timeout waiting for price to appear.');
        // Capture screenshot of the state where price is missing
        await page.screenshot({ path: 'simulation_missing_price.png' });
        
        // Check if we have an error status
        const statusLocator = bookCard.locator('text=Fehler');
        if (await statusLocator.isVisible()) {
             console.error('Book status shows error.');
        }
        
        throw new Error('Price did not appear within timeout.');
    }
    
    console.log('Success: Price generated and displayed!');
    
    // Take success screenshot
    await page.screenshot({ path: 'simulation_success.png' });

  } catch (error) {
    console.error('Simulation failed:', error);
    await page.screenshot({ path: 'simulation_error.png' });
    throw error; // Fail the test
  }
});
