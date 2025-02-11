import os
import logging
import asyncio
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn

# === Настройка логирования ===
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === Загрузка переменных окружения ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if TOKEN:
    logging.info(f"✅ TELEGRAM_BOT_TOKEN загружен, длина: {len(TOKEN)} символов")
else:
    logging.error("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден! Проверь переменные окружения.")
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")

# === Инициализация бота и диспетчера ===
try:
    bot = Bot(token=TOKEN)
    dp = Dispatcher()  # aiogram 3.x
    logging.info("✅ Бот успешно инициализирован.")
except Exception as e:
    logging.error(f"❌ Ошибка инициализации бота: {e}")
    raise

# === Обработчик команды /start ===
@dp.message(Command("start"))
async def start_command(message: types.Message):
    logging.info(f"✅ Получена команда /start от пользователя {message.from_user.id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Начать тест", web_app=WebAppInfo(url="https://your-web-app-url.com"))]
    ])
    await message.answer(
        "Привет! Это бот для технического скрининга.\nНажми кнопку ниже, чтобы начать тест.",
        reply_markup=keyboard
    )

# === Создаем FastAPI-приложение ===
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "OK", "message": "FastAPI работает"}

# === Функция для запуска polling бота (aiogram 3.x) ===
async def start_bot():
    try:
        logging.info("🚀 Запуск бота...")
        await bot.delete_webhook(drop_pending_updates=True)  # Чистим очередь сообщений
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Бот завершился с ошибкой: {e}")
        raise

# === Запуск FastAPI и бота ===
if __name__ == "__main__":
    logging.info("🔥 Стартуем FastAPI и бота...")

    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=asyncio.run, args=(start_bot(),), daemon=True)
    bot_thread.start()

    # Запуск FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
