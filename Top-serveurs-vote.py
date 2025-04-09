import time
import logging
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from PIL import Image
import google.generativeai as genai

# Configuration du logging
logging.basicConfig(level=logging.INFO)

# Clé API Gemini + modèle à jour
GEMINI_API_KEY = "AIzaSyDVfIrN6wSf6KBofx9V1my9hX5q90ST9tw"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

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
async def send_image_to_gemini_api(image_path, prompt="Lis ce captcha :"):
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        response = model.generate_content([{"mime_type": "image/png", "data": image_data}, {"text": prompt}])
        response.resolve()
        return response.text.strip()
    except Exception as e:
        logging.error(f"Erreur Gemini : {e}")
        return None

# Fonction principale
async def vote_and_generate():
    driver = setup_driver()
    try:
        logging.info("Ouverture de la page...")
        driver.get("https://top-serveurs.net/rdr/vote/sunny-western")
        logging.info("Page chargée.")

        # Accepter les cookies
        accept_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'Autoriser')]"))
        )
        accept_btn.click()

        # Entrer le pseudo
        pseudo_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "playername"))
        )
        pseudo_input.send_keys("Tekashi Nomura")
        logging.info("Pseudo inséré.")

        # Pause pour que le captcha s'affiche
        time.sleep(3)

        # Capturer l'écran du captcha
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"C:/Users/Meddy/OneDrive/Images/Screenshots/captcha_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Capture écran enregistrée : {screenshot_path}")

        # Recadrer l'image du captcha
        captcha_box = (1008, 780, 1450, 925)  # Ajuste si nécessaire
        cropped_path = crop_captcha_image(screenshot_path, captcha_box)

        # Résoudre le captcha avec Gemini
        captcha_solution = await send_image_to_gemini_api(cropped_path)
        if captcha_solution:
            logging.info(f"Solution captchée : {captcha_solution}")

            # Trouver et cliquer sur le champ du captcha pour simuler un clic
            captcha_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "mtcap-inputtext-1"))
            )
            captcha_input.click()  # Simule un clic sur le champ
            captcha_input.clear()  # Nettoyer le champ
            captcha_input.send_keys(captcha_solution)  # Entrer la solution du captcha
            logging.info("Solution captcha entrée dans le champ.")

            # Optionnel : Clique sur le bouton de vote
            vote_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Voter')]"))
            )
            vote_btn.click()  # Clic sur le bouton de vote
            logging.info("Vote effectué.")

        else:
            logging.warning("Pas de solution détectée.")

    except Exception as e:
        logging.error(f"Erreur du script : {e}")
    finally:
        driver.quit()
        logging.info("Navi fermé. Script terminé.")

# Lancer le script
if __name__ == "__main__":
    asyncio.run(vote_and_generate())
