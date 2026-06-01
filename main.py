import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# 1. BOT TOKENINGNI SHU YERGA YOZ
BOT_TOKEN = ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Musiqani yuklash funksiyasi
def get_audio_url(search_query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_query, download=False)
            video = info['entries'][0]
            return video['url'], video['title']
        except:
            return None, None
8853912401:AAEvwDxh-xw0vJY1pT_c-KEVwfGQ4lUkodw
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Salom! Qo'shiq nomini yozing, men uni topib beraman 🎵")

@dp.message()
async def search_music(message: types.Message):
    wait_msg = await message.answer("🔍 Qidirilmoqda...")
    
    loop = asyncio.get_event_loop()
    url, title = await loop.run_in_executor(None, get_audio_url, message.text)
    
    if url:
        try:
            await message.answer_audio(audio=url, title=title, caption="Marhamat! 🎧")
            await wait_msg.delete()
        except:
            await wait_msg.edit_text("Yuborishda xatolik bo'ldi.")
    else:
        await wait_msg.edit_text("Topilmadi 😔")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(asyncio.run(main()))
