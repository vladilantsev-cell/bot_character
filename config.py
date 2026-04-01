import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
CHANNEL_ID = os.getenv("CHANNEL_ID")
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/smllr")
WEEKLY_POST_LINK = os.getenv("WEEKLY_POST_LINK", "https://t.me/ваш_канал/пост")
GUIDE_LINK = os.getenv("GUIDE_LINK", "https://disk.yandex.ru/i/NNqm36NBAVEJpQ")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "+78001234567")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан!")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL или SUPABASE_KEY не заданы!")

print("✅ Все переменные окружения загружены")