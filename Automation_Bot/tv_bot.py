import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingViewBot:
    def __init__(self, tv_username, tv_password):
        self.tv_username = tv_username
        self.tv_password = tv_password
        self.driver = None

    def start_driver(self):
        """Initializes the Chrome Driver with persistent profile to avoid constant logins."""
        options = Options()
        # options.add_argument("--headless")  # Uncomment for server mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        # Use a user-data-dir to save login session (cookies)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(script_dir, "chrome_profile")
        options.add_argument(f"user-data-dir={user_data_dir}")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logging.info("Chrome Driver started.")

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            logging.info("Chrome Driver closed.")

    def login(self):
        """Logs into TradingView if not already logged in."""
        self.driver.get("https://www.tradingview.com/")
        time.sleep(2)

        # Check if already logged in (look for avatar or profile menu)
        try:
            # This selector often changes, generic check for "Sign In" button
            sign_in_btn = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Open user menu']")
            if sign_in_btn:
                logging.info("Already logged in.")
                return
            
            # If not logged in, perform login flow (This is tricky due to Captcha, hence user-data-dir is preferred)
            logging.warning("Not logged in. Please log in manually in the browser window once, and it will be saved for future runs.")
            # Navigate to login page
            self.driver.get("https://www.tradingview.com/accounts/signin/")
            
            # Wait for user to log in manually (Hybrid approach is best for Bots to avoid Captcha issues)
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Open user menu']"))
            )
            logging.info("Login detected!")
            
        except Exception as e:
            logging.error(f"Login check failed: {e}")

    def manage_access(self, script_url, username, action="add", expiration_date=None):
        """
        Adds or removes a user from a specific Invite-Only script.
        action: 'add' or 'remove'
        expiration_date: 'YYYY-MM-DD' (optional)
        """
        try:
            if not self.driver:
                self.start_driver()
                self.login()

            logging.info(f"Navigating to script: {script_url}")
            self.driver.get(script_url)
            time.sleep(3)

            # Click "Manage Access" button
            # Note: Selectors are fragile and may need updates if TV updates UI
            manage_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Manage Access')]"))
            )
            manage_btn.click()
            time.sleep(2)

            # Switch to the modal context if necessary (usually it's just a div overlay)
            
            if action == "add":
                # Find input field
                input_field = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Username']")
                input_field.clear()
                input_field.send_keys(username)
                time.sleep(1)

                # Set expiration if provided (Advanced logic needed here for date picker)
                # For MVP, we just add permanent access or manage removal via bot later
                
                # Click "Add" button
                add_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add')]")
                add_btn.click()
                logging.info(f"Added user: {username}")

            elif action == "remove":
                # Search for user in the list (or just scroll/find)
                # This is complex in UI. 
                # Alternative: Just use the search box if available in the list section
                # For MVP: We assume the list is visible.
                
                # Find the 'X' button next to the username
                # pseudo-code xpath: //div[text()='username']/following-sibling::button[@icon='close']
                delete_btn = self.driver.find_element(By.XPATH, f"//span[contains(text(), '{username}')]/ancestor::div[contains(@class, 'row')]//button[contains(@class, 'delete')]")
                delete_btn.click()
                logging.info(f"Removed user: {username}")

            # Save/Close
            # Some modals autosave, some need "Apply". TV usually autosaves on "Add".
            # Close modal
            close_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-name='close']")
            close_btn.click()
            
            return True

        except Exception as e:
            logging.error(f"Error managing access: {e}")
            return False
        finally:
            # We don't close driver here to keep session alive for next request if high volume
            # But for low volume, maybe close it.
            pass

if __name__ == "__main__":
    # Test Run
    bot = TradingViewBot("your_tv_username", "your_tv_password")
    bot.start_driver()
    # bot.login() # First time run requires manual login
    # bot.manage_access("https://www.tradingview.com/script/YOUR_SCRIPT_ID/", "TargetUser123", "add")
