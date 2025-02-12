import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Импортируем настройки БД и модель
from db import SessionLocal, TestResult

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле!")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализируем бота, диспетчер и хранилище состояний
bot = Bot(token=TOKEN)
storage = MemoryStorage()  # Используем in-memory storage
dp = Dispatcher(storage=storage)

# Определяем состояния теста
class TestStates(StatesGroup):
    Q1 = State()
    Q2 = State()
    Q3 = State()

# Вопросы
QUESTIONS = [
    {"question": "Какой оператор используется для проверки равенства в Python?", "options": ["==", "=", "!="], "correct": "=="},
    {"question": "Как называется структура данных, которая упорядочивает элементы по ключу?", "options": ["Список", "Словарь", "Множество"], "correct": "Словарь"},
    {"question": "Какой тип цикла используется для обхода итерируемых объектов в Python?", "options": ["for", "while", "do-while"], "correct": "for"}
]

# Клавиатура WebApp
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Начать тест", web_app=WebAppInfo(url="https://tech-screen-front.onrender.com/"))]
    ])
    await message.answer("Привет! Это бот для технического скрининга.\nНажми кнопку ниже, чтобы начать тест.", reply_markup=keyboard)

# Функция для создания кнопок ответов
def create_keyboard(options: list) -> types.ReplyKeyboardMarkup:
    keyboard_buttons = [[types.KeyboardButton(text=option)] for option in options]
    return types.ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True, one_time_keyboard=True)

# Обработка ответов теста
@dp.message(Command("test"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Добро пожаловать на технический скрининг!\n\nПервый вопрос:\n{QUESTIONS[0]['question']}")
    keyboard = create_keyboard(QUESTIONS[0]["options"])
    await message.answer("Выберите ответ:", reply_markup=keyboard)
    await state.set_state(TestStates.Q1)

@dp.message(TestStates.Q1)
async def process_q1(message: types.Message, state: FSMContext):
    await state.update_data(q1=message.text.strip())
    await message.answer(f"Второй вопрос:\n{QUESTIONS[1]['question']}")
    keyboard = create_keyboard(QUESTIONS[1]["options"])
    await message.answer("Выберите ответ:", reply_markup=keyboard)
    await state.set_state(TestStates.Q2)

@dp.message(TestStates.Q2)
async def process_q2(message: types.Message, state: FSMContext):
    await state.update_data(q2=message.text.strip())
    await message.answer(f"Третий вопрос:\n{QUESTIONS[2]['question']}")
    keyboard = create_keyboard(QUESTIONS[2]["options"])
    await message.answer("Выберите ответ:", reply_markup=keyboard)
    await state.set_state(TestStates.Q3)

@dp.message(TestStates.Q3)
async def process_q3(message: types.Message, state: FSMContext):
    await state.update_data(q3=message.text.strip())
    data = await state.get_data()
    
    score = sum(1 for i in range(3) if data.get(f"q{i+1}") == QUESTIONS[i]["correct"])
    await message.answer(f"Тест завершен! Ваш результат: {score} из {len(QUESTIONS)}")

    # Сохраняем результат в БД
    session = SessionLocal()
    try:
        result = TestResult(user_id=str(message.from_user.id), q1=data.get("q1"), q2=data.get("q2"), q3=data.get("q3"), score=score)
        session.add(result)
        session.commit()
        logging.info("✅ Результат сохранен в базе данных")
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Ошибка сохранения в базе: {e}")
    finally:
        session.close()

    await state.clear()

# Запуск бота
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
