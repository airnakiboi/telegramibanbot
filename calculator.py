import time
import logging
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from webdriver_manager.chrome import ChromeDriverManager

# Logger ayarı
logging.basicConfig(level=logging.INFO)

# Telegram Bot Token
TOKEN = "7885842081:AAHvjOV9QgWxQL1u20MbPdUwDWKt5ZpziBo"
SITE_URL = "https://www.ibancalculator.com/bic_und_iban.html"  # IBAN hesaplama sitesi

# Selenium WebDriver Ayarları
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Tarayıcıyı tam ekran aç
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")  # Bot tespiti önleme
options.page_load_strategy = "eager"  # Sayfanın hızlı yüklenmesi için


def get_iban(user_number: str) -> str:
    logging.info("Tarayıcı başlatılıyor...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    logging.info("Tarayıcı açıldı, siteye gidiliyor...")
    driver.get(SITE_URL)

    driver.implicitly_wait(2)  # Bekleme sürelerini minimize ettik

    if "IBAN" not in driver.page_source:
        logging.error("Sayfa yüklenemedi veya yanlış URL!")
        driver.quit()
        return "IBAN hesaplama sitesi açılmadı, lütfen tekrar deneyin!"

    try:
        logging.info("Ülke seçimi yapılıyor...")
        country_select = Select(driver.find_element(By.NAME, "tx_intiban_pi1[country]"))
        country_select.select_by_value("TR")

        logging.info("Banka kodu giriliyor...")
        bank_code = driver.find_element(By.NAME, "tx_intiban_pi1[blz]")
        bank_code.clear()
        bank_code.send_keys("00829")

        logging.info("Hesap numarası giriliyor...")
        account_number = driver.find_element(By.NAME, "tx_intiban_pi1[kontonr]")
        full_account = "000949" + str(user_number)
        account_number.clear()
        account_number.send_keys(full_account)

        logging.info("Hesaplama butonuna basılıyor...")
        calculate_button = driver.find_element(By.NAME, "tx_intiban_pi1[a]")
        driver.execute_script("arguments[0].click();", calculate_button)

        logging.info("IBAN sonucu alınıyor...")
        driver.implicitly_wait(2)  # IBAN yüklenmesini beklemeden hızlı erişim sağladık
        iban_element = driver.find_element(By.XPATH, "//fieldset//span[contains(text(), 'IBAN:')]")
        iban = iban_element.text.replace("IBAN: ", "")
    except Exception as e:
        logging.error(f"Hata oluştu: {e}")
        iban = f"IBAN alınamadı: {str(e)}"
    finally:
        driver.quit()

    return iban


# Telegram Mesaj Alma ve Yanıt Gönderme

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.strip()
    if not user_input.isdigit():
        await update.message.reply_text("Lütfen geçerli bir hesap numarası girin!")
        return

    logging.info(f"Kullanıcıdan gelen numara: {user_input}")
    iban = get_iban(user_input)
    await update.message.reply_text(f"İşlem Tamamlandı!\nIBAN: {iban}")


def main() -> None:
    logging.info("Telegram bot başlatılıyor...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
