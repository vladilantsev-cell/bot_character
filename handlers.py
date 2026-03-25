import httpx
import aiohttp
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from datetime import datetime, timedelta

from config import SUPABASE_URL, SUPABASE_KEY, WEEKLY_POST_LINK, GUIDE_LINK, CHANNEL_ID
import keyboards as kb
from utils import check_subscription
import database as db

router = Router()


# === СОСТОЯНИЯ ===
class Form(StatesGroup):
    purpose = State()
    city = State()
    layout = State()
    waiting_phone = State()
    waiting_promo_phone = State()
    waiting_promo_name = State()
    # Калькулятор ипотеки
    mortgage_price = State()
    mortgage_down_payment = State()
    mortgage_rate = State()
    mortgage_term = State()


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
async def get_catalog_from_db(city: str = None, purpose: str = None, layout: str = None):
    """Получает каталог из базы данных"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/catalog"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        params = {}
        if city:
            params["city"] = f"eq.{city}"
        if purpose:
            params["purpose"] = f"eq.{purpose}"
        if layout:
            params["layout"] = f"eq.{layout}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения каталога: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Ошибка получения каталога: {e}")
        return []


async def send_catalog(message, items, title="Подборка объектов"):
    """Отправляет каталог объектов с картинками"""
    if not items:
        await message.answer(
            "😕 К сожалению, пока нет подходящих вариантов.\n\n"
            "Оставьте заявку, и наш специалист подберёт варианты вручную:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 Оставить заявку", callback_data="leave_request")]
            ])
        )
        return

    await message.answer(f"🏢 <b>{title}</b>\n\n", parse_mode="HTML")

    for item in items[:10]:
        text = (
            f"🏢 <b>{item.get('name')}</b>\n"
            f"💰 <b>{item.get('price')}</b>\n"
            f"💳 {item.get('monthly_payment')} | ставка {item.get('rate')}\n\n"
            f"{item.get('description')[:400]}..."
        )

        if item.get('image_url'):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(item.get('image_url')) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            await message.answer_photo(
                                photo=BufferedInputFile(image_data, filename=f"{item.get('id')}.jpg"),
                                caption=text,
                                parse_mode="HTML",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text="📞 Консультация",
                                                          callback_data=f"consult_{item.get('id')}")]
                                ])
                            )
                        else:
                            await message.answer(
                                text,
                                parse_mode="HTML",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text="📞 Консультация",
                                                          callback_data=f"consult_{item.get('id')}")]
                                ])
                            )
            except Exception as e:
                logger.error(f"Ошибка отправки фото: {e}")
                await message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📞 Консультация", callback_data=f"consult_{item.get('id')}")]
                    ])
                )
        else:
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📞 Консультация", callback_data=f"consult_{item.get('id')}")]
                ])
            )

    # Предложение подобрать варианты под бюджет
    await message.answer(
        "💡 <b>Хотите, я сразу подберу 3 самых актуальных варианта под ваш бюджет?</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, подобрать", callback_data="budget_yes")],
            [InlineKeyboardButton(text="⏰ Позже", callback_data="budget_no")]
        ])
    )


async def schedule_user_messages(user_id):
    """Планирует отложенные сообщения"""
    from scheduler import send_guide, send_shortlist, send_rent_options, send_tax_guide
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    now = datetime.now()

    # Гайд через 15 минут
    guide_time = now + timedelta(minutes=15)
    scheduler.add_job(
        send_guide,
        trigger=DateTrigger(run_date=guide_time),
        args=[user_id],
        id=f"guide_{user_id}"
    )

    # Short-list через 1 день в 11:00
    day1 = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0)
    if day1 < now:
        day1 += timedelta(days=1)
    scheduler.add_job(
        send_shortlist,
        trigger=DateTrigger(run_date=day1),
        args=[user_id],
        id=f"shortlist_{user_id}"
    )

    # Варианты с ремонтом через 2 дня в 15:00
    day2 = (now + timedelta(days=2)).replace(hour=15, minute=0, second=0)
    if day2 < now:
        day2 += timedelta(days=1)
    scheduler.add_job(
        send_rent_options,
        trigger=DateTrigger(run_date=day2),
        args=[user_id],
        id=f"rent_{user_id}"
    )

    # Гайд по налогам через 3 дня в 13:00
    day3 = (now + timedelta(days=3)).replace(hour=13, minute=0, second=0)
    if day3 < now:
        day3 += timedelta(days=1)
    scheduler.add_job(
        send_tax_guide,
        trigger=DateTrigger(run_date=day3),
        args=[user_id],
        id=f"tax_{user_id}"
    )

    scheduler.start()
    logger.info(f"Запланированы рассылки для пользователя {user_id}")


# === ОСНОВНЫЕ ОБРАБОТЧИКИ ===
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await db.save_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    await message.answer(
        "👋 <b>Привет! Я помогу подобрать объект недвижимости под ваш запрос — по реальным ценам и самой выгодной ставке.</b>\n\n"
        "Ответьте на 2 вопроса, чтобы я собрал точную подборку 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Начать подбор", callback_data="continue")]
        ])
    )


@router.message(Command("restart"))
async def cmd_restart(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(Command("menu"))
async def menu_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=kb.get_main_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == "continue")
async def continue_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏠 <b>Скажите, для чего вы рассматриваете покупку недвижимости?</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Для себя", callback_data="purpose_self")],
            [InlineKeyboardButton(text="💰 Для инвестиций", callback_data="purpose_invest")]
        ])
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("purpose_"))
async def purpose_handler(callback: types.CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)

    if purpose == "invest":
        await callback.message.edit_text(
            "🌆 <b>В каком регионе рассматриваете покупку?</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Москва", callback_data="city_moscow")],
                [InlineKeyboardButton(text="Санкт-Петербург", callback_data="city_spb")],
                [InlineKeyboardButton(text="Черноморское побережье", callback_data="city_blacksea")],
                [InlineKeyboardButton(text="Новосибирск", callback_data="city_novosibirsk")],
                [InlineKeyboardButton(text="Алтай", callback_data="city_altay")]
            ])
        )
    else:
        await callback.message.edit_text(
            "🏠 <b>Какую планировку рассматриваете?</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Студия", callback_data="layout_studio")],
                [InlineKeyboardButton(text="1-комнатная", callback_data="layout_1")],
                [InlineKeyboardButton(text="2-комнатная", callback_data="layout_2")],
                [InlineKeyboardButton(text="3-комнатная", callback_data="layout_3")]
            ])
        )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("city_"))
async def city_handler(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split("_")[1]
    city_names = {
        "moscow": "Москва",
        "spb": "Санкт-Петербург",
        "blacksea": "Черноморское побережье",
        "novosibirsk": "Новосибирск",
        "altay": "Алтай"
    }
    await state.update_data(city=city_names.get(city, city))

    await callback.message.edit_text(
        "🏠 <b>Какую планировку рассматриваете?</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Студия", callback_data="layout_studio")],
            [InlineKeyboardButton(text="1-комнатная", callback_data="layout_1")],
            [InlineKeyboardButton(text="2-комнатная", callback_data="layout_2")],
            [InlineKeyboardButton(text="3-комнатная", callback_data="layout_3")],
            [InlineKeyboardButton(text="Все варианты", callback_data="layout_all")]
        ])
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("layout_"))
async def layout_handler(callback: types.CallbackQuery, state: FSMContext):
    layout = callback.data.split("_")[1]
    layout_names = {
        "studio": "Студия",
        "1": "1-комнатная",
        "2": "2-комнатная",
        "3": "3-комнатная",
        "all": None
    }
    await state.update_data(layout=layout_names.get(layout, layout))

    # Проверка подписки
    subscribed = await check_subscription(callback.from_user.id)
    data = await state.get_data()

    if not subscribed:
        await callback.message.edit_text(
            "🔔 <b>Чтобы получить подборку, подпишитесь на наш канал — там актуальные лоты, обзоры и интересные статьи.</b>\n\n"
            f"👉 <a href='https://t.me/{CHANNEL_ID}'>Подписаться</a>\n\n"
            "После подписки нажмите кнопку ниже 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
            ])
        )
    else:
        await show_catalog_from_state(callback.message, data, layout_names.get(layout, layout))

    await callback.answer()


@router.callback_query(lambda c: c.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery, state: FSMContext):
    subscribed = await check_subscription(callback.from_user.id)
    data = await state.get_data()
    layout = data.get("layout")

    if subscribed:
        await callback.message.edit_text(
            "✅ <b>Отлично! 🎉</b>\n\nВот обещанная подборка объектов под ваш запрос 👇",
            parse_mode="HTML"
        )
        await show_catalog_from_state(callback.message, data, layout)
    else:
        await callback.message.edit_text(
            "⚠️ <b>Упс, кажется, вы не подписались.</b>\n\n"
            "Без подписки я не смогу выдать материал.\n\n"
            f"Повторите попытку снова или напишите нам в чат поддержки: @smllr",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
    await callback.answer()


async def show_catalog_from_state(message, data, layout):
    purpose = data.get("purpose")
    city = data.get("city")

    # Получаем каталог из базы
    items = await get_catalog_from_db(city, purpose, layout)

    title = f"Подборка для {'себя' if purpose == 'self' else 'инвестиций'}"
    if city:
        title += f" в {city}"
    if layout and layout != "all":
        title += f", {layout}"

    await send_catalog(message, items, title)


@router.callback_query(lambda c: c.data == "budget_yes")
async def budget_yes_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📱 <b>Супер! Укажите, пожалуйста, номер телефона — чтобы наш специалист прислал вам конкретные лоты и рассчитал ипотеку.</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Отправить мой номер", callback_data="send_phone", request_contact=True)]
        ])
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "budget_no")
async def budget_no_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🤝 <b>Договорились! Как будете готовы - нажмите на кнопку \"Бесплатная консультация\" в меню и специалист вам ответит.</b>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "send_phone", flags={"is_contact": True})
async def phone_handler(callback: types.CallbackQuery, state: FSMContext):
    contact = callback.message.contact
    if contact:
        phone = contact.phone_number
        user_id = callback.from_user.id

        await db.update_user_phone(user_id, phone)
        await db.save_client_request(user_id, "budget", phone=phone)

        await callback.message.answer(
            "✅ <b>Спасибо! 🙌</b>\n\n"
            "Мы свяжемся с вами в ближайшее время.\n\n"
            "А пока можете посмотреть подборку квартир недели — вот ссылка на свежий пост 👇",
            parse_mode="HTML"
        )
        await callback.message.answer(
            f"🏙 <a href='{WEEKLY_POST_LINK}'>Смотреть квартиры недели</a>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏢 Квартиры недели", url=WEEKLY_POST_LINK)],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )

        # Запускаем отложенные рассылки
        await schedule_user_messages(user_id)

        await state.clear()
    await callback.answer()


@router.callback_query(lambda c: c.data == "leave_request")
async def leave_request_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📱 <b>Оставьте ваш контакт, и наш специалист свяжется с вами:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Отправить мой номер", callback_data="send_phone", request_contact=True)]
        ])
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "consultation")
async def consultation_handler(callback: types.CallbackQuery):
    await callback.message.answer(
        "📞 <b>Выберите удобный способ связи:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать в Telegram", url="https://t.me/smllr")],
            [InlineKeyboardButton(text="📞 Позвонить", url="tel:+78001234567")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "mortgage")
async def mortgage_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🧮 <b>Калькулятор ипотеки</b>\n\n"
        "Введите стоимость квартиры (в рублях):\n"
        "Пример: <code>5 000 000</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
    )
    await state.set_state(Form.mortgage_price)
    await callback.answer()


@router.message(Form.mortgage_price)
async def mortgage_price_handler(message: types.Message, state: FSMContext):
    try:
        price = int(message.text.replace(" ", "").replace(",", ""))
        await state.update_data(price=price)

        await message.answer(
            "💰 Введите первоначальный взнос (в рублях):\n"
            "Пример: <code>1 000 000</code>",
            parse_mode="HTML"
        )
        await state.set_state(Form.mortgage_down_payment)
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число.\n"
            "Пример: <code>5 000 000</code>",
            parse_mode="HTML"
        )


@router.message(Form.mortgage_down_payment)
async def mortgage_down_payment_handler(message: types.Message, state: FSMContext):
    try:
        down_payment = int(message.text.replace(" ", "").replace(",", ""))
        data = await state.get_data()
        price = data.get("price")

        if down_payment >= price:
            await message.answer(
                "❌ Первоначальный взнос не может быть больше или равен стоимости квартиры.\n"
                "Введите меньшую сумму:",
                parse_mode="HTML"
            )
            return

        await state.update_data(down_payment=down_payment)

        await message.answer(
            "📊 Введите процентную ставку (годовых):\n"
            "Пример: <code>12.5</code> или <code>12.5%</code>",
            parse_mode="HTML"
        )
        await state.set_state(Form.mortgage_rate)
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число.\n"
            "Пример: <code>1 000 000</code>",
            parse_mode="HTML"
        )


@router.message(Form.mortgage_rate)
async def mortgage_rate_handler(message: types.Message, state: FSMContext):
    try:
        rate_text = message.text.replace("%", "").replace(",", ".")
        rate = float(rate_text)
        await state.update_data(rate=rate)

        await message.answer(
            "📅 Введите срок ипотеки (в годах):\n"
            "Пример: <code>15</code> или <code>30</code>",
            parse_mode="HTML"
        )
        await state.set_state(Form.mortgage_term)
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число.\n"
            "Пример: <code>12.5</code>",
            parse_mode="HTML"
        )


@router.message(Form.mortgage_term)
async def mortgage_term_handler(message: types.Message, state: FSMContext):
    try:
        term = int(message.text.replace(" ", ""))
        data = await state.get_data()
        price = data.get("price")
        down_payment = data.get("down_payment")
        rate = data.get("rate")

        loan_amount = price - down_payment
        monthly_rate = rate / 100 / 12
        months = term * 12

        if monthly_rate == 0:
            monthly_payment = loan_amount / months
        else:
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / (
                        (1 + monthly_rate) ** months - 1)

        total_payment = monthly_payment * months
        overpayment = total_payment - loan_amount

        result_text = (
            f"🏠 <b>Результат расчёта ипотеки</b>\n\n"
            f"💰 Стоимость квартиры: <b>{price:,} ₽</b>\n"
            f"💸 Первоначальный взнос: <b>{down_payment:,} ₽</b>\n"
            f"🏦 Сумма кредита: <b>{loan_amount:,} ₽</b>\n"
            f"📊 Процентная ставка: <b>{rate}%</b>\n"
            f"📅 Срок: <b>{term} лет</b> ({months} мес.)\n"
            f"────────────────\n"
            f"💳 Ежемесячный платёж: <b>{monthly_payment:,.0f} ₽</b>\n"
            f"💰 Общая выплата: <b>{total_payment:,.0f} ₽</b>\n"
            f"📈 Переплата: <b>{overpayment:,.0f} ₽</b>\n\n"
            "💡 <i>Это предварительный расчёт. Для точного расчёта обратитесь к специалисту.</i>"
        )

        result_text = result_text.replace(",", " ").replace(" ", " ", 1)

        await message.answer(
            result_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Рассчитать заново", callback_data="mortgage")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка расчёта ипотеки: {e}")
        await message.answer(
            "❌ Ошибка расчёта. Проверьте введённые данные и попробуйте снова.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="mortgage")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
        await state.clear()


@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Горячие предложения", callback_data="promo_list")],
            [InlineKeyboardButton(text="🏠 Подобрать объект", callback_data="continue")],
            [InlineKeyboardButton(text="🧮 Калькулятор ипотеки", callback_data="mortgage")],
            [InlineKeyboardButton(text="🏢 Квартиры недели", url=WEEKLY_POST_LINK)],
            [InlineKeyboardButton(text="📞 Бесплатная консультация", callback_data="consultation")]
        ])
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "promo_list")
async def promo_list_handler(callback: types.CallbackQuery):
    promos = await db.get_all_promo()

    if not promos:
        await callback.message.answer(
            "😕 Пока нет горячих предложений.\n\n"
            "Подпишитесь на наш канал, чтобы не пропустить:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться", url=f"https://t.me/{CHANNEL_ID}")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
    else:
        await callback.message.edit_text(
            "🔥 <b>Горячие предложения</b>",
            parse_mode="HTML"
        )
        for promo in promos[:5]:
            text = (
                f"🏢 <b>{promo.get('name')}</b>\n"
                f"💰 {promo.get('price')}\n"
                f"📍 {promo.get('location')}\n\n"
                f"{promo.get('description')}"
            )

            if promo.get('image_url'):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(promo.get('image_url')) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                await callback.message.answer_photo(
                                    photo=BufferedInputFile(image_data, filename=f"promo_{promo.get('id')}.jpg"),
                                    caption=text,
                                    parse_mode="HTML",
                                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                        [InlineKeyboardButton(text="📞 Узнать подробнее",
                                                              callback_data=f"promo_detail_{promo.get('id')}")]
                                    ])
                                )
                except Exception as e:
                    logger.error(f"Ошибка отправки промо: {e}")
                    await callback.message.answer(
                        text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📞 Узнать подробнее",
                                                  callback_data=f"promo_detail_{promo.get('id')}")]
                        ])
                    )
            else:
                await callback.message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📞 Узнать подробнее",
                                              callback_data=f"promo_detail_{promo.get('id')}")]
                    ])
                )

    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("promo_detail_"))
async def promo_detail_handler(callback: types.CallbackQuery, state: FSMContext):
    promo_id = int(callback.data.split("_")[2])
    promo = await db.get_promo_by_id(promo_id)

    if promo:
        text = (
            f"🏢 <b>{promo.get('name')}</b>\n\n"
            f"📍 Локация: {promo.get('location')}\n"
            f"💰 Цена: {promo.get('price')}\n"
            f"🏗 Застройщик: {promo.get('builder', 'Не указан')}\n\n"
            f"{promo.get('full_description', promo.get('description'))}"
        )

        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📞 Консультация", callback_data="consultation")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
    await callback.answer()


@router.message()
async def handle_unknown(message: types.Message, state: FSMContext):
    """Обрабатывает неизвестные сообщения"""
    current_state = await state.get_state()
    if current_state not in [Form.mortgage_price.state, Form.mortgage_down_payment.state,
                             Form.mortgage_rate.state, Form.mortgage_term.state]:
        await message.answer(
            "🤷‍♂️ <b>Я вас не понимаю</b>\n\n"
            "Пожалуйста, используйте кнопки в меню или введите /start",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )