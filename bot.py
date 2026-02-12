import logging
import asyncio
import io
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '7627481814:AAHhAlr07yJQ7y9vWVY4VK5e5nfEI94Cd1M'
ADMIN_ID = 529579637  # Sizning ID-ingiz
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/gviz/tq?tqx=out:csv&sheet=Results"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- RENDER UCHUN PORT ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

# --- NATIJANI TEKSHIRISH ---
def check_results(full_name):
    try:
        # Keshni chetlab o'tish uchun vaqt qo'shish ixtiyoriy
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
        "Men natijangizni tekshirib, adminga xabar beraman."
    )

# --- XABARLARNI QABUL QILISH ---
@dp.message(F.text)
async def handle_student_message(message: types.Message):
    student_name = message.text.strip()
    
    # 1. O'quvchiga javob
    wait_msg = await message.answer("🔍 Natijangiz tekshirilmoqda, iltimos kuting...")
    
    # 2. Jadvaldan qidirish
    result = check_results(student_name)
    
    status_text = ""
    if result is None:
        status_text = "❌ Bu ism bazadan topilmadi (lekin xabaringiz adminga yuborildi)."
    elif isinstance(result, str) and result == "error":
        status_text = "⚠️ Tizimda vaqtinchalik uzilish (xabaringiz adminga yuborildi)."
    else:
        score = result["Ball (%)"]
        subject = result["Fan"]
        real_name = result["Ism-familiya"]
        status_text = f"✅ Natijangiz topildi!\n👤 Ism: {real_name}\n📚 Fan: {subject}\n📊 Ball: {score}\n\n⏳ Adminga xabar yuborildi. Tez orada javob olasiz."

    await wait_msg.edit_text(status_text)

    # 3. ADMINGA (SIZGA) XABAR YUBORISH
    # O'quvchi test ishlagan bo'lsa natijasi bilan, ishlamagan bo'lsa shunchaki ismi bilan boradi
    admin_info = (
        f"📩 **Yangi murojaat!**\n\n"
        f"👤 **O'quvchi yozdi:** {student_name}\n"
        f"🆔 **ID:** `{message.from_user.id}`\n"
        f"🔗 **Username:** @{message.from_user.username}\n"
    )
    
    if not isinstance(result, str) and result is not None:
        admin_info += (
            f"\n📊 **Test natijasi:**\n"
            f"🔹 Ism: {result['Ism-familiya']}\n"
            f"🔹 Fan: {result['Fan']}\n"
            f"🔹 Ball: {result['Ball (%)']}"
        )
    else:
        admin_info += "\n⚠️ *Bu foydalanuvchi bazadan topilmadi.*"

    # Adminga yuborish (Sertifikat bering deb yozish shartmas, avtomatik boradi)
    await bot.send_message(ADMIN_ID, admin_info, parse_mode="Markdown")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    # Render portini band qilish
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logging.info(f"Bot ishga tushdi! Port: {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
