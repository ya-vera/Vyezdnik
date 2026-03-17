import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re
import unicodedata
import time
import random
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URLS = [
    {
        "url": "https://www.kdmid.ru/docs/thailand/information-about-the-country",
        "source_name": "МИД РФ — общая информация",
        "country": "thailand"
    },
    {
        "url": "https://tdac.immigration.go.th/manual/en/index.html",
        "source_name": "TDAC manual (обязательный цифровой arrival card)",
        "country": "thailand"
    },
    {
        "url": "https://tdac.immigration.go.th/manual/en/faq.html",
        "source_name": "TDAC FAQ",
        "country": "thailand"
    },
    {
        "url": "https://www.immigration.go.th/en/?p=entry_requirements",
        "source_name": "Immigration Thailand — Entry Requirements",
        "country": "thailand"
    },
    {
        "url": "https://thaiconsulatela.thaiembassy.org/en/publicservice/visa-exemption-and-visa-on-arrival-to-thailand",
        "source_name": "Visa Exemption & VOA — зеркало (актуальный список 93 стран)",
        "country": "thailand"
    },
    {
        "url": "https://www.thaievisa.go.th/",
        "source_name": "Thai e-Visa Official Portal",
        "country": "thailand"
    },
]

OUTPUT_DIR = Path("backend/data/knowledge")
OUTPUT_FILE = OUTPUT_DIR / "thailand_all_sources.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

def fetch_with_requests(url, max_retries=4):
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504, 403],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update(HEADERS)

    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = extract_clean_text(soup)
        if len(text) > 500:
            return text
    except Exception as e:
        print(f"  requests failed: {e}")
    return None

def fetch_with_undetected(url):
    print("   → undetected-chromedriver")
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-agent={HEADERS['User-Agent']}")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.get(url)
        time.sleep(8 + random.uniform(3, 6))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4 + random.uniform(2, 4))

        try:
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "main, article, .content, #content, body > div"))
            )
        except:
            pass

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        text = extract_clean_text(soup)
        if len(text) > 500:
            return text
    except Exception as e:
        print(f"  undetected failed: {e}")
    finally:
        if driver is not None:
            try:
                driver.quit()
            except:
                pass
    return None

def fetch_fallback_selenium(url):
    print("   → fallback selenium + webdriver-manager")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={HEADERS['User-Agent']}")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(1920, 1080)
        driver.get(url)
        time.sleep(10 + random.uniform(3, 6))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)
        html = driver.page_source
        text = extract_clean_text(BeautifulSoup(html, "html.parser"))
        if len(text) > 500:
            return text
    except Exception as e:
        print(f"  fallback failed: {e}")
    finally:
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
    return None

def extract_clean_text(soup):
    unwanted = ["script", "style", "noscript", "iframe", "form", "svg", "meta", "link", "head", "footer", "nav"]
    for tag in unwanted:
        for elem in soup.find_all(tag):
            elem.decompose()

    lines = []
    for tag in soup.find_all(['h1','h2','h3','h4','h5','h6','p','li','td','th','strong','em','div','span','section','article']):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) < 2:
            continue
        if tag.name.startswith('h'):
            lines.append(f"\n{text.upper()}\n{'-' * len(text)}\n")
        elif tag.name == 'li':
            lines.append(f"• {text}")
        else:
            lines.append(text)

    return "\n\n".join(lines)

def fetch_page_text(url):
    for attempt in range(1, 4):
        print(f"  Попытка {attempt}/3...")
        text = fetch_with_requests(url)
        if text:
            return text

        text = fetch_with_undetected(url)
        if text:
            return text

        text = fetch_fallback_selenium(url)
        if text:
            return text

        time.sleep(5 + random.uniform(3, 8))

    return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Правила въезда в Таиланд для граждан РФ (март 2026)\n")
        f.write(f"last_updated: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write("category: въезд, виза, TDAC, безвиз, документы\n\n")

        f.write("АКТУАЛЬНО НА МАРТ 2026:\n")

        for item in URLS:
            url = item["url"]
            source = item["source_name"]
            country = item["country"]

            print(f"\nОбрабатываю: {source}")
            print(url)

            text = fetch_page_text(url)

            if text:
                f.write(f"## Источник: {source}\n")
                f.write(f"source_url: {url}\n")
                f.write(f"country: {country}\n")
                f.write(f"date_fetched: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write(text + "\n\n")
                f.write("═" * 100 + "\n\n")
                print(f"  OK  ({len(text):,} символов)")
            else:
                print("  FAIL")
                f.write(f"## {source} — НЕ УДАЛОСЬ ЗАГРУЗИТЬ (попробовать позже)\n")
                f.write(f"source_url: {url}\n\n")

    print("\nГотово! Файл:", OUTPUT_FILE.absolute())

if __name__ == "__main__":
    main()