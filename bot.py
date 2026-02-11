import logging
import asyncio
import io
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from PIL import Image, ImageDraw, ImageFont

# --- SOZLAMALAR ---
# Xavfsizlik uchun Tokenni serverning Environment Variables qismiga qo'yish tavsiya etiladi
API_TOKEN = '7627481814:AAHhAlr07yJQ7y9vWVY4VK5e5nfEI94Cd1M'
ADMIN_ID = 529579637 

# Google Sheets CSV eksport havolasi
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/gviz/tq?tqx=out:csv&sheet=Results"

# Fayllar yo'lini aniqlash (GitHub/Serverda xato bermasligi uchun)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_IMAGE = os.path.join(BASE_DIR, "Blue and Gold Classy Appreciation Certificate.jpg")
FONT_FILE = os.path.join(BASE_DIR, "Montserrat-Italic-VariableFont_wght.ttf")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def create_cert(name, subject, score):
    try:
        img = Image.open(CERT_IMAGE)
        draw = ImageDraw.Draw(img)
        
        try:
            font_name = ImageFont.truetype(FONT_FILE, 55)
            font_info = ImageFont.truetype(FONT_FILE, 30)
        except:
            logging.warning("Shrift yuklanmadi, standart ishlatiladi")
            font_name = ImageFont.load_default()
            font_info = ImageFont.load_default()

        text_color = "#1a3a5a"
        # Koordinatalar (Rasm o'lchamiga qarab biroz o'zgarishi mumkin)
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
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        # Ism-familiya ustunidan qidirish
        user_res = df[df['Ism-familiya'].astype(str).str.contains(full_name, case=False, na=False)]
        return user_res.iloc[-1] if not user_res.empty else None
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
    
    if result == "error":
        await msg.edit_text("⚠️ Bazaga ulanib bo'lmadi. Jadval ruxsatini tekshiring.")
    elif result is not None:
        try:
            score = float(str(result["Ball (%)"]).replace('%', '').strip())
            if score >= 80:
                await msg.edit_text("✅ Natija topildi! Sertifikat tayyorlanmoqda...")
                cert = create_cert(result["Ism-familiya"], result["Fan"], score)
                if cert:
                    photo = types.BufferedInputFile(cert.read(), filename="sertifikat.jpg")
                    await message.answer_photo(photo, caption=f"Tabriklaymiz, {result['Ism-familiya']}!")
            else:
                await msg.edit_text(f"😕 Ballingiz: {score}%. Sertifikat uchun kamida 80% kerak.")
        except Exception as e:
            await msg.edit_text("❌ Ma'lumotni o'qishda xatolik.")
    else:
        await msg.edit_text("❌ Ismingiz bazadan topilmadi.")

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
