import logging
import asyncio
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '7627481814:AAHhAlr07yJQ7y9vWVY4VK5e5nfEI94Cd1M'
ADMIN_ID = 529579637  # Sizning ID-ingiz
# Google Sheets URL (Keshni chetlab o'tish uchun vaqt belgisi qo'shiladi)
BASE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/gviz/tq?tqx=out:csv&sheet=Results"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- RENDER UCHUN WEB SERVER ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

# --- JADVALDAN NATIJANI QIDIRISH ---
def check_results(full_name):
    try:
        # Har safar yangi ma'lumot olish uchun URL oxiriga tasodifiy son qo'shamiz
        current_url = f"{BASE_SHEET_URL}&cache={pd.Timestamp.now().timestamp()}"
        df = pd.read_csv(current_url)
        
        # Ustun nomlaridagi bo'shliqlarni tozalash
        df.columns = df.columns.str.strip()
        
        # Qidiruv (ismni kichik harflarda solishtirish)
        user_res = df[df['Ism-familiya'].astype(str).str.strip().str.lower() == full_name.strip().lower()]
        
        if user_res.empty:
            # Agar to'liq mos kelmasa, qisman qidirish
            user_res = df[df['Ism-familiya'].astype(str).str.contains(full_name, case=False, na=False)]
            
        if user_res.empty:
            return None
            
        return user_res.iloc[-1]
    except Exception as e:
        logging.error(f"Jadval o'qishda xatolik: {e}")
        return "error"

# --- START BUYRUG'I ---
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "Assalomu alaykum! 🎓\n\nSertifikat olish uchun testda qatnashgan **Ism-familiyangizni** yuboring.\n"
        "Men natijangizni tekshirib, adminga so'rov yuboraman."
    )

# --- 1. ADMIN REPLY (Sertifikatni o'quvchiga qaytarish) ---
@dp.message(F.reply_to_message & (F.from_user.id == ADMIN_ID))
async def admin_reply_handler(message: types.Message):
    try:
        orig_text = message.reply_to_message.text or message.reply_to_message.caption
        if orig_text and "🆔 Telegram ID:" in orig_text:
            # ID ni xabardan ajratib olish
            student_id = int(orig_text.split("🆔 Telegram ID: `")[1].split("`")[0])
            
            # Admindan kelgan xabarni o'quvchiga nusxalash
            await bot.copy_message(
                chat_id=student_id,
                from_chat_id=ADMIN_ID,
                message_id=message.message_id
            )
            await message.answer("✅ Xabar o'quvchiga muvaffaqiyatli yuborildi!")
        else:
            await message.answer("❌ Bu xabarda foydalanuvchi ID-si topilmadi.")
    except Exception as e:
        logging.error(f"Sertifikat yuborishda xato: {e}")
        await message.answer(f"⚠️ Xatolik: {e}")

# --- 2. O'QUVCHI XABARI ---
@dp.message(F.text & (F.from_user.id != ADMIN_ID))
async def handle_student(message: types.Message):
    student_input = message.text.strip()
    wait_msg = await message.answer("🔍 Natijangiz tekshirilmoqda, iltimos kuting...")
    
    result = check_results(student_input)
    
    if result == "error":
        await wait_msg.edit_text("❌ Tizimda texnik xatolik yuz berdi. Birozdan so'ng urinib ko'ring.")
        return

    admin_msg = (
        f"🔔 **Yangi murojaat!**\n\n"
        f"👤 **O'quvchi yozgan ism:** {student_input}\n"
        f"🆔 Telegram ID: `{message.from_user.id}`\n"
        f"🔗 Profil: @{message.from_user.username if message.from_user.username else 'yo`q'}\n"
    )
    
    if result is not None:
        # Jadvalingizdagi ustun nomlariga mos ravishda ma'lumot olish
        admin_msg += (
            f"\n📊 **Natija topildi:**\n"
            f"🔹 Ism: {result.get('Ism-familiya', 'Noma`lum')}\n"
            f"🔹 Fan: {result.get('Fan', 'Noma`lum')}\n"
            f"🔹 Ball: {result.get('Ball (%)', '0%')}\n\n"
            f"👉 *Ushbu xabarga 'reply' qilib sertifikatni yuboring.*"
        )
        await wait_msg.edit_text("✅ Natijangiz topildi va adminga yuborildi. Sertifikat tayyor bo'lishini kuting.")
    else:
        admin_msg += "\n⚠️ *Bu ism bazadan topilmadi.*"
        await wait_msg.edit_text("⚠️ Ismingiz bazadan topilmadi. Ism-familiyani to'g'ri yozganingizni tekshiring.")

    # Adminga xabarni yetkazish
    try:
        await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Adminga xabar yuborishda xato: {e}")

# --- ASOSIY LOOP ---
async def main():
    # Web serverni ishga tushirish (Render uchun)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logging.info(f"🚀 Bot ishga tushdi! Port: {port}")
    
    # Eski xabarlarni tozalash va pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
