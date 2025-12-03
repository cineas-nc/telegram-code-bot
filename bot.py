import logging
import json
import aiohttp
from aiogram import Bot, Dispatcher, executor, types

# ---- Вставь свой API token бота и id группы ----
API_TOKEN = 'ВСТАВЬ_ТВОЙ_ТЕЛЕГРАМ_BOT_TOKEN'
TELEGRAM_GROUP_ID = -1001234567890   # <-- сюда id твоей группы с минусом впереди

# ---- Твои ключи от Zoom Marketplace ----
ZOOM_ACCOUNT_ID = "KDaSi2vVRNKqPQKaqRqAzA"
ZOOM_CLIENT_ID = "mvsumRr9SyekM1MZyXvyww"
ZOOM_CLIENT_SECRET = "Ka9PKA0e2l872r3PViakZtcJSlOcR3PW"
ZOOM_MEETING_ID = "87894049408"  # <-- должен быть ЦИФРОВОЙ, например 87894049408 (ПРОВЕРЬ через Zoom)

# --- Имя файла для хранения связки user_id - join_url ---
DB_FILE = "zoom_users.json"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def load_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f)

async def get_zoom_access_token():
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ZOOM_ACCOUNT_ID}"
    headers = {
        "Authorization": "Basic " + (
            f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}"
        ).encode("ascii").decode("ascii"),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            data = await resp.json()
            return data.get("access_token")

async def check_user_in_group(user_id):
    try:
        chat_member = await bot.get_chat_member(TELEGRAM_GROUP_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print('ошибка проверки группы:', e)
        return False

async def register_on_zoom(fullname, email):
    token = await get_zoom_access_token()
    url = f"https://api.zoom.us/v2/meetings/{ZOOM_MEETING_ID}/registrants"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "first_name": fullname,
        "last_name": "",
        # Zoom не всегда использует эти параметры, но оставим для совместимости
        "auto_approve": True
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            # print(data)
            return data.get("join_url")

@dp.message_handler(commands=["zoom", "join"])
async def process_zoom(message: types.Message):
    tg_id = str(message.from_user.id)
    db = load_db()

    if tg_id in db:
        await message.reply(f"Ваша индивидуальная ссылка для Zoom:\n{db[tg_id]}\nНЕ передавайте её другим.")
        return

    # Проверка участия в группе
    in_group = await check_user_in_group(message.from_user.id)
    if not in_group:
        await message.reply("Извините, только для членов спец.чата.")
        return

    fullname = message.from_user.username or message.from_user.full_name or "TelegramUser"
    email = f"tg_{tg_id}@bot.local"
    try:
        join_url = await register_on_zoom(fullname, email)
        if join_url:
            db[tg_id] = join_url
            save_db(db)
            await message.reply(f"Ваша индивидуальная ссылка на Zoom:\n{join_url}\nНЕ передавайте её другим.")
        else:
            await message.reply("Не удалось получить ссылку Zoom. Обратитесь к админу.")
    except Exception as e:
        print(e)
        await message.reply("Ошибка регистрации в Zoom. Сообщите админу.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
