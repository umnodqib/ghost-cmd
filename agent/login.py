import os
import time
import subprocess
import sys
import pyautogui 
import mss

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.3

PASSWORD = "Bismillah12345!"      
PROFILE_PREFIX = "dotaja"     
START_INDEX = 1               

CHROME_PATH = "/usr/bin/google-chrome" 
BASE_PROFILE_DIR = "/root/chrome_profiles"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
EMAIL_FILE = os.path.join(BASE_PATH, "email.txt")

def kill_chrome():
    os.system("pkill -9 -f chrome > /dev/null 2>&1")
    time.sleep(2)

with open(EMAIL_FILE, "r") as f:
    EMAILS = [line.strip() for line in f if line.strip()]

for i, EMAIL in enumerate(EMAILS, start=START_INDEX):
    folder_name = f"{PROFILE_PREFIX}{i:02d}"
    full_profile_path = os.path.join(BASE_PROFILE_DIR, folder_name)
    os.makedirs(full_profile_path, exist_ok=True)

    print(f"🚀 Login {EMAIL} → {folder_name}")

    cmd = [
        CHROME_PATH,
        "--disable-gpu",
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={full_profile_path}",
        "https://accounts.google.com/signin"
    ]
    
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("  ⏳ Chrome loading... (35s)")
    time.sleep(35)

    try:
        # ===== INPUT EMAIL =====
        print(f"  → Typing email: {EMAIL}")
        pyautogui.write(EMAIL, interval=0.05)
        time.sleep(1)
        pyautogui.press('enter')
        print("  ⏳ Waiting for password field... (25s)")
        time.sleep(25)

        # ===== INPUT PASSWORD =====
        print(f"  → Typing password")
        pyautogui.write(PASSWORD, interval=0.05)
        time.sleep(1)
        pyautogui.press('enter')
        print("  ⏳ Waiting for login complete... (35s)")
        time.sleep(35)

        # ===== SCREENSHOT BUKTI =====
        ss_path = os.path.join(BASE_PATH, f"bukti_{folder_name}.png")
        with mss.mss() as sct:
            sct.shot(mon=-1, output=ss_path)
        print(f"✅ Login berhasil: {ss_path}\n")

    except Exception as e:
        print(f"❌ Error {EMAIL}: {e}\n")

    kill_chrome()
    time.sleep(5)

print("✅ Selesai.")
