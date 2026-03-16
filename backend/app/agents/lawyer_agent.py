from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="mistral-large-latest",
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1",
    temperature=0.0,
)


embedder = SentenceTransformer("intfloat/multilingual-e5-large")

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333")
)
COLLECTION_NAME = "thailand_rules"

LAWYER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Ты — строгий справочный консультант по актуальным правилам въезда в Таиланд для граждан РФ.
    Отвечай ТОЛЬКО фактами из предоставленного контекста (retrieved chunks). Ничего не придумывай.
    Не добавляй информацию, которой нет в контексте.

    Контекст может содержать **английские и русские фрагменты** — сохраняй оригинальные термины (TDAC, visa exemption, passport validity и т.п.) и объясняй их на русском, если это нужно для ясности.
    Отвечай исключительно на русском языке, кратко, структурировано и по делу.
    Используй markdown: заголовки, списки, жирный текст для ключевых фактов.

    Основные темы, которые могут быть в вопросе:
    - безвизовый режим / виза (срок пребывания, продление)
    - TDAC (цифровая карта прибытия) — если упоминается в контексте
    - документы (паспорт, для детей, страховка и т.д.)
    - таможня, здоровье, транзит и т.п.

    Включай только то, что релевантно вопросу.
    В конце всегда добавляй дисклеймер:
    **Важно:** Эта информация справочная и может устареть. Проверяйте на официальных сайтах и в консульстве. Окончательное решение принимает пограничная служба.

    Источники указывай в конце, если они есть в контексте."""),
    ("human", "Контекст из базы знаний:\n{context}\n\nВопрос пользователя: {question}"),
])

chain = LAWYER_PROMPT | llm | StrOutputParser()


def lawyer_agent(question: str, country: str = "thailand", min_score: float = 0.75, limit: int = 6):
    query_vector = embedder.encode(question).tolist()

    hits = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
        query_filter=Filter(  
            must=[FieldCondition(key="country", match=MatchValue(value=country))]
        )
    )

    relevant_chunks = []
    sources = set()
    for point in hits.points:
        if point.score >= min_score:
            payload = point.payload
            relevant_chunks.append(payload.get("text", ""))
            sources.add(payload.get("source_url", "—"))

    if not relevant_chunks:
        return "Не удалось найти точную информацию в базе. Рекомендую проверить самостоятельно на официальных сайтах."

    context = "\n\n".join(relevant_chunks)

    response = chain.invoke({
        "context": context,
        "question": question
    })

    sources_str = "\n**Источники:**\n" + "\n".join([f"- [{s}]({s})" for s in sources if s != "—"])
    final = response + sources_str

    return final