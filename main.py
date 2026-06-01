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
# Foydalanuvchining oxirgi qidiruv natijalarini vaqtincha eslab qolish uchun kesh (baza)
user_search_caches = {}

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

# Formatlash funksiyasi (soniyani minut:sekund qiladi)
def format_duration(d):
    if not d: return "0:00"
    m = d // 60
    s = d % 60
    return f"{m}:{s:02d}"

# Internetdan 10 ta eng mos musiqani topish funksiyasi
def search_top_10(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch10', # 10 ta natija qidirish
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                tracks = []
                for entry in info['entries']:
                    if entry:
                        tracks.append({
                            'url': entry.get('url'),
                            'title': entry.get('title', 'Noma\'lum tarona'),
                            'duration': entry.get('duration', 0)
                        })
                return tracks
        except Exception as e:
            print(f"Search error: {e}")
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

    if not user_text: return

    if user_text == "🇺🇿 O'zbekcha":
        user_languages[user_id] = "uz"
        await message.answer("O'zbek tili tanlandi! Qo'shiq nomini yozing! 🎧")
        return
    elif user_text == "🇷🇺 Русский":
        user_languages[user_id] = "ru"
        await message.answer("Выбран русский язык! Введите название песни! 🎧")
        return

    lang = user_languages.get(user_id, "uz")
    is_ru = lang == "ru"

    loading_text = "🔍 Ищу варианты..." if is_ru else "🔍 Variantlar qidirilmoqda..."
    msg = await message.answer(loading_text)

    loop = asyncio.get_event_loop()
    # Toza o'zbekcha taronalarni ham aniq topishi uchun matnga qo'shimcha beramiz
    results = await loop.run_in_executor(None, search_top_10, f"{user_text} muz audio")

    if results:
        # Foydalanuvchining natijalarini keshga saqlaymiz (Tugmani bosganda ishlatish uchun)
        user_search_caches[user_id] = results

        # 1. 10 talik ro'yxat matnini chiroyli qilib yig'amiz
        response_text = ""
        for index, track in enumerate(results, start=1):
            dur = format_duration(track['duration'])
            response_text += f"{index}. {track['title']} ({dur})\n"

        # 2. Xuddi rasm_4e6cfd.png dagi kabi 1 dan 10 gacha raqamli tugmalarni yasaymiz
        builder = InlineKeyboardBuilder()
        
        # Birinchi qator (1, 2, 3, 4, 5)
        for i in range(1, min(6, len(results) + 1)):
            builder.button(text=str(i), callback_data=f"play_{i-1}")
        
        # Ikkinchi qator (6, 7, 8, 9, 10)
        if len(results) > 5:
            for i in range(6, len(results) + 1):
                builder.button(text=str(i), callback_data=f"play_{i-1}")
        
        # Knopkalarni 5 tadan qilib chiroyli joylashtirish (rasmdagidek matrix ko'rinishi)
        builder.adjust(5, 5)

        await message.answer(response_text, reply_markup=builder.as_markup())
        await msg.delete()
    else:
        await message.answer("Hech narsa topilmadi 😔" if not is_ru else "Ничего не найдено 😔")
        await msg.delete()

# Raqamli knopka bosilganda ishlaydigan asosiy yuklovchi qism
@dp.callback_query(lambda c: c.data.startswith("play_"))
async def play_chosen_track(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    track_index = int(callback.data.split("play_")[1])

    lang = user_languages.get(user_id, "uz")
    is_ru = lang == "ru"

    # Keshda ma'lumot borligini tekshiramiz
    if user_id not in user_search_caches or track_index >= len(user_search_caches[user_id]):
        await callback.answer("Eski qidiruv natijasi. Iltimos, qayta qidirib ko'ring!" if not is_ru else "Устаревший поиск. Пожалуйста, ищите снова!", show_alert=True)
        return

    chosen_track = user_search_caches[user_id][track_index]
    
    await callback.answer("Musiqa yuklanmoqda..." if not is_ru else "Загрузка музыки...")
    
    # Yuklash vaqtida foydalanuvchiga bildirishnoma xabari
    status_msg = await callback.message.answer("📥 Mp3 tayyorlanmoqda..." if not is_ru else "📥 Подготовка Mp3...")

    try:
        await callback.message.answer_audio(
            audio=chosen_track['url'],
            title=chosen_track['title'],
            performer="NOVA Music",
            caption="Muvaffaqiyatli yuklandi! 🎧" if not is_ru else "Успешно загружено! 🎧"
        )
        await status_msg.delete()
    except Exception as e:
        await callback.message.answer("Musiqa hajmi juda katta yoki xatolik yuz berdi." if not is_ru else "Ошибка при отправке аудио.")
        await status_msg.delete()

async def main():
    await startup_server()  
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
