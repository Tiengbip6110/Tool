from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8000/test.html')

    # Wait for initial load
    page.wait_for_selector('.lock-screen', state='visible')
    print("Lock screen is visible.")

    # Click digits 3 3 1 0
    # The digits are actually buttons with class 'num-btn' and data-value
    page.click('button.num-btn[data-value="3"]')
    page.click('button.num-btn[data-value="3"]')
    page.click('button.num-btn[data-value="1"]')
    page.click('button.num-btn[data-value="0"]')
    print("Clicked 3 3 1 0")

    page.screenshot(path='/home/jules/verification/debug_click_result.png')

    # Wait for main content
    page.wait_for_selector('#main-content', state='visible', timeout=5000)
    print("Main content visible!")

    page.screenshot(path='/home/jules/verification/final_screenshot.png')

    browser.close()
