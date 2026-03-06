from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8000/test.html')

    # Wait for initial load
    page.wait_for_selector('.lock-screen', state='visible')
    print("Lock screen is visible.")

    # Click digits 3 3 1 0
    # The digits are actually elements with class 'digit' and data-value, wait let's inspect the DOM
    # They might be div or buttons. Let's just use text content or class.
    page.click('.lock-form .digit:has-text("3")')
    page.click('.lock-form .digit:has-text("3")')
    page.click('.lock-form .digit:has-text("1")')
    page.click('.lock-form .digit:has-text("0")')
    print("Clicked 3 3 1 0")

    # Wait for main content
    page.wait_for_selector('.main-content', state='visible', timeout=10000)
    print("Main content visible!")

    page.screenshot(path='/home/jules/verification/debug_unlocked.png')

    browser.close()
