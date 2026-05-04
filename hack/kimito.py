import sys
import time
import threading
import cv2
import numpy as np
from mss import mss
import pyautogui
import keyboard
from datetime import datetime, timedelta

# ---------------------------------------------
# CREDENTIALS / AD LOCK (fake but keeps it free)
# ---------------------------------------------
LAST_AD_TIME = None
AD_COOLDOWN = timedelta(hours=24)

def show_ad():
    print("[Zenith] Peep this 30‑sec ad to activate the sauce (simulated).")
    for i in range(30, 0, -1):
        print(f"[Ad] {i}s left...", end='\r')
        time.sleep(1)
    print("\n[Zenith] Ad done. You good to slay, fam!                ")
    global LAST_AD_TIME
    LAST_AD_TIME = datetime.now()

def check_ad():
    global LAST_AD_TIME
    if LAST_AD_TIME is None or datetime.now() - LAST_AD_TIME > AD_COOLDOWN:
        show_ad()

# -------
# SCREEN
# -------
SCREEN_REGION = {"top": 40, "left": 0, "width": 720, "height": 1280}  # BlueStacks full window
monitor = {"top": SCREEN_REGION["top"], "left": SCREEN_REGION["left"],
           "width": SCREEN_REGION["width"], "height": SCREEN_REGION["height"]}
sct = mss()

def grab_frame():
    img = sct.grab(monitor)
    return np.array(img)[:,:,:3]  # BGR

# ---------------
# SIMPLE DETECT
# ---------------
# We'll look for red enemy outlines (common in Brawl) and projectile indicators
lower_red = np.array([0, 0, 100])
upper_red = np.array([80, 80, 255])

lower_projectile = np.array([200, 200, 200])  # white/grey trail
upper_projectile = np.array([255, 255, 255])

def find_enemies(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_red, upper_red)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    enemies = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 30:  # ignore tiny noise
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                enemies.append((cx, cy))
    return enemies

def find_projectiles(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    projectiles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 10 < area < 150:  # approximate size of bullet/gem
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                projectiles.append((cx, cy))
    return projectiles

def aim_at(target_x, target_y):
    # Assume your brawler is near center-bottom of screen
    center_x = monitor["width"] // 2
    center_y = int(monitor["height"] * 0.8)
    # Move mouse to aim (you can adjust sensitivity)
    dx = target_x - center_x
    dy = target_y - center_y
    pyautogui.moveRel(dx * 0.4, dy * 0.4, duration=0.05)  # smooth mouse movement
    pyautogui.click()  # shoot (you can hold for auto‑fire if needed)

def dodge(projectile_list):
    # If any projectile is getting close to our character area, swipe in opposite direction
    danger_zone_top = monitor["height"] * 0.6
    danger_zone_bottom = monitor["height"] * 0.95
    danger_left = monitor["width"] * 0.2
    danger_right = monitor["width"] * 0.8
    for px, py in projectile_list:
        if danger_left < px < danger_right and danger_zone_top < py < danger_zone_bottom:
            # Dodge left or right depending on projectile position
            if px < monitor["width"] // 2:
                # swipe right
                pyautogui.moveTo(300, 1000)
                pyautogui.drag(200, 0, duration=0.1)
            else:
                # swipe left
                pyautogui.moveTo(450, 1000)
                pyautogui.drag(-200, 0, duration=0.1)
            break

# --------------
# MAIN LOOPS
# --------------
running = False

def aimbot_loop():
    while running:
        frame = grab_frame()
        enemies = find_enemies(frame)
        if enemies:
            # target closest enemy (just for demo, you can make it smarter)
            target = min(enemies, key=lambda e: e[1])  # highest y is more forward
            aim_at(target[0], target[1])
        time.sleep(0.05)

def dodge_loop():
    while running:
        frame = grab_frame()
        projectiles = find_projectiles(frame)
        if projectiles:
            dodge(projectiles)
        time.sleep(0.03)

def toggle_hack():
    global running
    running = not running
    state = "ON" if running else "OFF"
    print(f"[Zenith] Aimbot + Auto‑Dodge {state} fam!")

# ------
# START
# ------
if __name__ == "__main__":
    print("Credit: Zenith.gg – TWAI Fam forever.")
    check_ad()
    print("[Zenith] Ready! Press F6 to toggle the hack ON/OFF. Press F7 to quit.")
    keyboard.add_hotkey('F6', toggle_hack)
    keyboard.add_hotkey('F7', lambda: sys.exit(0))
    # threading for both functions
    aim_thread = threading.Thread(target=aimbot_loop, daemon=True)
    dodge_thread = threading.Thread(target=dodge_loop, daemon=True)
    aim_thread.start()
    dodge_thread.start()
    keyboard.wait()
