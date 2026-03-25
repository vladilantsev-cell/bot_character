import httpx
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, FSInputFile
from loguru import logger

from config import BOT_TOKEN, CHANNEL_ID, SUPPORT_LINK, WEEKLY_POST_LINK, GUIDE_LINK, ADMIN_IDS
import database as db
import keyboards as kb
from utils import check_subscription

router = Router()


# === СОСТОЯНИЯ ===
class Form(StatesGroup):
    purpose = State()
    city = State()
    layout = State()
    waiting_phone = State()
    waiting_promo_phone = State()
    waiting_promo_name = State()


# === КОМАНДЫ ===
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    db.save_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    await message.answer(
        "🏢 <b>Привет! Я помогу подобрать объект недвижимости под ваш запрос — по реальным ценам и самой выгодной ставке.</b>\n\n"
        "Ответьте на 2 вопроса, чтобы я собрал точную подборку 📊",
        parse_mode="HTML",
        reply_markup=kb.get_start_keyboard()
    )


@router.message(Command("restart"))
async def cmd_restart(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=kb.get_main_menu_keyboard()
    )
    await message.answer(
        "Что хотите сделать?",
        reply_markup=kb.get_info_menu_keyboard()
    )


@router.message(F.text == "🔄 Перезапустить")
async def restart_menu(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(F.text == "ℹ️ Информация")
async def info_menu(message: types.Message):
    await message.answer(
        "📢 <b>Актуальные предложения</b>",
        parse_mode="HTML",
        reply_markup=kb.get_info_menu_keyboard()
    )


@router.message(F.text == "📞 Бесплатная консультация")
async def consultation_menu(message: types.Message):
    await message.answer(
        "📞 <b>Свяжитесь с нами удобным способом:</b>",
        parse_mode="HTML",
        reply_markup=kb.get_consultation_keyboard()
    )


# === ОБРАБОТЧИКИ КНОПОК ===
@router.callback_query(lambda c: c.data == "continue")
async def continue_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏠 <b>Для кого ищете недвижимость?</b>",
        parse_mode="HTML",
        reply_markup=kb.get_purpose_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=kb.get_info_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("purpose_"))
async def purpose_handler(callback: types.CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)

    if purpose == "invest":
        await callback.message.edit_text(
            "🌆 <b>Выберите город:</b>",
            parse_mode="HTML",
            reply_markup=kb.get_cities_keyboard()
        )
    else:
        await callback.message.edit_text(
            "🏠 <b>Какую планировку рассматриваете?</b>",
            parse_mode="HTML",
            reply_markup=kb.get_layout_keyboard()
        )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("city_"))
async def city_handler(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split("_")[1]
    await state.update_data(city=city)

    await callback.message.edit_text(
        "🏠 <b>Какую планировку рассматриваете?</b>",
        parse_mode="HTML",
        reply_markup=kb.get_layout_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("layout_"))
async def layout_handler(callback: types.CallbackQuery, state: FSMContext):
    layout = callback.data.split("_")[1]
    data = await state.get_data()

    await state.update_data(layout=layout)

    # Проверка подписки
    subscribed = await check_subscription(callback.from_user.id)

    if not subscribed:
        await callback.message.edit_text(
            "🔔 <b>Чтобы получить подборку, подпишитесь на наш канал — там актуальные лоты, обзоры и интересные статьи.</b>\n\n"
            f"👉 <a href='https://t.me/ваш_канал'>Подписаться</a>\n\n"
            "После подписки нажмите кнопку ниже 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
            ])
        )
    else:
        await show_catalog(callback.message, data, layout)

    await callback.answer()


@router.callback_query(lambda c: c.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery, state: FSMContext):
    subscribed = await check_subscription(callback.from_user.id)
    data = await state.get_data()

    if subscribed:
        await callback.message.edit_text(
            "✅ <b>Отлично!</b>\n\nВот обещанная подборка объектов под ваш запрос:",
            parse_mode="HTML"
        )
        await show_catalog(callback.message, data, data.get("layout"))
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


async def show_catalog(message, data, layout):
    purpose = data.get("purpose")
    city = data.get("city", "Москва")

    catalog = db.get_catalog_by_city(city, purpose, layout)

    if not catalog:
        await message.answer(
            "😕 К сожалению, пока нет подходящих вариантов.\n\n"
            "Оставьте заявку, и наш специалист подберёт варианты вручную:",
            reply_markup=kb.get_phone_keyboard()
        )
        return

    for item in catalog[:5]:
        text = (
            f"🏢 <b>{item.get('name')}</b>\n\n"
            f"📍 Локация: {item.get('location')}\n"
            f"💰 Цена: {item.get('price')}\n"
            f"📐 Площадь: {item.get('area')}\n"
            f"🏗 Застройщик: {item.get('builder')}\n"
            f"📝 Описание: {item.get('description')}"
        )

        if item.get('image_url'):
            await message.answer_photo(
                photo=item.get('image_url'),
                caption=text,
                parse_mode="HTML",
                reply_markup=kb.get_promo_keyboard(item.get('id'))
            )
        else:
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=kb.get_promo_keyboard(item.get('id'))
            )

    # Предложение подобрать варианты под бюджет
    await message.answer(
        "💡 <b>Хотите, я сразу подберу 3 самых актуальных варианта под ваш бюджет?</b>",
        parse_mode="HTML",
        reply_markup=kb.get_budget_keyboard()
    )


