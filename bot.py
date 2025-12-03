import random
import string
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = "8408011643:AAEbATOF3eldawdXyA5WCoTKqaCXafuoDXA"
TARGET_CHAT_ID = -1002524076661   # chat_id твоей группы с МИНУСОМ!
ADMIN_IDS = [516469420]        # твой user_id, без кавычек

CODES_FILE = "codes.json"

def load_codes():
    try:
        with open(CODES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_codes(codes):
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f)

def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def is_user_in_chat(bot, user_id):
    try:
        member = bot.get_chat_member(TARGET_CHAT_ID, user_id)
        print(f"Проверка пользователя {user_id}, статус: {member.status}")
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"Ошибка get_chat_member: {e}")
        return False

def getcode(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    codes = load_codes()

    # Информационный вывод в консоль для диагностики:
    print(f"Запрос кода. user_id: {user_id}, username: {username}")

    if is_user_in_chat(context.bot, user_id):
        if str(user_id) in codes:
            code = codes[str(user_id)]["code"]
            update.message.reply_text(f"Ваш код уже был выдан раньше: {code}")
        else:
            code = generate_code()
            codes[str(user_id)] = {"code": code, "username": username}
            save_codes(codes)
            update.message.reply_text(f"Ваш уникальный код: {code}")
    else:
        update.message.reply_text("Вы не состоите в нужном чате или канале.")
        print(f"Пользователь {user_id} не найден в группе!")

def codes_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("Нет доступа.")
        return

    codes = load_codes()
    if not codes:
        update.message.reply_text("Кодов еще не выдано.")
        return

    text = "Список выданных кодов:\n"
    for uid, info in codes.items():
        line = f"- @{info['username'] if info['username'] else uid}: {info['code']}"
        text += line + "\n"
    update.message.reply_text(text)

# Диагностическая команда chatid
def chatid(update: Update, context: CallbackContext):
    update.message.reply_text(
        f"chat_id этого чата: {update.effective_chat.id}\n"
        f"Ваш user_id: {update.effective_user.id}"
    )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('getcode', getcode))
    dp.add_handler(CommandHandler('codes', codes_command))
    dp.add_handler(CommandHandler('chatid', chatid))
    updater.start_polling()
    print("Бот запущен! Нажмите Ctrl+C для остановки...")
    updater.idle()

if __name__ == "__main__":
    main()
