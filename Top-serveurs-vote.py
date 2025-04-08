 
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import google.generativeai as genai
import requests  # Still needed for Discord webhook
# Variables
GEMINI_API_KEY = "AIzaSyDVfIrN6wSf6KBofx9V1my9hX5q90ST9tw"  # Replace with your actual Gemini API key
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1358636041270989041/TujDmyYjkPznIch9iZZwaJd09kp-5KoSRPcDC2SUgb7Qy8T7JP_82jLe4fVMncC3wptH"  # Replace with your Discord webhook URL
# Configure the Gemini API with your API key
genai.configure(api_key=GEMINI_API_KEY)
# Select the Gemini Pro Vision model (for multimodal input)
model = genai.GenerativeModel('gemini-pro-vision')
# Fonction pour envoyer l'image à l'API Gemini pour analyse
async def send_image_to_gemini_api(image_path, prompt="Describe the text in this image."):
    """Sends a local image to the Gemini API for analysis.
    Args:
        image_path (str): The path to the local image file.
        prompt (str, optional): An optional text prompt to accompany the image.
                                Defaults to "Describe the text in this image.".
    Returns:
        str: The text response from the Gemini API, or None if an error occurs.
    """
    if not os.path.exists(image_path):
        logging.error(f"Image file not found at {image_path}")
        return None
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        contents = [
            {
                "parts": [
                    {"mime_type": "image/*", "data": image_data},  # Gemini can infer the type
                    {"text": prompt},
                ]
            }
        ]
        response = model.generate_content(contents)
        response.resolve()  # Ensure the response is fully processed
        return response.text
    except Exception as e:
        logging.error(f"Error sending image to Gemini API: {e}")
        return None
# Fonction pour envoyer un message sur Discord
def send_to_discord(message):
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to Discord: {e}")
# Fonction pour configurer et lancer le navigateur Firefox
def setup_driver():
    options = Options()
    options.headless = False  # Ne pas utiliser le mode headless pour voir l'interface
    options.add_argument("--start-fullscreen")  # Ouvrir en plein écran
    driver_path = GeckoDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=options)
    return driver
# Fonction principale pour voter et analyser l'image du captcha
def vote_and_generate():
    # Lancer le navigateur
    driver = setup_driver()
    try:
        # Ouvrir la page de vote
        driver.get("https://top-serveurs.net/rdr/vote/sunny-western")
        logging.info("Page ouverte avec succès.")
        # Accepter les cookies
        accept_cookies_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'Autoriser')]"))
        )
        accept_cookies_button.click()
        logging.info("Cookies acceptés.")
        # Insérer le pseudo
        pseudo_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "playername"))
        )
        pseudo_input.send_keys("Tekashi Nomura")
        logging.info("Pseudo 'Tekashi Nomura' inséré.")
        # Prendre la capture d'écran
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"C:/Users/Meddy/OneDrive/Images/Screenshots/captcha_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Capture d'écran enregistrée : {screenshot_path}")
        # Envoyer l'image à l'API Gemini pour analyse
        gemini_response_text = send_image_to_gemini_api(screenshot_path, prompt="What text do you see in this image? If there is no text, say 'No text detected'.")
        if gemini_response_text:
            logging.info(f"Texte détecté par Gemini : {gemini_response_text}")
            # Envoi du texte du captcha sur Discord
            send_to_discord(f"Texte du captcha (Gemini): {gemini_response_text}")
        else:
            logging.warning("Aucun texte détecté par Gemini ou erreur lors de l'analyse.")
            send_to_discord("Erreur lors de l'analyse du captcha par Gemini.")
    except Exception as e:
        logging.error(f"Une erreur est survenue : {e}")
        send_to_discord(f"Erreur : {e}")
    finally:
        # Fermeture du navigateur
        driver.quit()
        logging.info("Script terminé et navigateur fermé.")
# Fonction pour configurer les logs
def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
if __name__ == "__main__":
    setup_logging()
    vote_and_generate()
