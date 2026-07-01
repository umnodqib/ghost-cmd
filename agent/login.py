import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime

# ==========================================
PASSWORD = "Bismillah12345!"  # GANTI PASSWORDNYA
RECOVERY_EMAIL = "ferrynara12@gmail.com"
PROFILE_PREFIX = "gmail_prof"
START_INDEX = 1
EMAIL_FILE = "email.txt"
HISTORY_FILE = "history_skses.txt"
FORCE_LOGIN = True             # Ubah ke False kalau tidak mau force

BASE_PATH = "/home/ubuntu"
BASE_PROFILE_DIR = os.path.join(BASE_PATH, "chrome_profiles")
SCREENSHOT_DIR = os.path.join(BASE_PATH, "bukti_login")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(BASE_PROFILE_DIR, exist_ok=True)

# ==========================================
def take_screenshot(driver, email, status="DEBUG"):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{status}_{email}_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        driver.save_screenshot(filepath)
        print(f"  Screenshot: {filepath}")
    except:
        pass

# ==========================================
def create_driver(profile_path):
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--profile-directory=Default")
    
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# ==========================================
def login_gmail(driver, email):
    try:
        print(f"\n>>> Login: {email}")
        driver.get("https://accounts.google.com/" )
        wait = WebDriverWait(driver, 20)
        time.sleep(3)
        
        # Check if already logged in via persistent profile
        if "myaccount.google.com" in driver.current_url or "mail.google.com" in driver.current_url:
            print("  [INFO] Sudah login secara otomatis!")
            return True

        take_screenshot(driver, email, "MULAI")

        # STEP 1: Email
        print("  Step 1: Masukkin email...")
        email_input = wait.until(EC.visibility_of_element_located((By.NAME, "identifier")))
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(1)
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next' or text()='Berikutnya']/parent::button")))
        next_btn.click()
        time.sleep(5)

        # STEP 2: Password
        print("  Step 2: Masukkin password...")
        pw_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
        time.sleep(2) 
        # Use JS injection to bypass "Element Not Interactable"
        driver.execute_script(f"arguments[0].value = '{PASSWORD}';", pw_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", pw_input)
        time.sleep(1)
        pw_next = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next' or text()='Berikutnya']/parent::button")))
        pw_next.click()
        time.sleep(10)
        take_screenshot(driver, email, "AFTER_PASSWORD")
        
        # STEP 3: Handle Challenges (Recovery Email Confirmation)
        for attempt in range(5):
            current_url = driver.current_url
            page_source = driver.page_source
            
            if "challenge" in current_url or "selection" in current_url or "Verify it's you" in page_source:
                print(f"  Terdeteksi halaman verifikasi (Attempt {attempt+1})...")
                
                # Look for "Confirm your recovery email" option
                recovery_options = driver.find_elements(By.XPATH, "//div[contains(., 'recovery email') or contains(., 'email pemulihan')]")
                if recovery_options:
                    print("  Opsi recovery email ditemukan, mengklik...")
                    driver.execute_script("arguments[0].click();", recovery_options[0])
                    time.sleep(5)
                    
                    try:
                        # This is the field for CONFIRMING the recovery email address
                        recovery_input = wait.until(EC.visibility_of_element_located((By.NAME, "knowledgePrereqResponse")))
                        recovery_input.send_keys(RECOVERY_EMAIL)
                        recovery_input.send_keys(Keys.ENTER)
                        print(f"  Recovery email '{RECOVERY_EMAIL}' dimasukkan untuk konfirmasi.")
                        time.sleep(10)
                        continue
                    except: pass
                
                # If no direct option, try "Try another way" to find it
                try:
                    try_another = driver.find_elements(By.XPATH, "//div[text()='Try another way' or text()='Coba cara lain'] | //span[text()='Try another way' or text()='Coba cara lain']")
                    if try_another:
                        print("  Klik 'Try another way'...")
                        driver.execute_script("arguments[0].click();", try_another[0])
                        time.sleep(5)
                        continue
                except: pass

            # Skip optional home address page
            if "homeaddress" in current_url:
                try:
                    skip_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Skip' or text()='Lewati']/parent::button")))
                    skip_btn.click()
                    time.sleep(5)
                    continue
                except: pass
            
            time.sleep(3)

        # STEP 4: Final Check Success
        time.sleep(5)
        current_url = driver.current_url
        success_indicators = ["myaccount.google.com", "mail.google.com", "inbox"]
        
        if any(indicator in current_url for indicator in success_indicators) or email in driver.page_source:
            print(f"  SUKSES LOGIN: {email}")
            take_screenshot(driver, email, "SUKSES")
            return True
        else:
            print(f"  Gagal atau butuh verifikasi manual.")
            take_screenshot(driver, email, "GAGAL")
            return False

    except Exception as e:
        print(f"  Error: {e}")
        take_screenshot(driver, email, "ERROR")
        return False

# ==========================================
if __name__ == "__main__":
    with open(EMAIL_FILE, "w") as f:
        f.write("ferryidxgugel3@gmail.com\n")
            
    with open(EMAIL_FILE, "r") as f:
        emails = [line.strip() for line in f if line.strip()]

    for email in emails:
        folder_name = f"profile_{email.split('@')[0]}"
        profile_path = os.path.join(BASE_PROFILE_DIR, folder_name)
        os.makedirs(profile_path, exist_ok=True)
        driver = None
        try:
            driver = create_driver(profile_path)
            if login_gmail(driver, email):
                print(f"  ✓ {email} berhasil")
        finally:
            if driver: driver.quit()
            time.sleep(2)
