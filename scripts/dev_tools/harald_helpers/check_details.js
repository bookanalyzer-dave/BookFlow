const { chromium } = require('playwright-chromium');

(async () => {
  console.log('--- STARTING BOOK DETAILS CHECK ---');
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'] 
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    const testEmail = `harald_check_${Date.now()}@hacker.net`;
    console.log('1. Registering/Logging in...');
    await page.goto('https://project-52b2fab8-15a1-4b66-9f3.web.app/register');
    await page.fill('input[placeholder*="Email"]', testEmail);
    await page.fill('input[placeholder*="Password"]', 'TestPass123!');
    await page.click('button:has-text("Register")');
    await page.waitForTimeout(5000);

    console.log('2. Uploading book to trigger full pipeline...');
    await page.goto('https://project-52b2fab8-15a1-4b66-9f3.web.app/upload');
    const fileInput = await page.$('input[type="file"]');
    await fileInput.setInputFiles('source/test_books/Testbuch1_Foto1.jpg');
    await page.click('button:has-text("Upload & Analyse starten")');

    console.log('3. Waiting for status change to needs_review or ingested...');
    // Wir warten geduldig auf die KI
    await page.waitForTimeout(45000); 

    console.log('4. Checking Book List for the entry...');
    await page.goto('https://project-52b2fab8-15a1-4b66-9f3.web.app/');
    await page.waitForTimeout(5000);
    
    const hasBook = await page.textContent('body');
    console.log('Book visible in list:', hasBook.includes('Ein Geheimnis'));
    await page.screenshot({ path: 'final_list_check.png' });

    if (hasBook.includes('Ein Geheimnis')) {
        console.log('5. Clicking on book to see details...');
        await page.click('text=Ein Geheimnis');
        await page.waitForTimeout(5000);
        await page.screenshot({ path: 'final_details_view.png', fullPage: true });
        
        const content = await page.textContent('body');
        console.log('--- CONTENT ANALYSIS ---');
        console.log('Found Title:', content.includes('Ein Geheimnis'));
        console.log('Found ISBN:', content.includes('978-3-518-45920-1'));
        console.log('Found Author:', content.includes('Philippe Grimbert'));
        // Check für Pricing/Condition
        console.log('Found Price:', content.includes('€'));
        console.log('------------------------');
    }

  } catch (error) {
    console.error('CHECK FAILED:', error);
  } finally {
    await browser.close();
    console.log('--- TEST FINISHED ---');
  }
})();
