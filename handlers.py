import aiohttp
import httpx
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from datetime import datetime, timedelta

import database as db
import keyboards as kb
from config import WEEKLY_POST_LINK, CHANNEL_ID, SUPPORT_LINK
from utils import check_subscription
from scheduler import schedule_user_messages

router = Router()

class Form(StatesGroup):
    purpose = State()
    city = State()
    layout = State()
    waiting_phone = State()
    waiting_shortlist_phone = State()
    mortgage_price = State()
    mortgage_down_payment = State()
    mortgage_rate = State()
    mortgage_term = State()

async def get_catalog_from_db(city: str = None, purpose: str = None, layout: str = None):
    try:
        url = f"{db.SUPABASE_URL}/rest/v1/catalog"
        headers = {"apikey": db.SUPABASE_KEY, "Authorization": f"Bearer {db.SUPABASE_KEY}"}
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
            return []
    except Exception as e:
        logger.error(f"Ошибка получения каталога: {e}")
        return []

async def send_catalog(message, items, title="Подборка объектов"):
    if not items:
        await message.answer("😕 К сожалению, пока нет подходящих вариантов.\n\nОставьте заявку, и наш специалист подберёт варианты вручную:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📱 Оставить заявку", callback_data="leave_request")]]))
        return

    await message.answer(f"🏢 <b>{title}</b>\n\n", parse_mode="HTML")

    for item in items[:10]:
        text = f"🏢 <b>{item.get('name')}</b>\n💰 <b>{item.get('price')}</b>\n💳 {item.get('monthly_payment')} | ставка {item.get('rate')}\n\n{item.get('description', '')[:400]}..."
        if item.get('image_url'):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(item.get('image_url')) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            await message.answer_photo(photo=BufferedInputFile(image_data, filename=f"{item.get('id')}.jpg"), caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📞 Консультация", callback_data=f"consult_{item.get('id')}")]]))
            except:
                await message.answer(text, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")

    await message.answer("💡 <b>Хотите, я сразу подберу 3 самых актуальных варианта под ваш бюджет?</b>", parse_mode="HTML", reply_markup=kb.get_budget_keyboard())

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await db.save_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer("👋 <b>Привет! Я помогу подобрать объект недвижимости под ваш запрос — по реальным ценам и самой выгодной ставке.</b>\n\nОтветьте на 2 вопроса, чтобы я собрал точную подборку 👇", parse_mode="HTML", reply_markup=kb.main_menu_reply_keyboard)
    await message.answer("Выберите действие:", reply_markup=kb.get_start_keyboard())

@router.message(Command("restart"))
async def cmd_restart(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

@router.message(Command("menu"))
async def menu_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 <b>Главное меню</b>\n\nВыберите действие:", parse_mode="HTML", reply_markup=kb.get_main_menu_keyboard())

@router.message(F.text == "🏠 Главное меню")
async def menu_reply(message: types.Message, state: FSMContext):
    await menu_command(message, state)

@router.message(F.text == "🔄 Перезапустить")
async def restart_reply(message: types.Message, state: FSMContext):
    await cmd_restart(message, state)

@router.callback_query(lambda c: c.data == "continue")
async def continue_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🏠 <b>Скажите, для чего вы рассматриваете покупку недвижимости?</b>", parse_mode="HTML", reply_markup=kb.get_purpose_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("purpose_"))
async def purpose_handler(callback: types.CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)
    if purpose == "invest":
        await callback.message.edit_text("🌆 <b>В каком регионе рассматриваете покупку?</b>", parse_mode="HTML", reply_markup=kb.get_cities_keyboard())
    else:
        await callback.message.edit_text("🏠 <b>Какую планировку рассматриваете?</b>", parse_mode="HTML", reply_markup=kb.get_layout_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("city_"))
async def city_handler(callback: types.CallbackQuery, state: FSMContext):
    cities = {"moscow": "Москва", "spb": "Санкт-Петербург", "blacksea": "Черноморское побережье", "novosibirsk": "Новосибирск", "altay": "Алтай"}
    await state.update_data(city=cities[callback.data.split("_")[1]])
    await callback.message.edit_text("🏠 <b>Какую планировку рассматриваете?</b>", parse_mode="HTML", reply_markup=kb.get_layout_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("layout_"))
async def layout_handler(callback: types.CallbackQuery, state: FSMContext):
    layouts = {"studio": "Студия", "1": "1-комнатная", "2": "2-комнатная", "3": "3-комнатная"}
    await state.update_data(layout=layouts.get(callback.data.split("_")[1]))

    if not await check_subscription(callback.from_user.id):
        await callback.message.edit_text(f"🔔 <b>Чтобы получить подборку, подпишитесь на наш канал — там актуальные лоты, обзоры и интересные статьи.</b>\n\n👉 <a href='https://t.me/{CHANNEL_ID}'>Подписаться</a>\n\nПосле подписки нажмите кнопку ниже 👇", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]]))
    else:
        await show_catalog_from_state(callback.message, await state.get_data())
    await callback.answer()

