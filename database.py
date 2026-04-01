import httpx
from config import SUPABASE_URL, SUPABASE_KEY
from loguru import logger

async def supabase_request(endpoint: str, params: dict = None, method: str = "GET", data: dict = None):
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                return []

            if response.status_code not in [200, 201, 204]:
                logger.error(f"Ошибка Supabase: {response.status_code} - {response.text}")
                return []

            if response.status_code == 204:
                return []
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка запроса к Supabase: {e}")
            return []

# === ПОЛЬЗОВАТЕЛИ ===
async def save_user(user_id, username, full_name, phone=None):
    existing = await supabase_request("users", params={"user_id": f"eq.{user_id}"})
    if existing:
        await supabase_request(f"users?user_id=eq.{user_id}", method="PATCH", data={
            "username": username, "full_name": full_name, "phone": phone
        })
    else:
        await supabase_request("users", method="POST", data={
            "user_id": user_id, "username": username, "full_name": full_name,
            "phone": phone, "status": "active"
        })
    logger.info(f"Пользователь {user_id} сохранён")

async def get_all_users():
    return await supabase_request("users")

async def get_user(user_id):
    result = await supabase_request("users", params={"user_id": f"eq.{user_id}"})
    return result[0] if result else None

async def update_user_phone(user_id, phone):
    await supabase_request(f"users?user_id=eq.{user_id}", method="PATCH", data={"phone": phone})

async def update_user_shortlist(user_id, shortlist=True):
    await supabase_request(f"users?user_id=eq.{user_id}", method="PATCH", data={"shortlist": shortlist})

# === КАТАЛОГ ===
async def get_catalog_by_filters(city: str = None, purpose: str = None, layout: str = None):
    params = {}
    if city:
        params["city"] = f"eq.{city}"
    if purpose:
        params["purpose"] = f"eq.{purpose}"
    if layout:
        params["layout"] = f"eq.{layout}"
    return await supabase_request("catalog", params=params)

# === КЛИЕНТЫ ===
async def save_client_request(user_id, purpose, city=None, layout=None, phone=None, name=None):
    data = {
        "user_id": user_id,
        "purpose": purpose,
        "city": city,
        "layout": layout,
        "phone": phone,
        "name": name,
        "status": "new"
    }
    await supabase_request("clients", method="POST", data=data)
    logger.info(f"Заявка от {user_id} сохранена")

async def get_all_clients():
    return await supabase_request("clients", params={"_order": "created_at.desc"})

# === ПРОМО ===
async def get_all_promo():
    return await supabase_request("promo")

async def get_promo_by_id(promo_id):
    result = await supabase_request("promo", params={"id": f"eq.{promo_id}"})
    return result[0] if result else None

async def add_promo(name, description, price, location, image_url=None, builder=None):
    data = {
        "name": name,
        "description": description,
        "price": price,
        "location": location,
        "image_url": image_url,
        "builder": builder
    }
    await supabase_request("promo", method="POST", data=data)
    logger.info(f"Промо {name} добавлено")