from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest, Forbidden
import json

# --- Sozlamalar ---
ADMIN_ID = 7105959922 # bu yerga o'zingizning Telegram ID'ingizni yozing
BATTLE_CHANNEL = "@skromniy6"  # default battle kanali
BOOST_LINK = "https://t.me/boost/skromniy6"  # default boost silka
start_number = 1

# Ro'yxatdan o'tgan foydalanuvchilar
registered_users = []

# Talab qilinadigan kanallar ro'yxati
REQUIRED_CHANNELS = [
    ('@skromniy6', 'Kanal'),
    ('@ckromniykanal', 'Kanal'),
    ('@auric_stars', 'Kanal')
]

# Username formatini tekshirish
def is_valid_username(username: str) -> bool:
    if not username.startswith('@'):
        return False
    username_part = username[1:]
    if len(username_part) < 5 or len(username_part) > 32:
        return False
    return all(char.isalnum() or char == '_' for char in username_part)

# Inline tugmalar yasash (faqat obuna bo‘lmagan canal uchun)
def get_channel_buttons(not_subscribed_channels):
    buttons = [
        [InlineKeyboardButton(text=name, url=f"https://t.me/{channel[1:]}")]
        for channel, name in not_subscribed_channels
    ]
    return InlineKeyboardMarkup(buttons) if buttons else None

# Kanalga obuna bo‘lganligini tekshirish va obuna bo‘lmagan kanallarni qaytarish
async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    not_subscribed_channels = []
    for channel, name in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed_channels.append((channel, name))
        except (BadRequest, Forbidden):
            not_subscribed_channels.append((channel, name))
    return not_subscribed_channels

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Obuna bo‘lmagan kanallarni tekshirish
    not_subscribed_channels = await check_membership(user_id, context)

    # Agar obuna bo‘lmagan kanallar bo‘lsa
    if not_subscribed_channels:
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:\n\n"
            "✅ Obuna bo‘lib bo‘lgach, qayta /start yuboring.",
            reply_markup=get_channel_buttons(not_subscribed_channels)
        )
        return

    # Agar barcha kanallarga obuna bo‘lgan bo‘lsa
    user_first_name = update.effective_user.first_name or "Foydalanuvchi"
    await update.message.reply_text(
        f"👋 Salom {user_first_name}!\n\n"
        "📝 Iltimos, faqat o‘z @usernamengizni yuboring.\n"
        "📋 Masalan: @mening_username\n\n"
        "ℹ️ Username kamida 5 ta belgidan iborat bo‘lishi kerak."
    )

# Username qabul qilish
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BATTLE_CHANNEL, BOOST_LINK, registered_users
    if update.message is None or update.message.text is None:
        return

    user_id = update.effective_user.id
    user_username = update.effective_user.username
    text = update.message.text.strip().lower()

    # Agar admin boost linkini yuborishi kerak bo'lsa
    if user_id == ADMIN_ID and context.user_data.get("awaiting_boost_link"):
        if not text.startswith("https://t.me/boost/"):
            await update.message.reply_text("❌ Noto‘g‘ri boost silka formati! `https://t.me/boost/` bilan boshlanishi kerak.")
            return
        BOOST_LINK = text
        context.user_data["awaiting_boost_link"] = False
        await update.message.reply_text(f"✅ Boost silka saqlandi:\n{BOOST_LINK}")
        save_data()
        return

    # Oddiy foydalanuvchi uchun obuna tekshiruvi
    not_subscribed_channels = await check_membership(user_id, context)
    if not_subscribed_channels:
        await update.message.reply_text(
            "❗ Avval quyidagi kanallarga obuna bo‘ling:\n\n"
            "✅ Obuna bo‘lib bo‘lgach, qayta /start yuboring.",
            reply_markup=get_channel_buttons(not_subscribed_channels)
        )
        return

    # Username formati noto‘g‘ri
    if not is_valid_username(text):
        await update.message.reply_text(
            "❗ Noto‘g‘ri username formati!\n\n"
            "✅ To‘g‘ri format: @username\n"
            "📏 Kamida 5 ta belgi\n"
            "🔤 Faqat harf, raqam va _ belgisi ishlatiladi\n\n"
            "📋 Masalan: @user123"
        )
        return

    # Profilida username yo‘q yoki boshqa odamni username sini kiritdi
    if user_username is None or text != f"@{user_username.lower()}":
        suggested = f"@{user_username}" if user_username else "sizning usernamengiz yo‘q"
        await update.message.reply_text(
            f"❌ Bu sizning usernamengiz emas!\n\n"
            f"💡 Sizning usernamengiz: {suggested}\n"
            "ℹ️ Iltimos, faqat o‘z username’ingizni yuboring."
        )
        return

    # Allaqachon ro‘yxatdan o‘tganmi?
    if text in registered_users:
        await update.message.reply_text("⚠️ Bu username allaqachon ro‘yxatga olingan.")
        return

    # Ro‘yxatga qo‘shish
    registered_users.append(text)
    position = start_number + len(registered_users) - 1

    message = f"""🎯 Stars battle uchun ro'yxatdan o'tdingiz! 🎉  
{position}⃣ – {text}
⭐️ Stars – 5 ball  
👍 Reaksiya – 1 ball  
🚀 Boost – 15 ball
{BOOST_LINK}"""

    try:
        await context.bot.send_message(chat_id=BATTLE_CHANNEL, text=message)
        await update.message.reply_text(
            f"✅ Username muvaffaqiyatli ro'yxatga olindi!\n"
            f"📊 Sizning raqamingiz: {position}\n"
            f"📢 Xabar {BATTLE_CHANNEL} kanaliga yuborildi."
        )
        save_data()
    except Exception as e:
        registered_users.remove(text)
        await update.message.reply_text(f"❗ Kanalga xabar yuborishda xatolik: {e}")

