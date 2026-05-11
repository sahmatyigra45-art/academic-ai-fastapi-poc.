import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

# --- 1. НАСТРОЙКА ПРОЕКТА ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("AcademicPlatform_PoC")

app = FastAPI(
    title="Academic AI Platform (PoC)",
    description="Микросервисы для анализа статей (LLM) и генерации брифов (RAG). Реализация M1-M4.",
    version="1.1.0"
)

# --- 2. СХЕМЫ ДАННЫХ (PYDANTIC) ---
class ArticleRequest(BaseModel):
    title: str = Field(..., example="Machine Learning in Medical Diagnostics")
    abstract: str = Field(..., description="Анотация статьи для анализа")
    author_email: str = Field(..., example="author@science.org")

class ScoringResult(BaseModel):
    total_score: int
    ai_feedback: str

class BriefRequest(BaseModel):
    journal_url: str = Field(..., example="https://nature.com/ai-med")
    target_topic: str = Field(..., example="Neural networks in oncology")

class BriefResponse(BaseModel):
    brief_content: str
    sources_used: list[str]

# --- 3. MOCK-СЕРВИСЫ: LLM & RAG (M2, M3, M4) ---
async def fetch_from_pgvector(topic: str) -> str:
    """Имитация RAG: поиск релевантного контекста в векторной БД (pgvector)"""
    logger.info(f"[RAG] Поиск эмбеддингов для темы: {topic}")
    await asyncio.sleep(0.5) # Имитация запроса к БД
    return "Journal requirements: APA format, double-blind peer review, focus on practical AI application."

async def call_llm_api(prompt: str, context: str = "") -> str:
    """Имитация вызова OpenAI/Claude API"""
    logger.info("[LLM] Отправка промпта в нейросеть...")
    await asyncio.sleep(1.5) # Имитация ожидания ответа
    return "AI Generated Response based on provided structure and constraints."

# --- 4. ФОНОВЫЕ ЗАДАЧИ: PDF & EMAIL (M1) ---
async def process_pdf_and_delivery(score_data: dict, email: str, filename: str):
    """WeasyPrint генерация -> Resend отправка -> Очистка"""
    try:
        logger.info(f"[Background] Генерация PDF отчета {filename} (WeasyPrint)...")
        await asyncio.sleep(2)
        logger.info(f"[Background] Отправка email на {email} (Resend API)...")
        await asyncio.sleep(1)
        logger.info(f"[Background] Файл {filename} добавлен в cron на удаление через 24 часа.")
    except Exception as e:
        logger.error(f"Background Task Error: {e}")

# --- 5. ЭНДПОИНТЫ ---

@app.post("/api/v1/articles/score", response_model=ScoringResult, tags=["M3: Readiness Scoring"])
async def score_article(request: ArticleRequest, bg_tasks: BackgroundTasks):
    """Анализ статьи (M3) и фоновая отправка отчета (M1)"""
    # Вызов LLM для оценки
    ai_feedback = await call_llm_api(f"Analyze abstract: {request.abstract}")
    result = ScoringResult(total_score=85, ai_feedback=ai_feedback)
    
    # Запуск M1 (PDF + Email) в фоне
    safe_filename = f"{request.title.replace(' ', '_').lower()}.pdf"
    bg_tasks.add_task(process_pdf_and_delivery, result.model_dump(), request.author_email, safe_filename)
    
    return result

@app.post("/api/v1/briefs/generate", response_model=BriefResponse, tags=["M4: Brief Generator"])
async def generate_brief(request: BriefRequest):
    """Генерация брифа на основе RAG (M4)"""
    # Получаем контекст из векторной БД
    rag_context = await fetch_from_pgvector(request.target_topic)
    
    # Генерируем контент через LLM с учетом контекста
    brief_text = await call_llm_api(request.target_topic, context=rag_context)
    
    return BriefResponse(
        brief_content=brief_text,
        sources_used=["pgvector_doc_101", "pgvector_doc_102"]
    )

if __name__ == "__main__":
    logger.info("Для запуска используйте команду: uvicorn main:app --reload")
    logger.info("Документация Swagger UI будет доступна по адресу: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