@router.callback_query(lambda c: c.data == "budget_yes")
async def budget_yes_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📱 <b>Супер! Укажите, пожалуйста, номер телефона — чтобы наш специалист прислал подборку.</b>",
        parse_mode="HTML",
        reply_markup=kb.get_phone_keyboard()
    )
    await state.set_state(Form.waiting_phone)
    await callback.answer()


@router.callback_query(lambda c: c.data == "budget_no")
async def budget_no_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🤝 <b>Договорились! Как будете готовы - нажмите на кнопку \"Бесплатная консультация\" в меню и специалист вам ответит.</b>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Form.waiting_phone, F.contact)
async def phone_handler(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    user_id = message.from_user.id

    db.update_user_phone(user_id, phone)
    db.save_client_request(user_id, "budget_request", phone=phone)

    await message.answer(
        "✅ <b>Спасибо!</b>\n\n"
        "Мы свяжемся с вами в ближайшее время.\n\n"
        "А пока можете посмотреть подборку квартир недели — вот ссылка на свежий пост:",
        parse_mode="HTML"
    )
    await message.answer(
        f"🏢 <a href='{WEEKLY_POST_LINK}'>Смотреть квартиры недели</a>",
        parse_mode="HTML",
        reply_markup=kb.get_after_consult_keyboard()
    )
    await state.clear()


@router.callback_query(lambda c: c.data.startswith("promo_detail_"))
async def promo_detail_handler(callback: types.CallbackQuery, state: FSMContext):
    promo_id = int(callback.data.split("_")[2])
    promo = db.get_promo_by_id(promo_id)

    if promo:
        text = (
            f"🏢 <b>{promo.get('name')}</b>\n\n"
            f"📍 {promo.get('location')}\n"
            f"💰 {promo.get('price')}\n"
            f"📐 {promo.get('area')}\n\n"
            f"{promo.get('full_description')}"
        )

        if promo.get('image_url'):
            await callback.message.answer_photo(
                photo=promo.get('image_url'),
                caption=text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📞 Консультация", callback_data=f"consult_{promo_id}")]
                ])
            )
        else:
            await callback.message.answer(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📞 Консультация", callback_data=f"consult_{promo_id}")]
                ])
            )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("consult_"))
async def consult_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📱 <b>Оставьте ваши контакты, и наш специалист свяжется с вами:</b>\n\n"
        "Введите ваше имя и номер телефона через пробел\n"
        "Пример: <code>Иван 79001234567</code>",
        parse_mode="HTML"
    )
    await state.set_state(Form.waiting_promo_name)
    await callback.answer()


@router.message(Form.waiting_promo_name)
async def promo_name_handler(message: types.Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer(
            "❌ <b>Пожалуйста, введите имя и номер телефона через пробел</b>\n\n"
            "Пример: <code>Иван 79001234567</code>",
            parse_mode="HTML"
        )
        return

    name = " ".join(parts[:-1])
    phone = parts[-1]

    db.save_client_request(
        message.from_user.id,
        "promo",
        phone=phone,
        name=name
    )

    await message.answer(
        "✅ <b>Спасибо!</b>\n\n"
        "Мы свяжемся с вами в ближайшее время.\n\n"
        "А пока можете посмотреть подборку квартир недели:",
        parse_mode="HTML"
    )
    await message.answer(
        f"🏢 <a href='{WEEKLY_POST_LINK}'>Смотреть квартиры недели</a>",
        parse_mode="HTML",
        reply_markup=kb.get_after_consult_keyboard()
    )
    await state.clear()


@router.callback_query(lambda c: c.data == "promo_list")
async def promo_list_handler(callback: types.CallbackQuery):
    promos = db.get_all_promo()

    if not promos:
        await callback.message.answer(
            "😕 Пока нет горячих предложений.\n\n"
            "Подпишитесь на наш канал, чтобы не пропустить:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/ваш_канал")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
    else:
        await callback.message.edit_text(
            "🔥 <b>Горячие предложения</b>",
            parse_mode="HTML"
        )
        for promo in promos:
            text = (
                f"🏢 <b>{promo.get('name')}</b>\n\n"
                f"📍 {promo.get('location')}\n"
                f"💰 {promo.get('price')}\n"
                f"🏗 {promo.get('builder')}"
            )

            if promo.get('image_url'):
                await callback.message.answer_photo(
                    photo=promo.get('image_url'),
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=kb.get_promo_keyboard(promo.get('id'))
                )
            else:
                await callback.message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=kb.get_promo_keyboard(promo.get('id'))
                )

    await callback.answer()