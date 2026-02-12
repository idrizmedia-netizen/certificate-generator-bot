import logging
import asyncio
import io
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '7627481814:AAHhAlr07yJQ7y9vWVY4VK5e5nfEI94Cd1M'
ADMIN_ID = 529579637  # 👈 BU YERGA O'ZINGIZNING TELEGRAM ID-INGIZNI YOZING
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/gviz/tq?tqx=out:csv&sheet=Results"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Fayllar mavjudligini tekshirish uchun (ixtiyoriy)
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- RENDER PORT UCHUN ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

def check_results(full_name):
    try:
        # Jadvalni o'qish
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        # To'liq mos kelishini tekshirish (aniqroq bo'lishi uchun)
        user_res = df[df['Ism-familiya'].astype(str).str.contains(full_name, case=False, na=False)]
        
        if user_res.empty:
            return None
        return user_res.iloc[-1]
    except Exception as e:
        logging.error(f"Jadval xatosi: {e}")
        return "error"

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(f"Assalomu alaykum! 🎓\nNatijangizni bilish uchun testda qatnashgan **Ism-familiyangizni** yuboring.")

@dp.message(F.text)
async def handle_message(message: types.Message):
    name_query = message.text.strip()
    msg = await message.answer("🔍 Natijangiz qidirilmoqda...")
    
    result = check_results(name_query)
    
    if isinstance(result, str) and result == "error":
        await msg.edit_text("⚠️ Bazaga ulanib bo'lmadi.")
    elif result is not None:
        try:
            score_val = result["Ball (%)"]
            score = float(str(score_val).replace('%', '').strip())
            f_name = result["Ism-familiya"]
            subject = result["Fan"]

            if score >= 80:
                # Tugma yaratish
                builder = InlineKeyboardBuilder()
                # Tugma ichiga ma'lumotlarni yashirincha joylaymiz
                builder.row(types.InlineKeyboardButton(
                    text="📜 Sertifikatni olish", 
                    callback_data=f"get_cert:{score}")
                )
                
                await msg.edit_text(
                    f"✅ Natija topildi!\n👤 Ism: {f_name}\n📚 Fan: {subject}\n📊 Ball: {score}%\n\n"
                    f"Sertifikat olish uchun quyidagi tugmani bosing:",
                    reply_markup=builder.as_markup()
                )
            else:
                await msg.edit_text(f"😕 Ballingiz: {score}%. Sertifikat olish uchun kamida 80% kerak.")
        except Exception as e:
            await msg.edit_text("❌ Ma'lumotni o'qishda xatolik.")
    else:
        await msg.edit_text("❌ Ismingiz bazadan topilmadi. Iltimos, ism-familiyani to'g'ri yozganingizga ishonch hosil qiling.")

# --- TUGMA BOSILGANDA ---
@dp.callback_query(F.data.startswith("get_cert:"))
async def process_cert_request(callback: types.CallbackQuery):
    score = callback.data.split(":")[1]
    user = callback.from_user
    
    # 1. O'quvchiga xabar
    await callback.message.edit_text("⏳ So'rovingiz adminga yuborildi. Tez orada sertifikatingizni olasiz!")
    
    # 2. Sizga (Adminga) xabar yuborish
    admin_text = (
        f"🔔 **Yangi sertifikat so'rovi!**\n\n"
        f"👤 O'quvchi: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📝 Telegram username: @{user.username}\n"
        f"📊 Balli: {score}%\n"
        f"💬 Xabar: *Menga sertifikat bering*"
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        await callback.answer("So'rov yuborildi!")
    except Exception as e:
        logging.error(f"Adminga yuborishda xato: {e}")
        await callback.answer("Xatolik yuz berdi, keyinroq urining.")

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