@router.callback_query(lambda c: c.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery, state: FSMContext):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("✅ <b>Отлично! 🎉</b>\n\nВот обещанная подборка объектов под ваш запрос 👇", parse_mode="HTML")
        await show_catalog_from_state(callback.message, await state.get_data())
    else:
        await callback.message.edit_text(f"⚠️ <b>Упс, кажется, вы не подписались.</b>\n\nБез подписки я не смогу выдать материал.\n\nПовторите попытку снова или напишите нам в чат поддержки: {SUPPORT_LINK}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")], [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]))
    await callback.answer()

async def show_catalog_from_state(message, data):
    items = await get_catalog_from_db(data.get("city"), data.get("purpose"), data.get("layout"))
    title = f"Подборка для {'себя' if data.get('purpose') == 'self' else 'инвестиций'}"
    if data.get("city"):
        title += f" в {data.get('city')}"
    if data.get("layout"):
        title += f", {data.get('layout')}"
    await send_catalog(message, items, title)

@router.callback_query(lambda c: c.data == "budget_yes")
async def budget_yes_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📱 <b>Супер! Укажите, пожалуйста, номер телефона — чтобы наш специалист прислал вам конкретные лоты и рассчитал ипотеку.</b>", parse_mode="HTML", reply_markup=kb.get_phone_keyboard())
    await state.set_state(Form.waiting_phone)
    await callback.answer()

@router.callback_query(lambda c: c.data == "budget_no")
async def budget_no_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("🤝 <b>Договорились! Как будете готовы - нажмите на кнопку \"Бесплатная консультация\" в меню и специалист вам ответит.</b>", parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data == "send_phone", flags={"is_contact": True})
async def phone_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.message.contact:
        phone = callback.message.contact.phone_number
        user_id = callback.from_user.id
        await db.update_user_phone(user_id, phone)
        data = await state.get_data()
        await db.save_client_request(user_id, data.get("purpose", "budget"), phone=phone, name=callback.from_user.full_name)
        await callback.message.answer("✅ <b>Спасибо! 🙌</b>\n\nМы свяжемся с вами в ближайшее время.\n\nА пока можете посмотреть подборку квартир недели — вот ссылка на свежий пост 👇", parse_mode="HTML")
        await callback.message.answer(f"🏙 <a href='{WEEKLY_POST_LINK}'>Смотреть квартиры недели</a>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏢 Квартиры недели", url=WEEKLY_POST_LINK)], [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]))
        schedule_user_messages(user_id)
        await state.clear()
    await callback.answer()

@router.callback_query(lambda c: c.data == "leave_request")
async def leave_request_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📱 <b>Оставьте ваш контакт, и наш специалист свяжется с вами:</b>", parse_mode="HTML", reply_markup=kb.get_phone_keyboard())
    await state.set_state(Form.waiting_phone)
    await callback.answer()

@router.callback_query(lambda c: c.data == "consultation")
async def consultation_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("📞 <b>Выберите удобный способ связи:</b>", parse_mode="HTML", reply_markup=kb.get_consultation_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 <b>Главное меню</b>\n\nВыберите действие:", parse_mode="HTML", reply_markup=kb.get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "promo_list")
async def promo_list_handler(callback: types.CallbackQuery):
    promos = await db.get_all_promo()
    if not promos:
        await callback.message.answer("😕 Пока нет горячих предложений.\n\nПодпишитесь на наш канал, чтобы не пропустить:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📢 Подписаться", url=f"https://t.me/{CHANNEL_ID}")], [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]))
    else:
        await callback.message.edit_text("🔥 <b>Горячие предложения</b>", parse_mode="HTML")
        for promo in promos[:5]:
            text = f"🏢 <b>{promo.get('name')}</b>\n💰 {promo.get('price')}\n📍 {promo.get('location')}\n\n{promo.get('description')}"
            if promo.get('image_url'):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(promo.get('image_url')) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                await callback.message.answer_photo(photo=BufferedInputFile(image_data, filename=f"promo_{promo.get('id')}.jpg"), caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📞 Узнать подробнее", callback_data=f"promo_detail_{promo.get('id')}")]]))
                except:
                    await callback.message.answer(text, parse_mode="HTML")
            else:
                await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("promo_detail_"))
async def promo_detail_handler(callback: types.CallbackQuery):
    promo_id = int(callback.data.split("_")[2])
    promo = await db.get_promo_by_id(promo_id)
    if promo:
        text = f"🏢 <b>{promo.get('name')}</b>\n\n📍 Локация: {promo.get('location')}\n💰 Цена: {promo.get('price')}\n🏗 Застройщик: {promo.get('builder', 'Не указан')}\n\n{promo.get('full_description', promo.get('description'))}"
        await callback.message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📞 Консультация", callback_data="consultation")], [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]))
    await callback.answer()

@router.callback_query(lambda c: c.data == "shortlist_yes")
async def shortlist_yes_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📱 <b>Оставьте ваш контакт, и мы пришлем вам каталог сразу после релиза:</b>", parse_mode="HTML", reply_markup=kb.get_phone_keyboard())
    await state.set_state(Form.waiting_shortlist_phone)
    await callback.answer()

@router.message()
async def handle_unknown(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state not in [Form.mortgage_price.state, Form.mortgage_down_payment.state, Form.mortgage_rate.state, Form.mortgage_term.state, Form.waiting_phone.state, Form.waiting_shortlist_phone.state]:
        await message.answer("🤷‍♂️ <b>Я вас не понимаю</b>\n\nПожалуйста, используйте кнопки в меню или введите /start", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]))