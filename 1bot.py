import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
from dotenv import load_dotenv
import threading
import uvicorn

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверяем, загружен ли токен
if not TOKEN:
    logging.error("❌ TELEGRAM_BOT_TOKEN не найден! Проверь переменные окружения.")
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
logging.info(f"✅ TELEGRAM_BOT_TOKEN загружен, длина: {len(TOKEN)} символов")

# Инициализация бота и диспетчера (без аргументов!)
try:
    bot = Bot(token=TOKEN)
    dp = Dispatcher()  # В aiogram v3 Dispatcher создается БЕЗ аргументов
    logging.info("✅ Бот успешно инициализирован.")
except Exception as e:
    logging.error(f"❌ Ошибка инициализации бота: {e}")
    raise

# Регистрация обработчика
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

# FastAPI-приложение
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "OK", "message": "FastAPI работает"}

# Функция запуска бота (aiogram v3)
async def start_bot():
    try:
        logging.info("🚀 Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Бот завершился с ошибкой: {e}")
        raise

if __name__ == "__main__":
    logging.info("🔥 Стартуем FastAPI и бота...")

    # Запускаем бота в фоне
    bot_thread = threading.Thread(target=asyncio.run, args=(start_bot(),), daemon=True)
    bot_thread.start()
    
    # Запускаем FastAPI через uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