# Admin battle kanalini o‘zgartirishi
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BATTLE_CHANNEL
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz bu buyruqni ishlata olmaysiz.")
        return

    if len(context.args) != 1 or not context.args[0].startswith('@'):
        await update.message.reply_text("ℹ️ To‘g‘ri format: /setchannel @kanal")
        return

    BATTLE_CHANNEL = context.args[0]
    await update.message.reply_text(
        f"✅ Battle kanali {BATTLE_CHANNEL} ga o‘zgartirildi.\n"
        "📌 Endi boost kanali silkasini yuboring:"
    )
    context.user_data["awaiting_boost_link"] = True
    save_data()

# Admin uchun /setstart komandasi
async def set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global start_number
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("ℹ️ To‘g‘ri format: /setstart 10")
        return
    start_number = int(context.args[0])
    save_data()
    await update.message.reply_text(f"✅ Boshlanish raqami {start_number} qilib o‘rnatildi.")

# /about komandasi
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📢 Hozirgi battle kanali: {BATTLE_CHANNEL}\n"
        f"🚀 Boost silka: {BOOST_LINK}"
    )

# /parti komandasi (faqat admin)
async def parti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return

    if not registered_users:
        await update.message.reply_text("📋 Ro'yxat bo'sh.")
        return

    text = f"📢 {BATTLE_CHANNEL}\n" + "\n".join(f"{start_number + i}⃣ – {username}" for i, username in enumerate(registered_users))
    await update.message.reply_text(text)

# /clear komandasi (faqat admin)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global registered_users, start_number
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return

    registered_users.clear()
    start_number = 1  # start_number ni 1 ga qaytarish
    save_data()
    await update.message.reply_text("✅ Tozalandi. Boshlanish raqami 1 ga o'rnatildi.")

def load_data():
    global registered_users, start_number, BATTLE_CHANNEL, BOOST_LINK
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            registered_users = data.get('users', [])
            start_number = data.get('start_number', 1)
            BATTLE_CHANNEL = data.get('battle_channel', '@skromniy6')
            BOOST_LINK = data.get('boost_link', 'https://t.me/boost/skromniy6')
    except FileNotFoundError:
        pass

def save_data():
    data = {
        'users': registered_users,
        'start_number': start_number,
        'battle_channel': BATTLE_CHANNEL,
        'boost_link': BOOST_LINK
    }
    with open('data.json', 'w') as f:
        json.dump(data, f)

# Botni ishga tushirish
def main():
    load_data()
    TOKEN = "7464929521:AAENK_53jmZdbxPwZpVbc0OAnj4j7jLOiLM"
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setchannel", set_channel))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("parti", parti))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("setstart", set_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    print("🤖 Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Bot to‘xtatildi")
    except Exception as e:
        print(f"Xatolik: {e}")
