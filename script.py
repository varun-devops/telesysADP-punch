from playwright.sync_api import sync_playwright
import os
import sys

LOGIN_URL = "https://telesyssoftware.securtime.adp.com/login?redirectUrl=%2Fwelcome"
USERNAME = os.environ.get("PUNCH_USERNAME") or "varun.singh@telesys.com"
PASSWORD = os.environ.get("PUNCH_PASSWORD") or "telesys"
ACTION = os.environ.get("PUNCH_ACTION", "in")


def save_debug(page, prefix):
    page.screenshot(path=f"{prefix}.png", full_page=True)
    with open(f"{prefix}.html", "w", encoding="utf-8") as debug_file:
        debug_file.write(page.content())


def login(page):
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector('input[type="email"], input[formcontrolname="userName"]', timeout=60000)
    page.fill('input[type="email"]', USERNAME)
    page.fill('input[type="password"]', PASSWORD)
    page.click('button[type="submit"]:has-text("Sign In")')

    try:
        # Consider login successful if welcome header or punch buttons appear.
        page.wait_for_selector(
            'h2:has-text("Welcome!"), button:has-text("Punch In"), button:has-text("Punch Out")',
            timeout=45000,
        )
        print("Logged in successfully!")
    except Exception:
        print("Login did not reach home page. Saving debug artifacts...")
        save_debug(page, "login_debug")
        raise

def run():
    with sync_playwright() as p:
        is_github = os.environ.get("GITHUB_ACTIONS") == "true"
        browser = p.chromium.launch(headless=is_github) 
        context = browser.new_context(
            permissions=['geolocation'],
            geolocation={'latitude': 28.6139, 'longitude': 77.2090}
        )
        page = context.new_page()

        print(f"Starting Punch {ACTION.upper()} process...")
        login(page)

        if ACTION == "in":
            try:
                page.click('button:has-text("Punch In")')
                page.wait_for_selector('text=Punch IN submission successfully', timeout=30000)
                print("Punch In Successful.")
            except Exception as e:
                print("Punch In failed or already punched in?", e)
                page.screenshot(path="error_punch_in.png")
            
        elif ACTION == "out":
            try:
                page.click('button:has-text("Punch Out")')
                # Wait for success message
                page.wait_for_selector('h2.new-title:has-text("Success...!")', timeout=30000)
                print("Punch Out Successful.")
            except Exception as e:
                print("Punch Out failed or already punched out?", e)
                page.screenshot(path="error_punch_out.png")
            
            print("Refreshing page to reveal Dashboard tab...")
            page.reload()
            
            print("Logging in again after refresh...")
            login(page)
            
            print("Clicking Dashboard tab...")
            # Click the Dashboard link
            page.click('a[href="/dashboard"]')
            
            # Wait for the dashboard "Myself" span to load
            page.wait_for_selector('span.ffc-header:has-text("Myself")', timeout=15000)
            print("Dashboard loaded.")
            
            page.screenshot(path="dashboard_screenshot.png")
            print("Screenshot taken and saved as dashboard_screenshot.png")  
        else:
            print(f"Unknown action: {ACTION}")
        context.close()
        browser.close()

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)
