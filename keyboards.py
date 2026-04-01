from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import WEEKLY_POST_LINK, GUIDE_LINK, SUPPORT_LINK, PHONE_NUMBER

# === ИНЛАЙН-КЛАВИАТУРЫ ===

def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Продолжить", callback_data="continue")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_purpose_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Для себя", callback_data="purpose_self")],
        [InlineKeyboardButton(text="💰 Для инвестиций", callback_data="purpose_invest")]
    ])

def get_cities_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Москва", callback_data="city_moscow")],
        [InlineKeyboardButton(text="Санкт-Петербург", callback_data="city_spb")],
        [InlineKeyboardButton(text="Черноморское побережье", callback_data="city_blacksea")],
        [InlineKeyboardButton(text="Новосибирск", callback_data="city_novosibirsk")],
        [InlineKeyboardButton(text="Алтай", callback_data="city_altay")]
    ])

def get_layout_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Студия", callback_data="layout_studio")],
        [InlineKeyboardButton(text="1-комнатная", callback_data="layout_1")],
        [InlineKeyboardButton(text="2-комнатная", callback_data="layout_2")],
        [InlineKeyboardButton(text="3-комнатная", callback_data="layout_3")]
    ])

def get_budget_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, подобрать", callback_data="budget_yes")],
        [InlineKeyboardButton(text="⏰ Позже", callback_data="budget_no")]
    ])

def get_phone_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Отправить мой номер", callback_data="send_phone", request_contact=True)]
    ])

def get_consultation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в Telegram", url=SUPPORT_LINK)],
        [InlineKeyboardButton(text="📞 Позвонить", url=f"tel:{PHONE_NUMBER}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_guide_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Забрать гайд", url=GUIDE_LINK)],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_shortlist_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, супер!", callback_data="shortlist_yes")]
    ])

def get_rent_options_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Посмотреть варианты", url=WEEKLY_POST_LINK)]
    ])

def get_tax_guide_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Читать инструкцию", url=GUIDE_LINK)]
    ])

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Горячие предложения", callback_data="promo_list")],
        [InlineKeyboardButton(text="🏠 Подобрать объект", callback_data="continue")],
        [InlineKeyboardButton(text="🧮 Калькулятор ипотеки", callback_data="mortgage")],
        [InlineKeyboardButton(text="🏢 Квартиры недели", url=WEEKLY_POST_LINK)],
        [InlineKeyboardButton(text="📞 Бесплатная консультация", callback_data="consultation")]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ Добавить промо", callback_data="admin_add_promo")],
        [InlineKeyboardButton(text="📋 Клиенты", callback_data="admin_clients")],
        [InlineKeyboardButton(text="🔥 Горячие клиенты", callback_data="admin_hot_clients")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

# === КЛАВИАТУРА ПОД ВВОДНОЙ СТРОКОЙ ===
main_menu_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Главное меню")],
        [KeyboardButton(text="🔄 Перезапустить")],
        [KeyboardButton(text="👑 Админ-панель")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)