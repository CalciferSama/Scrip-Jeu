import time
import logging
import asyncio
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from PIL import Image
import pyautogui
import google.generativeai as genai
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO)

# Clé API Gemini + modèle à jour
GEMINI_API_KEY = "AIzaSyDVfIrN6wSf6KBofx9V1my9hX5q90ST9tw"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Webhook Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1358636041270989041/TujDmyYjkPznIch9iZZwaJd09kp-5KoSRPcDC2SUgb7Qy8T7JP_82jLe4fVMncC3wptH"

# Fonction d'envoi de message à Discord
def notify_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi Discord : {e}")

# Lancer Edge + Selenium
def setup_driver():
    options = Options()
    options.headless = False
    edge_driver_path = "C:/Users/Meddy/OneDrive - student.helmo.be/Bureau/msedgedriver.exe"
    service = Service(edge_driver_path)
    driver = webdriver.Edge(service=service, options=options)
    driver.set_window_size(1920, 1080)
    return driver

# Recadrer le captcha
def crop_captcha_image(screenshot_path, crop_box):
    with Image.open(screenshot_path) as img:
        logging.info(f"Taille image avant recadrage : {img.size}")
        cropped_img = img.crop(crop_box)
        cropped_screenshot_path = screenshot_path.replace(".png", "_cropped.png")
        cropped_img.save(cropped_screenshot_path)
        logging.info(f"Image recadrée enregistrée : {cropped_screenshot_path}")
        return cropped_screenshot_path

# Envoyer à Gemini pour lire le texte
async def send_image_to_gemini_api(image_path, prompt="Lis uniquement le texte du captcha, sans explication :"):
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        response = model.generate_content([{"mime_type": "image/png", "data": image_data}, {"text": prompt}])
        response.resolve()
        return response.text.strip()
    except Exception as e:
        logging.error(f"Erreur Gemini : {e}")
        return None

# Filtrer le texte captcha
def filter_captcha_solution(solution):
    match = re.search(r'\b[A-Z0-9]{5,}\b', solution)
    if match:
        return match.group(0)
    return solution.strip()

# Fonction principale
async def vote_and_generate():
    driver = setup_driver()
    try:
        notify_discord("🔄 Début du processus de vote automatique...")
        driver.get("https://top-serveurs.net/rdr/vote/sunny-western")
        notify_discord("🌐 Page de vote chargée.")

        accept_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'Autoriser')]"))
        )
        accept_btn.click()

        pseudo_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "playername"))
        )
        pseudo_input.send_keys("Tekashi Nomura")
        notify_discord("📝 Pseudo inséré : Tekashi Nomura")

        time.sleep(3)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"C:/Users/Meddy/OneDrive/Images/Screenshots/captcha_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        notify_discord("📸 Screenshot du captcha capturé.")

        captcha_box = (1008, 780, 1450, 925)  # À ajuster si besoin
        cropped_path = crop_captcha_image(screenshot_path, captcha_box)
        notify_discord("✂️ Image captcha recadrée, envoi à Gemini...")

        captcha_solution = await send_image_to_gemini_api(cropped_path)
        if captcha_solution:
            captcha_solution = filter_captcha_solution(captcha_solution)
            logging.info(f"Solution captchée : {captcha_solution}")
            notify_discord(f"✅ Solution captcha trouvée : `{captcha_solution}`")

            time.sleep(2)
            pyautogui.press("tab", presses=4, interval=0.2)
            pyautogui.write(captcha_solution, interval=0.05)
            time.sleep(3)
            pyautogui.press("tab", presses=2, interval=0.2)
            pyautogui.press("enter")
            notify_discord("📤 Vote soumis avec succès !")

        else:
            notify_discord("⚠️ Aucune solution détectée par Gemini !")

    except Exception as e:
        logging.error(f"Erreur du script : {e}")
        notify_discord(f"❌ Erreur dans le script : {e}")
    finally:
        time.sleep(15)
        driver.quit()
        notify_discord("🛑 Navigateur fermé. Script terminé.")

# Boucle d'exécution
if __name__ == "__main__":
    while True:
        logging.info("Début de l'exécution du script...")
        notify_discord("🕒 Lancement d'un nouveau vote automatique.")
        asyncio.run(vote_and_generate())
        notify_discord("⏳ Prochain vote dans 2 heures et 1 minute...")
        time.sleep(2 * 3600 + 60)
