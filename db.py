import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+psycopg2://postgres:123@localhost/Tech_screen"

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    q1 = Column(String)
    q2 = Column(String)
    q3 = Column(String)
    score = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Новая таблица для вопросов
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)  # Текст вопроса
    options = Column(Text, nullable=False)  # Варианты ответов, например, в формате JSON или разделенные запятыми
    correct = Column(String, nullable=False)  # Правильный ответ

# Создаем таблицы (если их ещё нет)
Base.metadata.create_all(bind=engine)
