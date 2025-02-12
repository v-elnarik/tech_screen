from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from db import SessionLocal, TestResult, Question, User, Base, engine
from pydantic import BaseModel
from typing import List, Optional
import datetime
from passlib.context import CryptContext

# Создаем таблицы, если их еще нет
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HR API для технического скрининга")

CAT_GIF_URL = "https://media.giphy.com/media/v6aOjy0Qo1fIA/giphy.gif"

@app.get("/")
async def root():
    return RedirectResponse(url=CAT_GIF_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# --- Настройка хеширования паролей ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Модели Pydantic ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class QuestionSchema(BaseModel):
    id: Optional[int]
    text: str
    options: str
    correct: str

    class Config:
        orm_mode = True

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

# --- Эндпоинты авторизации ---
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="❌ Пользователь уже существует!")

    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "✅ Пользователь зарегистрирован!"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="❌ Неверный логин или пароль")

    return {"message": "✅ Успешный вход!", "username": db_user.username}

# --- Эндпоинты для вопросов ---
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
    
    if min_score is not None:
        query = query.filter(TestResult.score >= min_score)
    if max_score is not None:
        query = query.filter(TestResult.score <= max_score)
    
    if start_date is not None:
        query = query.filter(TestResult.timestamp >= datetime.datetime.combine(start_date, datetime.time.min))
    if end_date is not None:
        query = query.filter(TestResult.timestamp <= datetime.datetime.combine(end_date, datetime.time.max))
    
    sort_column = TestResult.timestamp if sort_by == "timestamp" else TestResult.score
    query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc())

    results = query.offset(skip).limit(limit).all()
    return results

@app.get("/results/{result_id}", response_model=TestResultSchema)
def read_result(result_id: int, db: Session = Depends(get_db)):
    result = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result
