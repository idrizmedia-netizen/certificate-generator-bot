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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/gviz/tq?tqx=out:csv&sheet=Results"

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
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        user_res = df[df['Ism-familiya'].astype(str).str.contains(full_name, case=False, na=False)]
        if user_res.empty:
            return None
        return user_res.iloc[-1]
    except Exception as e:
        logging.error(f"Jadval xatosi: {e}")
        return "error"

# --- START BUYRUG'I ---
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "Assalomu alaykum! 🎓\n\nSertifikat olish uchun testda qatnashgan **Ism-familiyangizni** yuboring. "
        "Adminga so'rov yuboriladi va tez orada sertifikatingizni olasiz."
    )

# --- 1. ADMIN REPLY (Siz o'quvchiga javob yozganingizda) ---
@dp.message(F.reply_to_message & (F.from_user.id == ADMIN_ID))
async def admin_reply_handler(message: types.Message):
    try:
        # Reply qilingan xabardan o'quvchi ID-sini qidirib topish
        orig_text = message.reply_to_message.text or message.reply_to_message.caption
        if "🆔 Telegram ID:" in orig_text:
            # ID ni qirqib olish
            student_id = int(orig_text.split("🆔 Telegram ID: `")[1].split("`")[0])
            
            # O'quvchiga xabarni (rasm, fayl yoki matn) yuborish
            await bot.copy_message(
                chat_id=student_id,
                from_chat_id=ADMIN_ID,
                message_id=message.message_id
            )
            await message.answer("✅ Xabaringiz o'quvchiga yetkazildi!")
        else:
            await message.answer("❌ Xatolik: Bu xabarda o'quvchi ID-si topilmadi.")
    except Exception as e:
        logging.error(f"Reply xatosi: {e}")
        await message.answer("⚠️ O'quvchiga yuborishda xatolik yuz berdi.")

# --- 2. O'QUVCHI XABARI (O'quvchi ismini yozganda) ---
@dp.message(F.text & (F.from_user.id != ADMIN_ID))
async def handle_student(message: types.Message):
    student_input = message.text.strip()
    await message.answer("🔍 Natijangiz tekshirilmoqda va adminga yuborilmoqda. Iltimos, kutib turing...")
    
    result = check_results(student_input)
    
    admin_msg = (
        f"🔔 **Yangi murojaat!**\n\n"
        f"👤 **O'quvchi yozgan ism:** {student_input}\n"
        f"🆔 Telegram ID: `{message.from_user.id}`\n"
        f"🔗 Profil: @{message.from_user.username if message.from_user.username else 'yo`q'}\n"
    )
    
    if result is not None and not isinstance(result, str):
        admin_msg += (
            f"\n📊 **Natijasi:**\n"
            f"🔹 Ism: {result['Ism-familiya']}\n"
            f"🔹 Fan: {result['Fan']}\n"
            f"🔹 Ball: {result['Ball (%)']}\n\n"
            f"👉 *Ushbu xabarga reply qilib sertifikatni yuboring.*"
        )
    else:
        admin_msg += "\n⚠️ *Bu ism bazadan topilmadi.*"

    await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

# --- ASOSIY LOOP ---
async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
