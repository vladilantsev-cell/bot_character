import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from loguru import logger

from config import BOT_TOKEN
from handlers import router as main_router
from admin import router as admin_router
from scheduler import setup_scheduler

# Настройка логирования
logger.add("bot.log", rotation="10 MB", retention="1 week", level="INFO")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(main_router)
dp.include_router(admin_router)

async def set_commands():
    """Устанавливает команды под вводной строкой"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="restart", description="🔄 Перезапустить"),
        BotCommand(command="menu", description="🏠 Главное меню"),
        BotCommand(command="admin", description="👑 Админ-панель"),
    ]
    await bot.set_my_commands(commands)

async def on_startup():
    """Действия при запуске"""
    logger.info("🚀 Бот запускается...")
    await set_commands()
    setup_scheduler()
    logger.info("✅ Бот готов к работе!")

async def on_shutdown():
    """Действия при остановке"""
    logger.info("🛑 Бот останавливается...")
    await bot.session.close()
    logger.info("✅ Бот остановлен")

async def main():
    await on_startup()
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        await on_shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен вручную")