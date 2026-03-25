from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
import database as db
from config import ADMIN_IDS

router = Router()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_promo_text = State()
    waiting_promo_image = State()


def is_admin(user_id):
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return

    await message.answer(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


def get_admin_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ Добавить промо", callback_data="admin_add_promo")],
        [InlineKeyboardButton(text="📋 Клиенты", callback_data="admin_clients")],
        [InlineKeyboardButton(text="🔥 Горячие клиенты", callback_data="admin_hot_clients")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


@router.callback_query(lambda c: c.data.startswith("admin_"))
async def admin_actions(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return

    action = callback.data.split("_")[1]

    if action == "broadcast":
        await callback.message.edit_text(
            "📢 <b>Введите текст для рассылки</b>\n\n"
            "Вы можете добавить фото, отправив его следующим сообщением.\n\n"
            "Чтобы отменить: /cancel",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_broadcast)

    elif action == "add_promo":
        await callback.message.edit_text(
            "➕ <b>Добавление промо-предложения</b>\n\n"
            "Введите название предложения:",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_promo_text)

    elif action == "clients":
        clients = db.get_all_clients()
        if not clients:
            await callback.message.edit_text("📋 Нет клиентов")
        else:
            text = "📋 <b>Список клиентов</b>\n\n"
            for client in clients[:20]:
                text += (
                        f"🆔 {client.get('user_id')} | {client.get('name') or '—'}\n"
                        f"📞 {client.get('phone') or '—'}\n"
                        f"🎯 {client.get('purpose')}\n"
                        f"🏙 {client.get('city') or '—'} | {client.get('layout') or '—'}\n"
                        f"📅 {client.get('created_at')[:16]}\n"
                        f"🏷 {client.get('status')}\n"
                        "─" * 20 + "\n"
                )
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
                ])
            )

    elif action == "hot_clients":
        clients = db.get_all_clients()
        hot = [c for c in clients if c.get("status") == "new" and c.get("phone")]
        if not hot:
            await callback.message.edit_text("🔥 Нет горячих клиентов")
        else:
            text = "🔥 <b>Горячие клиенты</b>\n\n"
            for client in hot:
                text += (
                        f"👤 {client.get('name') or '—'}\n"
                        f"📞 {client.get('phone')}\n"
                        f"🏢 {client.get('purpose')}\n"
                        f"📅 {client.get('created_at')[:16]}\n"
                        "─" * 20 + "\n"
                )
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
                ])
            )

    elif action == "back":
        await callback.message.edit_text(
            "👑 <b>Админ-панель</b>",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )

    await callback.answer()


@router.message(AdminStates.waiting_broadcast)
async def broadcast_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text
    if text == "/cancel":
        await state.clear()
        await message.answer("❌ Рассылка отменена")
        return

    # Получаем всех пользователей
    users = db.get_all_users()
    sent = 0

    for user in users:
        try:
            await message.bot.send_message(user['user_id'], text, parse_mode="HTML")
            sent += 1
        except:
            pass

    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent} пользователям")
    await state.clear()