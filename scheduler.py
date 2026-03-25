from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from loguru import logger
import database as db
from config import BOT_TOKEN, GUIDE_LINK

scheduler = AsyncIOScheduler()
bot = Bot(token=BOT_TOKEN)


async def send_guide():
    """Рассылка гайда через 15 минут после регистрации (запускается отдельно)"""
    # Это будет вызываться по триггеру после регистрации нового пользователя
    pass


async def send_shortlist():
    """Рассылка про short-list через 1 день"""
    users = db.get_users_by_status("active")
    text = (
        "🔥 <b>Открываем запись в short-list до старта продаж нового комплекса.</b>\n\n"
        "Хотите первым получить доступ к планировкам и выбрать лучший лот?"
    )
    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Да, супер!", callback_data="shortlist_yes")]
                ])
            )
        except:
            pass


async def send_rent_options():
    """Рассылка вариантов с ремонтом через 2 дня"""
    users = db.get_users_by_status("active")
    text = (
        "🏠 <b>Собрали 5 вариантов квартир с ремонтом и платежом до 35.000₽, хотите взглянуть?</b>"
    )
    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="👀 Посмотреть варианты", url=WEEKLY_POST_LINK)]
                ])
            )
        except:
            pass


async def send_tax_guide():
    """Рассылка гайда по налогам через 3 дня"""
    users = db.get_users_by_status("active")
    text = (
        "📄 <b>Как платить налоги на недвижимость правильно?</b>\n\n"
        "Собрали для вас простой гайд. Уберегите себя от штрафов."
    )
    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📖 Читать инструкцию", url=GUIDE_LINK)]
                ])
            )
        except:
            pass


def setup_scheduler():
    """Настройка планировщика"""
    # Каждый день в 10:00 проверяем и отправляем отложенные рассылки
    scheduler.add_job(send_shortlist, CronTrigger(hour=10, minute=0))
    scheduler.add_job(send_rent_options, CronTrigger(hour=10, minute=0))
    scheduler.add_job(send_tax_guide, CronTrigger(hour=10, minute=0))

    scheduler.start()
    logger.info("Планировщик запущен")