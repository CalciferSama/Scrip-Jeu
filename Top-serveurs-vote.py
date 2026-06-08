from playwright.sync_api import sync_playwright
from PIL import Image
from twocaptcha import TwoCaptcha

solver = TwoCaptcha("44c74eeb169fec0ab00daf093022b8e5")

PSEUDOS = [
    "Lucius Shelby/",
]

def lire_captcha(path):
    result = solver.normal(path)
    return result["code"]

total_bytes = 0

with sync_playwright() as p:
    for i, pseudo in enumerate(PSEUDOS):
        print(f"\n--- Vote avec : {pseudo} ---")
        browser = p.chromium.launch(
            channel="msedge",
            headless=False,
        )
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
                page.wait_for_timeout(300)
                break
            except:
                pass

        # Attendre que mtcaptcha charge
        page.wait_for_timeout(6000)

        # Trouver le frame mtcaptcha
        mtcaptcha_frame = None
        for frame in page.frames:
            if "mtcaptcha" in frame.url:
                mtcaptcha_frame = frame
                break

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

        # Remplir le pseudo
        page.get_by_placeholder("Pseudo (optionnel)").fill(pseudo)

        # Remplir le captcha
        if mtcaptcha_frame:
            try:
                captcha_input = mtcaptcha_frame.locator("input[type='text'], input[id*='inputfield'], input[class*='inputfield']").first
                captcha_input.press_sequentially(reponse_ia, delay=150)
            except Exception as e:
                print("Erreur captcha :", e)

        # Voter
        page.wait_for_timeout(1000)
        page.locator("span.btn-content:has-text('Voter')").click()
        print("Vote envoyé !")

        page.wait_for_timeout(30000)
        browser.close()

        total_bytes += vote_bytes[0]
        print(f"Data ce vote   : {vote_bytes[0] / 1024 / 1024:.3f} MB")
        print(f"Total cumulé   : {total_bytes / 1024 / 1024:.3f} MB ({total_bytes / 1024 / 1024 / 1024:.5f} GB)")

input("Appuie sur Entrée pour fermer...")
