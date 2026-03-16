import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re
import unicodedata

URLS = [

    {
        "url": "https://www.kdmid.ru/docs/thailand/information-about-the-country",
        "source_name": "МИД РФ — общая информация",
        "country": "thailand"
    },

    {
        "url": "https://www.kdmid.ru/docs/thailand/entry-conditions",
        "source_name": "МИД РФ — условия въезда",
        "country": "thailand"
    },

    {
        "url": "https://www.immigration.go.th/en/",
        "source_name": "Immigration Thailand",
        "country": "thailand"
    },

    {
        "url": "https://www.thaievisa.go.th/",
        "source_name": "Thai eVisa",
        "country": "thailand"
    },

    {
        "url": "https://tdac.immigration.go.th/",
        "source_name": "TDAC",
        "country": "thailand"
    },

    {
        "url": "https://tdac.immigration.go.th/manual/en/index.html",
        "source_name": "TDAC manual",
        "country": "thailand"
    },

    {
        "url": "https://moscow.thaiembassy.org/en",
        "source_name": "Thai embassy Moscow",
        "country": "thailand"
    },

]

OUTPUT_DIR = Path("backend/data/knowledge")
OUTPUT_FILE = OUTPUT_DIR / "thailand_all_sources.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text.lower())
    return re.sub(r'[-\s]+', '-', text).strip('-_')

def fetch_page_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        for elem in soup(["script", "style", "header", "footer", "nav", "aside", 
                          "form", "iframe", "noscript", "meta", "link", "svg", "img"]):
            elem.decompose()
        
        main_content = (
            soup.find("main") or 
            soup.find("article") or 
            soup.find("div", class_="content") or 
            soup.find("div", id="content") or 
            soup.body
        )
        
        if not main_content:
            print(f"Не найден основной контент для {url}")
            return None
        
        text = main_content.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    
    except Exception as e:
        print(f"Ошибка при обработке {url}: {e}")
        return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Все правила въезда в Таиланд для граждан РФ (собранные источники)\n")
        f.write(f"last_updated: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"category: въезд, виза, TDAC, документы, дети\n")
   
        for item in URLS:
            url = item["url"]
            source_name = item["source_name"]
            country = item["country"]
            
            print(f"Обрабатываю: {source_name} ({url})")
            
            page_text = fetch_page_text(url)
            if page_text:
                f.write(f"## Источник: {source_name}\n")
                f.write(f"source_url: {url}\n")
                f.write(f"country: {country}\n")
                f.write(f"date_fetched: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write(page_text)
                f.write("\n\n" + "="*80 + "\n\n")
                print(f"  Добавлено ({len(page_text)} символов)")
            else:
                print(f"  Пропущено (ошибка): {source_name} ({url})")
    
    print(f"\nГотово! Всё сохранено в один файл: {OUTPUT_FILE}")
    print(f"Размер: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()