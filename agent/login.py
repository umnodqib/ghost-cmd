import os
import time
import sys
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime

# ==========================================
# ⚙️ CONFIG
# ==========================================
# Default values, will be overridden by credentials.json if exists
DEFAULT_PASSWORD = "Bismillah12345!"
RECOVERY_EMAIL = "ferrynara12@gmail.com"
EMAIL_FILE = "email.txt"
CREDENTIALS_FILE = "credentials.json"
MAPPING_FILE = "mapping_profil.txt"

BASE_PATH = os.getcwd()
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
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# ==========================================
def login_gmail(driver, email, password):
    try:
        print(f"\n>>> Login: {email}")
        driver.get("https://accounts.google.com/")
        wait = WebDriverWait(driver, 20)
        time.sleep(3)
        
        # Check if already logged in
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
        driver.execute_script(f"arguments[0].value = '{password}';", pw_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", pw_input)
        time.sleep(1)
        pw_next = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next' or text()='Berikutnya']/parent::button")))
        pw_next.click()
        time.sleep(10)
        take_screenshot(driver, email, "AFTER_PASSWORD")
        
        # STEP 3: Handle Challenges
        for attempt in range(3):
            current_url = driver.current_url
            page_source = driver.page_source
            
            if "challenge" in current_url or "selection" in current_url or "Verify it's you" in page_source:
                print(f"  Terdeteksi halaman verifikasi...")
                recovery_options = driver.find_elements(By.XPATH, "//div[contains(., 'recovery email') or contains(., 'email pemulihan')]")
                if recovery_options:
                    driver.execute_script("arguments[0].click();", recovery_options[0])
                    time.sleep(5)
                    try:
                        recovery_input = wait.until(EC.visibility_of_element_located((By.NAME, "knowledgePrereqResponse")))
                        recovery_input.send_keys(RECOVERY_EMAIL)
                        recovery_input.send_keys(Keys.ENTER)
                        time.sleep(10)
                        continue
                    except: pass
            
            if "homeaddress" in current_url:
                try:
                    skip_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Skip' or text()='Lewati']/parent::button")))
                    skip_btn.click()
                    time.sleep(5)
                    continue
                except: pass
            
            time.sleep(3)

        # STEP 4: Final Check
        time.sleep(5)
        current_url = driver.current_url
        success_indicators = ["myaccount.google.com", "mail.google.com", "inbox"]
        
        if any(indicator in current_url for indicator in success_indicators):
            print(f"  SUKSES LOGIN: {email}")
            return True
        else:
            print(f"  Gagal login atau butuh verifikasi manual.")
            return False

    except Exception as e:
        print(f"  Error: {e}")
        return False

# ==========================================
if __name__ == "__main__":
    # Load Credentials
    creds = []
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds = json.load(f)
    elif os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, "r") as f:
            for line in f:
                if line.strip():
                    creds.append({"email": line.strip(), "password": DEFAULT_PASSWORD})

    if not creds:
        print("❌ Tidak ada data email/credentials!")
        sys.exit(1)

    mapping_data = []
    
    for item in creds:
        email = item.get("email")
        password = item.get("password") or DEFAULT_PASSWORD
        
        folder_name = f"profile_{email.split('@')[0]}"
        profile_path = os.path.join(BASE_PROFILE_DIR, folder_name)
        os.makedirs(profile_path, exist_ok=True)
        
        # Add to mapping (format: original_path|name)
        # modul_bot.py expects this format to create local profile symlinks
        mapping_data.append(f"{profile_path}|{folder_name}")
        
        driver = None
        try:
            driver = create_driver(profile_path)
            login_gmail(driver, email, password)
        finally:
            if driver: driver.quit()
            time.sleep(2)

    # Save mapping file for loop.py
    with open(MAPPING_FILE, "w") as f:
        f.write("\n".join(mapping_data) + "\n")
    
    print(f"✅ Selesai. Mapping disimpan di {MAPPING_FILE}")
