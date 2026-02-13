import logging
import asyncio
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '7627481814:AAHhAlr07yJQ7y9vWVY4VK5e5nfEI94Cd1M'
ADMIN_ID = 529579637
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
        current_url = f"{BASE_SHEET_URL}&cache={pd.Timestamp.now().timestamp()}"
        df = pd.read_csv(current_url)
        df.columns = df.columns.str.strip()
        
        # To'liq moslikni tekshirish
        user_res = df[df['Ism-familiya'].astype(str).str.strip().str.lower() == full_name.strip().lower()]
        
        if user_res.empty:
            # Qisman qidirish
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
        "Assalomu alaykum! 🎓\n\nSertifikat olish uchun testda qatnashgan **Ism-familiyangizni** yuboring."
    )

# --- 1. ADMIN REPLY (Sertifikat yuborish) ---
# Faqat Admin reply qilganda ishlaydi
@dp.message(F.reply_to_message & (F.from_user.id == ADMIN_ID))
async def admin_reply_handler(message: types.Message):
    try:
        orig_text = message.reply_to_message.text or message.reply_to_message.caption
        if orig_text and "🆔 Telegram ID:" in orig_text:
            student_id = int(orig_text.split("🆔 Telegram ID: `")[1].split("`")[0])
            await bot.copy_message(
                chat_id=student_id,
                from_chat_id=ADMIN_ID,
                message_id=message.message_id
            )
            await message.answer("✅ Sertifikat o'quvchiga yuborildi!")
        else:
            await message.answer("❌ Bu xabarda ID topilmadi. Ism yozgan bo'lsangiz, natijani qidirish uchun reply qilmasdan yozing.")
    except Exception as e:
        logging.error(f"Xato: {e}")
        await message.answer(f"⚠️ Xatolik: {e}")

# --- 2. NATIJA QIDIRISH (Hamma uchun, shu jumladan Admin uchun ham) ---
# Faqat reply bo'lmagan oddiy matnli xabarlarni qabul qiladi
@dp.message(F.text & ~F.reply_to_message)
async def handle_all_messages(message: types.Message):
    student_input = message.text.strip()
    wait_msg = await message.answer("🔍 Natija tekshirilmoqda...")
    
    result = check_results(student_input)
    
    if result == "error":
        await wait_msg.edit_text("❌ Jadval o'qishda xato yuz berdi.")
        return

    # Admin xabari tayyorlanmoqda
    admin_info = (
        f"🔔 **Yangi murojaat!**\n"
        f"👤 **Ism:** {student_input}\n"
        f"🆔 Telegram ID: `{message.from_user.id}`\n"
    )
    
    if result is not None:
        found_info = (
            f"\n📊 **Natija topildi:**\n"
            f"🔹 Ism: {result.get('Ism-familiya', 'Noma`lum')}\n"
            f"🔹 Fan: {result.get('Fan', 'Noma`lum')}\n"
            f"🔹 Ball: {result.get('Ball (%)', '0%')}\n"
        )
        await wait_msg.edit_text(f"✅ Natija topildi!{found_info}")
        
        # Agar yozgan odam Admin bo'lmasa, Adminga hisobot yuboramiz
        if message.from_user.id != ADMIN_ID:
            await bot.send_message(ADMIN_ID, admin_info + found_info + "\n👉 Sertifikat yuborish uchun reply qiling.", parse_mode="Markdown")
    else:
        await wait_msg.edit_text("⚠️ Bazadan topilmadi. Ismni to'g'ri yozganingizga ishonch hosil qiling.")
        if message.from_user.id != ADMIN_ID:
            await bot.send_message(ADMIN_ID, admin_info + "\n⚠️ Bu ism bazada yo'q.", parse_mode="Markdown")

# --- ASOSIY LOOP ---
async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logging.info(f"🚀 Bot ishga tushdi! Port: {port}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
