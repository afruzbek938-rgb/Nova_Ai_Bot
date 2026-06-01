import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# 🟢 BOT TOKEN (O'zingiznikini qo'ying)
BOT_TOKEN = "8853912401:AAEvwDxh-xw0vJY1pT_c-KEVwfGQ4lUkodw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_languages = {}

async def startup_server():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

def get_lang_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha")
    builder.button(text="🇷🇺 Русский")
    return builder.as_markup(resize_keyboard=True)

# 🎵 Internetdan qo'shiq qidirish va o'xshashlarini (Tavsiyalarni) topish funksiyasi
def search_and_recommend(query):
    # Qidirilganda birdaniga 4 ta natija olamiz (1 tasi asosiy, 3 tasi tavsiya)
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch4', 
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                results = []
                for entry in info['entries']:
                    results.append({
                        'url': entry.get('url'),
                        'title': entry.get('title'),
                    })
                return results # Birinchi element asosiy, qolganlari tavsiyalar
        except Exception as e:
            print(f"Search Error: {e}")
    return None

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🇺🇿 Iltimos, tilni tanlang:\n🇷🇺 Пожалуйста, выберите язык:",
        reply_markup=get_lang_keyboard()
    )

@dp.message()
async def handle_everything(message: types.Message):
    user_text = message.text
    user_id = message.from_user.id

    if not user_text:
        return

    if user_text == "🇺🇿 O'zbekcha":
        user_languages[user_id] = "uz"
        await message.answer("O'zbek tili tanlandi! Menga qo'shiqchi yoki tarona nomini yuboring! 🎧")
        return
    elif user_text == "🇷🇺 Русский":
        user_languages[user_id] = "ru"
        await message.answer("Выбран русский язык! Отправьте мне название песни или артиста! 🎧")
        return

    lang = user_languages.get(user_id, "uz")
    is_ru = lang == "ru"

    # AI va Video linklar olib tashlandi, faqat toza musiqa matnli qidiruv ishlaydi
    loading_text = "🔍 Музыка извлекается..." if is_ru else "🔍 Musiqa qidirilmoqda..."
    msg = await message.answer(loading_text)
    
    loop = asyncio.get_event_loop()
    # Qo'shiqni aniqroq audio variantini topish uchun kalit so'z qo'shamiz
    search_results = await loop.run_in_executor(None, search_and_recommend, f"{user_text} audio qo'shiq")

    if search_results:
        # 1. Asosiy so'ralgan qo'shiq (birinchi chiqqani)
        main_track = search_results[0]
        
        # 2. Qolgan 3 ta qo'shiqni tavsiya tugmalari qilib tayyorlaymiz
        builder = InlineKeyboardBuilder()
        for track in search_results[1:]:
            # Tugma bosilganda o'sha qo'shiq nomini shundoq botga qayta matn qilib yuboradi
            short_title = track['title'][:30] + "..." if len(track['title']) > 30 else track['title']
            builder.button(text=f"🎵 {short_title}", callback_data=f"search_{short_title}")
        builder.adjust(1) # Tugmalarni qatorasiga chiroyli joylash

        try:
            # Musiqani yuborish
            caption_text = "Mana, siz so'ragan musiqa! 🎧\n\n👇 Bular ham sizga yoqishi mumkin:" if not is_ru else "Вот ваша музыка! 🎧\n\n👇 Вам также может понравиться:"
            await message.answer_audio(
                audio=main_track['url'],
                title=main_track['title'],
                performer="NOVA Music",
                caption=caption_text,
                reply_markup=builder.as_markup()
            )
            await msg.delete()
        except Exception as e:
            await message.answer("Musiqani yuborishda xatolik bo'ldi." if not is_ru else "Ошибка при отправке аудио.")
            await msg.delete()
    else:
        await message.answer("Afsuski, hech narsa topilmadi 😔" if not is_ru else "К сожалению, ничего не найдено 😔")
        await msg.delete()

# Tavsiya tugmasi bosilganda avtomatik qayta qidiradigan qism
@dp.callback_query(lambda c: c.data.startswith("search_"))
async def callback_search(callback: types.CallbackQuery):
    song_name = callback.data.split("search_")[1]
    
    # Tugma bosilganda xuddi foydalanuvchi qo'lda yozgandek handle_everything ga uzatadi
    fake_message = types.Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        from_user=callback.from_user,
        text=song_name
    )
    await callback.answer(f"Qidirilmoqda: {song_name}" if user_languages.get(callback.from_user.id) == "uz" else f"Ищу: {song_name}")
    await handle_everything(fake_message)

async def main():
    await startup_server()  
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
