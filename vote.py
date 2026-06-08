import time
import requests
from playwright.sync_api import sync_playwright
from PIL import Image
from twocaptcha import TwoCaptcha

solver = TwoCaptcha("44c74eeb169fec0ab00daf093022b8e5")

PSEUDOS = [
    "Lucius Shelby/",
]

WEBHOOK_URL = "https://discord.com/api/webhooks/1513315343890649118/_EwOQMlpDdAoA9P2gc5L7BQhZh6mzMUuL_ym42Np1MkH5ik5K5QUnZiZ___DUksRdoB4"

def envoyer_webhook(message):
    requests.post(WEBHOOK_URL, json={"content": message})

def lire_captcha(path):
    result = solver.normal(path)
    return result["code"]

total_bytes = 0

DELAI_ENTRE_VOTES = 2 * 3600 + 5 * 60  # 2h05

with sync_playwright() as p:
  while True:
    for i, pseudo in enumerate(PSEUDOS):
        msg = f"\n--- Vote avec : {pseudo} ---"
        print(msg)
        envoyer_webhook(f"🗳️ **Début du vote**\n👤 Pseudo : `{pseudo}`")

        browser = p.firefox.launch()
        page = browser.new_page()

        # Tracker de consommation data
        vote_bytes = [0]
        def on_response(response, vb=vote_bytes):
            try:
                cl = response.headers.get("content-length")
                vb[0] += int(cl) if cl else len(response.body())
            except:
                pass
        page.on("response", on_response)

        page.goto("https://top-serveurs.net/rdr/vote/sunny-western")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Accepter les cookies
        cookies_acceptes = False
        for selector in [
            "p.fc-button-label:has-text('Autoriser')",
            "button:has-text('Autoriser')",
            "button:has-text('Accepter')",
            "button:has-text('Tout accepter')",
            "#didomi-notice-agree-button",
            ".cc-accept",
        ]:
            try:
                page.click(selector, timeout=2000)
                print("Cookies acceptés")
                envoyer_webhook("🍪 Cookies acceptés")
                page.wait_for_timeout(300)
                cookies_acceptes = True
                break
            except:
                pass

        if not cookies_acceptes:
            print("Pas de bannière cookies")
            envoyer_webhook("ℹ️ Pas de bannière cookies")

        # Attendre que mtcaptcha charge
        page.wait_for_timeout(6000)

        # Trouver le frame mtcaptcha
        mtcaptcha_frame = None
        for frame in page.frames:
            if "mtcaptcha" in frame.url:
                mtcaptcha_frame = frame
                break

        if mtcaptcha_frame:
            print("Frame mtcaptcha trouvé")
            envoyer_webhook("🔍 Frame mtcaptcha trouvé")
        else:
            print("Frame mtcaptcha introuvable")
            envoyer_webhook("⚠️ Frame mtcaptcha introuvable")

        # Scroller jusqu'au captcha puis screenshot
        try:
            page.locator("[id*='mtcaptcha'], .mtcaptcha, [class*='mtcaptcha']").first.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
        except:
            pass
        page.screenshot(path="capture_full.png")
        try:
            box = page.locator("[id*='mtcaptcha'], .mtcaptcha, [class*='mtcaptcha']").first.bounding_box()
            if box:
                full = Image.open("capture_full.png")
                cropped = full.crop((box['x'], box['y'], box['x'] + box['width'], box['y'] + box['height']))
                cropped.save("capture.png")
            else:
                Image.open("capture_full.png").save("capture.png")
        except:
            Image.open("capture_full.png").save("capture.png")

        reponse_ia = lire_captcha("capture.png")
        print("Captcha :", reponse_ia)
        envoyer_webhook(f"🧩 Captcha résolu : `{reponse_ia}`")

        # Remplir le pseudo
        page.get_by_placeholder("Pseudo (optionnel)").fill(pseudo)
        print("Pseudo rempli")
        envoyer_webhook(f"✍️ Pseudo rempli : `{pseudo}`")

        # Remplir le captcha
        if mtcaptcha_frame:
            try:
                captcha_input = mtcaptcha_frame.locator("input[type='text'], input[id*='inputfield'], input[class*='inputfield']").first
                captcha_input.press_sequentially(reponse_ia, delay=150)
                print("Captcha saisi")
                envoyer_webhook("⌨️ Captcha saisi dans le champ")
            except Exception as e:
                print("Erreur captcha :", e)
                envoyer_webhook(f"❌ Erreur captcha : `{e}`")

        # Voter
        page.wait_for_timeout(1000)
        page.locator("span.btn-content:has-text('Voter')").click()
        print("Vote envoyé !")

        page.wait_for_timeout(30000)
        browser.close()

        total_bytes += vote_bytes[0]
        mb_vote = vote_bytes[0] / 1024 / 1024
        mb_total = total_bytes / 1024 / 1024
        gb_total = total_bytes / 1024 / 1024 / 1024

        print(f"Data ce vote   : {mb_vote:.3f} MB")
        print(f"Total cumulé   : {mb_total:.3f} MB ({gb_total:.5f} GB)")

        message = (
            f"✅ **Vote envoyé !**\n"
            f"👤 Pseudo : `{pseudo}`\n"
            f"🧩 Captcha : `{reponse_ia}`\n"
            f"📶 Data ce vote : `{mb_vote:.3f} MB`\n"
            f"📊 Total cumulé : `{mb_total:.3f} MB ({gb_total:.5f} GB)`"
        )
        envoyer_webhook(message)

    print(f"\nProchain vote dans 2h05 ({DELAI_ENTRE_VOTES} s)...")
    envoyer_webhook(f"⏳ Prochain vote dans 2h05...")
    time.sleep(DELAI_ENTRE_VOTES)
