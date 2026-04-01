from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot
from loguru import logger
from config import BOT_TOKEN
from keyboards import get_guide_keyboard, get_shortlist_keyboard, get_rent_options_keyboard, get_tax_guide_keyboard

bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

async def send_guide(user_id):
    text = "📚 <b>Дарим полезный гайд \"7 шагов к безопасной сделке: как проверить застройщика?\"</b>"
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=get_guide_keyboard())
        logger.info(f"Гайд отправлен пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки гайда {user_id}: {e}")

async def send_shortlist(user_id):
    text = (
        "🔥 <b>Открываем запись в short-list до старта продаж нового комплекса.</b>\n\n"
        "Хотите первым получить доступ к планировкам и выбрать лучший лот?"
    )
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=get_shortlist_keyboard())
        logger.info(f"Short-list отправлен пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки short-list {user_id}: {e}")

async def send_rent_options(user_id):
    text = "🏠 <b>Собрали 5 вариантов квартир с ремонтом и платежом до 35.000₽, хотите взглянуть?</b>"
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=get_rent_options_keyboard())
        logger.info(f"Варианты с ремонтом отправлены пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки вариантов с ремонтом {user_id}: {e}")

async def send_tax_guide(user_id):
    text = (
        "📄 <b>Как платить налоги на недвижимость правильно?</b>\n\n"
        "Собрали для вас простой гайд. Уберегите себя от штрафов."
    )
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=get_tax_guide_keyboard())
        logger.info(f"Гайд по налогам отправлен пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки гайда по налогам {user_id}: {e}")

def schedule_user_messages(user_id):
    from datetime import datetime, timedelta
    now = datetime.now()

    guide_time = now + timedelta(minutes=15)
    scheduler.add_job(send_guide, trigger=DateTrigger(run_date=guide_time), args=[user_id], id=f"guide_{user_id}", replace_existing=True)

    shortlist_time = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0)
    if shortlist_time < now:
        shortlist_time += timedelta(days=1)
    scheduler.add_job(send_shortlist, trigger=DateTrigger(run_date=shortlist_time), args=[user_id], id=f"shortlist_{user_id}", replace_existing=True)

    rent_time = (now + timedelta(days=2)).replace(hour=15, minute=0, second=0)
    if rent_time < now:
        rent_time += timedelta(days=1)
    scheduler.add_job(send_rent_options, trigger=DateTrigger(run_date=rent_time), args=[user_id], id=f"rent_{user_id}", replace_existing=True)

    tax_time = (now + timedelta(days=3)).replace(hour=13, minute=0, second=0)
    if tax_time < now:
        tax_time += timedelta(days=1)
    scheduler.add_job(send_tax_guide, trigger=DateTrigger(run_date=tax_time), args=[user_id], id=f"tax_{user_id}", replace_existing=True)

    logger.info(f"Запланированы рассылки для пользователя {user_id}")

def setup_scheduler():
    scheduler.start()
    logger.info("Планировщик запущен")