from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# === ГЛАВНОЕ МЕНЮ (под вводной строкой) ===
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Главное меню")],
        [KeyboardButton(text="🔄 Перезапустить")],
        [KeyboardButton(text="ℹ️ Информация")],
        [KeyboardButton(text="📞 Бесплатная консультация")]
    ],
    resize_keyboard=True
)

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
        [InlineKeyboardButton(text="📱 Отправить номер", callback_data="send_phone", request_contact=True)]
    ])

def get_consultation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в Telegram", url="https://t.me/smllr")],
        [InlineKeyboardButton(text="📞 Позвонить", url="tel:+78001234567")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_after_consult_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Квартиры недели", url=WEEKLY_POST_LINK)],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_promo_keyboard(promo_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Узнать подробнее", callback_data=f"promo_detail_{promo_id}")],
        [InlineKeyboardButton(text="📞 Консультация", callback_data=f"consult_{promo_id}")]
    ])

def get_info_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Горячие предложения", callback_data="promo_list")],
        [InlineKeyboardButton(text="🏠 Подобрать объект", callback_data="continue")],
        [InlineKeyboardButton(text="🧮 Калькулятор ипотеки", callback_data="mortgage")],
        [InlineKeyboardButton(text="🏢 Квартиры недели", url=WEEKLY_POST_LINK)],
        [InlineKeyboardButton(text="📞 Бесплатная консультация", callback_data="consultation")]
    ])

def get_after_catalog_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, подобрать 3 варианта", callback_data="budget_yes")],
        [InlineKeyboardButton(text="⏰ Позже", callback_data="budget_no")]
    ])