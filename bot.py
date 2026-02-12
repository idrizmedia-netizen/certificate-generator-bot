import logging
import asyncio
import io
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web  # Render port xatosi uchun

# --- SOZLAMALAR ---
API_TOKEN = '7627481814:AAHhAlr07yJQ7y9vWVY4VK5e5nfEI94Cd1M'
# Google Sheets CSV eksport havolasi
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/gviz/tq?tqx=out:csv&sheet=Results"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_IMAGE = os.path.join(BASE_DIR, "Blue and Gold Classy Appreciation Certificate.jpg")
FONT_FILE = os.path.join(BASE_DIR, "Montserrat-Italic-VariableFont_wght.ttf")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- RENDER PORT UCHUN ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

def create_cert(name, subject, score):
    try:
        img = Image.open(CERT_IMAGE)
        draw = ImageDraw.Draw(img)
        
        try:
            font_name = ImageFont.truetype(FONT_FILE, 55)
            font_info = ImageFont.truetype(FONT_FILE, 30)
        except:
            font_name = ImageFont.load_default()
            font_info = ImageFont.load_default()

        text_color = "#1a3a5a"
        draw.text((1020, 480), f"{name}", fill=text_color, font=font_name, anchor="ms")
        draw.text((430, 605), f"{subject}", fill=text_color, font=font_info, anchor="ls")
        draw.text((600, 635), f"{score}%", fill=text_color, font=font_info, anchor="ls")

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception as e:
        logging.error(f"Sertifikat yasashda xato: {e}")
        return None

def check_results(full_name):
    try:
        # Keshni yangilab turish uchun URL ga o'zgartirish kiritamiz
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        user_res = df[df['Ism-familiya'].astype(str).str.contains(full_name, case=False, na=False)]
        
        if user_res.empty:
            return None
        return user_res.iloc[-1]
    except Exception as e:
        logging.error(f"Jadval xatosi: {e}")
        return "error"

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(f"Assalomu alaykum! 🎓\nSertifikat olish uchun testda qatnashgan **Ism-familiyangizni** yuboring.")

@dp.message()
async def handle_message(message: types.Message):
    name_query = message.text.strip()
    msg = await message.answer("🔍 Natijangiz qidirilmoqda...")
    
    result = check_results(name_query)
    
    # MUHIM: Pandas Series-ni string bilan to'g'ri solishtirish
    if isinstance(result, str) and result == "error":
        await msg.edit_text("⚠️ Bazaga ulanib bo'lmadi. Jadval ruxsatini tekshiring.")
    elif result is not None:
        try:
            score_val = result["Ball (%)"]
            score = float(str(score_val).replace('%', '').strip())
            
            if score >= 80:
                await msg.edit_text("✅ Natija topildi! Sertifikat tayyorlanmoqda...")
                cert = create_cert(result["Ism-familiya"], result["Fan"], score)
                if cert:
                    photo = types.BufferedInputFile(cert.read(), filename="sertifikat.jpg")
                    await message.answer_photo(photo, caption=f"Tabriklaymiz, {result['Ism-familiya']}!")
            else:
                await msg.edit_text(f"😕 Ballingiz: {score}%. Sertifikat uchun kamida 80% kerak.")
        except Exception as e:
            logging.error(f"Xatolik: {e}")
            await msg.edit_text("❌ Ma'lumotni o'qishda xatolik.")
    else:
        await msg.edit_text("❌ Ismingiz bazadan topilmadi.")

async def main():
    # Render-da portni band qilish (Timeout xatosini oldini oladi)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Bot ishga tushdi... Port: {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
