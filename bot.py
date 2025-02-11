import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Импортируем настройки БД и модель
from db import SessionLocal, TestResult

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле!")

logging.basicConfig(level=logging.INFO)

# Инициализируем бота, диспетчер и хранилище состояний
bot = Bot(token=TOKEN)
storage = MemoryStorage()  # Используем in-memory storage для прототипа
dp = Dispatcher(storage=storage)

# Определяем состояния для тестирования
class TestStates(StatesGroup):
    Q1 = State()  # вопрос 1
    Q2 = State()  # вопрос 2
    Q3 = State()  # вопрос 3

# Пример вопросов и правильных ответов
QUESTIONS = [
    {
        "question": "Какой оператор используется для проверки равенства в Python?",
        "options": ["==", "=", "!="],
        "correct": "=="
    },
    {
        "question": "Как называется структура данных, которая упорядочивает элементы по ключу?",
        "options": ["Список", "Словарь", "Множество"],
        "correct": "Словарь"
    },
    {
        "question": "Какой тип цикла используется для обхода итерируемых объектов в Python?",
        "options": ["for", "while", "do-while"],
        "correct": "for"
    }
]

# Функция для создания клавиатуры с кнопками из списка вариантов
def create_keyboard(options: list) -> types.ReplyKeyboardMarkup:
    # Каждая кнопка создается как объект KeyboardButton, каждая кнопка в отдельном ряду
    keyboard_buttons = [[types.KeyboardButton(text=option)] for option in options]
    return types.ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Обработчик команды /start — начинает тестирование
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать на технический скрининг!\n\nПервый вопрос:\n" +
        QUESTIONS[0]["question"]
    )
    keyboard = create_keyboard(QUESTIONS[0]["options"])
    await message.answer("Выберите ответ:", reply_markup=keyboard)
    await state.set_state(TestStates.Q1)

# Обработка первого вопроса
@dp.message(TestStates.Q1)
async def process_q1(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    await state.update_data(q1=answer)
    await message.answer("Второй вопрос:\n" + QUESTIONS[1]["question"])
    keyboard = create_keyboard(QUESTIONS[1]["options"])
    await message.answer("Выберите ответ:", reply_markup=keyboard)
    await state.set_state(TestStates.Q2)

# Обработка второго вопроса
@dp.message(TestStates.Q2)
async def process_q2(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    await state.update_data(q2=answer)
    await message.answer("Третий вопрос:\n" + QUESTIONS[2]["question"])
    keyboard = create_keyboard(QUESTIONS[2]["options"])
    await message.answer("Выберите ответ:", reply_markup=keyboard)
    await state.set_state(TestStates.Q3)

# Обработка третьего вопроса и подведение итогов
@dp.message(TestStates.Q3)
async def process_q3(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    await state.update_data(q3=answer)
    data = await state.get_data()
    
    # Подсчет баллов
    score = sum(1 for i in range(3) if data.get(f"q{i+1}") == QUESTIONS[i]["correct"])

    await message.answer(f"Тест завершен! Ваш результат: {score} из {len(QUESTIONS)}")
    
    # Сохранение результата в базе данных
    session = SessionLocal()
    try:
        result = TestResult(
            user_id=str(message.from_user.id),
            q1=data.get("q1"),
            q2=data.get("q2"),
            q3=data.get("q3"),
            score=score
        )
        session.add(result)
        session.commit()
        logging.info("✅ Результат сохранен в базе данных")
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Ошибка сохранения в базе: {e}")
    finally:
        session.close()

# Основной запуск бота
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
