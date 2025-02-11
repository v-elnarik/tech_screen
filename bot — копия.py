import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print("Loaded TOKEN:", TOKEN)  # Для отладки: убедитесь, что токен выводится

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера (без передачи бота в Dispatcher)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start с использованием нового синтаксиса
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Начать тест", web_app=WebAppInfo(url="https://your-web-app-url.com"))]
    ])
    await message.answer(
        "Привет! Это бот для технического скрининга.\nНажми кнопку ниже, чтобы начать тест.",
        reply_markup=keyboard
    )

# Создаем FastAPI-приложение
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "OK", "message": "FastAPI работает"}

# Функция для запуска polling бота (aiogram v3)
def start_bot():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    import threading

    # Запускаем polling бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    # Запускаем FastAPI через uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
@dp.message(Command("start"))
async def start_command(message: types.Message):
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "Привет! Это бот для технического скрининга.\nНажми кнопку ниже, чтобы начать тест.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Начать тест", web_app=WebAppInfo(url="https://your-web-app-url.com"))]
        ])
    )
