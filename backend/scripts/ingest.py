import os
import re
from pathlib import Path
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import uuid
import time


QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "thailand_rules"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"  # 1024 dim

INPUT_FILE = Path(r"backend\data\knowledge\thailand_all_sources.md")
CHUNK_SIZE = 960
CHUNK_OVERLAP = 160

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def create_collection_if_not_exists():
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Удалена старая коллекция: {COLLECTION_NAME}")
        time.sleep(1.5)
    except Exception as e:
        print(f"Коллекция не найдена или ошибка удаления (нормально): {e}")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )
    print(f"Создана новая коллекция: {COLLECTION_NAME}")


def split_by_sources(md_path: Path):
    if not md_path.exists():
        raise FileNotFoundError(f"Файл не найден: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    first_real_source_pos = content.find('## Источник:')
    if first_real_source_pos != -1:
        content = content[first_real_source_pos:]

    sections = re.split(r'(?=^## Источник:)', content, flags=re.MULTILINE)

    all_chunks = []
    current_meta = {}

    for section in sections:
        section = section.strip()
        if not section:
            continue

        header_match = re.match(
            r'^## Источник:\s*(.+?)\n'
            r'source_url:\s*(.+?)\n'
            r'(?:country:\s*(.+?)\n)?'
            r'(?:date_fetched:\s*(.+?)\n)?',
            section,
            flags=re.MULTILINE
        )

        if header_match:
            source_name = header_match.group(1).strip()
            source_url = header_match.group(2).strip()

            current_meta = {
                "source_name": source_name,
                "source_url": source_url,
                "country": header_match.group(3).strip() if header_match.group(3) else "thailand",
                "date_fetched": header_match.group(4).strip() if header_match.group(4) else datetime.now().strftime("%Y-%m-%d"),
            }

            text_part = re.sub(
                r'^## Источник:.*?\nsource_url:.*?(?:\ncountry:.*?\n)?(?:date_fetched:.*?\n)?\n*',
                '',
                section,
                flags=re.DOTALL | re.MULTILINE
            ).strip()
        else:
            text_part = section

        if not text_part:
            continue

        start = 0
        while start < len(text_part):
            end = min(start + CHUNK_SIZE, len(text_part))
            chunk_text = text_part[start:end].strip()

            if not chunk_text:
                start += CHUNK_SIZE - CHUNK_OVERLAP
                continue

            chunk_item = {
                "text": chunk_text,
                "metadata": current_meta.copy()
            }

            source_url = current_meta.get("source_url", "").strip()
            source_name = current_meta.get("source_name", "").strip()

            if not source_url or not source_name:
                print(f"Пропущен чанк без источника: {chunk_text[:100]}...")
                start += CHUNK_SIZE - CHUNK_OVERLAP
                continue

            all_chunks.append(chunk_item)

            start += CHUNK_SIZE - CHUNK_OVERLAP

    print(f"Всего валидных чанков после фильтра: {len(all_chunks)}")
    return all_chunks


def embed_and_upload(chunks_with_meta, embedder):
    points = []

    for item in chunks_with_meta:
        vector = embedder.encode(item["text"]).tolist()
        payload = {
            "text": item["text"],
            **item["metadata"]
        }

        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload
        ))

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"[{datetime.now()}] Загружено в Qdrant: {len(points)} чанков")


def main():
    print(f"[{datetime.now()}] Обработка файла: {INPUT_FILE}")

    create_collection_if_not_exists()

    chunks_with_meta = split_by_sources(INPUT_FILE)
    print(f"[{datetime.now()}] Получено {len(chunks_with_meta)} чанков с метаданными")

    if not chunks_with_meta:
        print("Не удалось извлечь чанки — проверьте формат markdown")
        return

    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embed_and_upload(chunks_with_meta, embedder)
    print(f"[{datetime.now()}] Работа завершена!")


if __name__ == "__main__":
    main()