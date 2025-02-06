from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from db import SessionLocal, TestResult, Question, Base, engine
from pydantic import BaseModel
from typing import List, Optional
import datetime

# Создаем таблицы, если их еще нет
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HR API для технического скрининга")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Эндпоинты для вопросов ---
class QuestionSchema(BaseModel):
    id: Optional[int]
    text: str
    options: str
    correct: str

    class Config:
        orm_mode = True

@app.get("/questions", response_model=List[QuestionSchema])
def read_questions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    questions = db.query(Question).offset(skip).limit(limit).all()
    return questions

@app.get("/questions/{question_id}", response_model=QuestionSchema)
def read_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@app.post("/questions", response_model=QuestionSchema)
def create_question(question: QuestionSchema, db: Session = Depends(get_db)):
    db_question = Question(text=question.text, options=question.options, correct=question.correct)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@app.put("/questions/{question_id}", response_model=QuestionSchema)
def update_question(question_id: int, updated: QuestionSchema, db: Session = Depends(get_db)):
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    db_question.text = updated.text
    db_question.options = updated.options
    db_question.correct = updated.correct
    db.commit()
    db.refresh(db_question)
    return db_question

@app.delete("/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(db_question)
    db.commit()
    return {"detail": "Question deleted"}

# --- Эндпоинты для результатов тестирования ---
class TestResultSchema(BaseModel):
    id: int
    user_id: str
    q1: str
    q2: str
    q3: str
    score: int
    timestamp: datetime.datetime

    class Config:
        orm_mode = True


        
@app.get("/results", response_model=List[TestResultSchema])
def read_results(
    skip: int = 0,
    limit: int = 100,
    min_score: Optional[int] = Query(None, description="Минимальный балл"),
    max_score: Optional[int] = Query(None, description="Максимальный балл"),
    start_date: Optional[datetime.date] = Query(None, description="Начало диапазона дат (YYYY-MM-DD)"),
    end_date: Optional[datetime.date] = Query(None, description="Конец диапазона дат (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query("timestamp", description="Поле сортировки (score или timestamp)"),
    order: Optional[str] = Query("desc", description="Порядок сортировки (asc или desc)"),
    db: Session = Depends(get_db)
):
    query = db.query(TestResult)
    
    # Фильтрация по баллам
    if min_score is not None:
        query = query.filter(TestResult.score >= min_score)
    if max_score is not None:
        query = query.filter(TestResult.score <= max_score)
    
    # Фильтрация по дате
    if start_date is not None:
        # Преобразуем дату в datetime, задавая начало дня
        query = query.filter(TestResult.timestamp >= datetime.datetime.combine(start_date, datetime.time.min))
    if end_date is not None:
        # Фильтруем до конца дня
        query = query.filter(TestResult.timestamp <= datetime.datetime.combine(end_date, datetime.time.max))
    
    # Сортировка
    sort_column = TestResult.timestamp  # по умолчанию сортировка по времени
    if sort_by == "score":
        sort_column = TestResult.score
    
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    results = query.offset(skip).limit(limit).all()
    return results

@app.get("/results/{result_id}", response_model=TestResultSchema)
def read_result(result_id: int, db: Session = Depends(get_db)):
    result = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result
