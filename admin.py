from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
import database as db
from config import ADMIN_IDS
import keyboards as kb

router = Router()

class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_promo_text = State()
    waiting_promo_price = State()
    waiting_promo_location = State()
    waiting_promo_description = State()
    waiting_promo_image = State()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    await message.answer("👑 <b>Админ-панель</b>\n\nВыберите действие:", parse_mode="HTML", reply_markup=kb.get_admin_keyboard())

@router.callback_query(lambda c: c.data.startswith("admin_"))
async def admin_actions(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return

    action = callback.data.split("_")[1]

    if action == "broadcast":
        await callback.message.edit_text(
            "📢 <b>Введите текст для рассылки</b>\n\nЧтобы отменить: /cancel",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_broadcast)

    elif action == "add_promo":
        await callback.message.edit_text(
            "➕ <b>Добавление промо-предложения</b>\n\nВведите название:",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_promo_text)

    elif action == "clients":
        clients = await db.get_all_clients()
        if not clients:
            await callback.message.edit_text("📋 Нет клиентов")
        else:
            text = "📋 <b>Список клиентов</b>\n\n"
            for client in clients[:20]:
                text += f"🆔 {client.get('user_id')} | {client.get('name') or '—'}\n📞 {client.get('phone') or '—'}\n🎯 {client.get('purpose')}\n🏙 {client.get('city') or '—'} | {client.get('layout') or '—'}\n📅 {client.get('created_at', '')[:16]}\n🏷 {client.get('status')}\n{'─' * 20}\n"
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))

    elif action == "hot_clients":
        clients = await db.get_all_clients()
        hot = [c for c in clients if c.get("status") == "new" and c.get("phone")]
        if not hot:
            await callback.message.edit_text("🔥 Нет горячих клиентов")
        else:
            text = "🔥 <b>Горячие клиенты</b>\n\n"
            for client in hot:
                text += f"👤 {client.get('name') or '—'}\n📞 {client.get('phone')}\n🏢 {client.get('purpose')}\n📅 {client.get('created_at', '')[:16]}\n{'─' * 20}\n"
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))

    elif action == "back":
        await callback.message.edit_text("👑 <b>Админ-панель</b>", parse_mode="HTML", reply_markup=kb.get_admin_keyboard())

    await callback.answer()

@router.message(AdminStates.waiting_broadcast)
async def broadcast_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Рассылка отменена")
        return

    users = await db.get_all_users()
    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user['user_id'], message.text, parse_mode="HTML")
            sent += 1
        except:
            pass

    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent} пользователям")
    await state.clear()

@router.message(AdminStates.waiting_promo_text)
async def add_promo_name(message: types.Message, state: FSMContext):
    await state.update_data(promo_name=message.text)
    await message.answer("💰 Введите цену:")
    await state.set_state(AdminStates.waiting_promo_price)

@router.message(AdminStates.waiting_promo_price)
async def add_promo_price(message: types.Message, state: FSMContext):
    await state.update_data(promo_price=message.text)
    await message.answer("📍 Введите локацию:")
    await state.set_state(AdminStates.waiting_promo_location)

@router.message(AdminStates.waiting_promo_location)
async def add_promo_location(message: types.Message, state: FSMContext):
    await state.update_data(promo_location=message.text)
    await message.answer("📝 Введите описание:")
    await state.set_state(AdminStates.waiting_promo_description)

@router.message(AdminStates.waiting_promo_description)
async def add_promo_description(message: types.Message, state: FSMContext):
    await state.update_data(promo_description=message.text)
    await message.answer("🖼 Отправьте фото (или /skip):")
    await state.set_state(AdminStates.waiting_promo_image)

@router.message(AdminStates.waiting_promo_image, F.photo)
async def add_promo_image(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    data = await state.get_data()
    await db.add_promo(
        name=data.get("promo_name"),
        price=data.get("promo_price"),
        location=data.get("promo_location"),
        description=data.get("promo_description"),
        image_url=file_id
    )
    await message.answer("✅ Промо-предложение добавлено!")
    await state.clear()

@router.message(AdminStates.waiting_promo_image, F.text == "/skip")
async def skip_promo_image(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.add_promo(
        name=data.get("promo_name"),
        price=data.get("promo_price"),
        location=data.get("promo_location"),
        description=data.get("promo_description")
    )
    await message.answer("✅ Промо-предложение добавлено без фото!")
    await state.clear()