import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

# 1. Настройка профессионального логирования (выглядит солидно)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("AcademicAI_PoC")

app = FastAPI(
    title="Academic AI: Article Scorer (PoC)",
    description="Микросервис для оценки академических статей (M1 & M3)",
    version="1.0.0"
)

# 2. Схемы данных (Pydantic) - показываем, что умеем валидировать данные
class ArticleRequest(BaseModel):
    title: str = Field(..., example="Machine Learning in Healthcare", min_length=5)
    abstract: str = Field(..., description="Анотация статьи", min_length=20)
    author_email: str = Field(..., pattern=r"^\S+@\S+\.\S+$", example="author@science.org")

class ScoringResult(BaseModel):
    clarity_score: int
    methodology_score: int
    relevance_score: int
    ai_feedback: str

# 3. Сервисный слой: Имитация работы OpenAI (M3)
async def ai_scoring_service(abstract: str) -> ScoringResult:
    """Mock-сервис для имитации вызова OpenAI/Claude API"""
    logger.info("Отправка запроса в LLM (OpenAI/Claude)...")
    await asyncio.sleep(1.5) # Имитация задержки сети
    
    # Возвращаем структурированный ответ, как просили в ТЗ (JSON результат)
    logger.info("Ответ от LLM успешно получен.")
    return ScoringResult(
        clarity_score=85,
        methodology_score=92,
        relevance_score=78,
        ai_feedback="Strong methodology, but needs clearer definitions in the introduction."
    )

# 4. Сервисный слой: Работа с PDF и Email (M1)
async def process_pdf_and_delivery(score: ScoringResult, email: str, file_name: str):
    """Фоновая задача: Генерация PDF (WeasyPrint) -> Відправка (Resend) -> Видалення"""
    try:
        # Шаг 1: Генерация (Mock)
        logger.info(f"PDF Generation: Создание отчета {file_name} (WeasyPrint/ReportLab)...")
        await asyncio.sleep(2) 
        
        # Шаг 2: Отправка (Mock)
        logger.info(f"Email Delivery: Отправка отчета на {email} через Resend API...")
        await asyncio.sleep(1)
        
        # Шаг 3: Удаление (Mock)
        logger.info(f"Cleanup: Файл {file_name} поставлен в очередь на удаление через 24ч.")
    except Exception as e:
        logger.error(f"Ошибка в фоновом процессе: {e}")

# 5. Основной API Эндпоинт
@app.post("/api/v1/articles/score", response_model=ScoringResult, status_code=status.HTTP_200_OK)
async def score_academic_article(request: ArticleRequest, bg_tasks: BackgroundTasks):
    """
    Анализ статьи через LLM с последующей фоновой генерацией PDF-отчета.
    """
    try:
        # Получаем оценку от ИИ (ожидаем завершения, так как это нужно вернуть в ответе)
        scoring_result = await ai_scoring_service(request.abstract)
        
        # Запускаем генерацию и отправку PDF в фоне (НЕ блокируем ответ пользователю)
        safe_filename = f"{request.title.replace(' ', '_').lower()}_report.pdf"
        bg_tasks.add_task(process_pdf_and_delivery, scoring_result, request.author_email, safe_filename)
        
        return scoring_result
        
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

if __name__ == "__main__":
    logger.info("🚀 Сервер запущен! Перейди по ссылке: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
