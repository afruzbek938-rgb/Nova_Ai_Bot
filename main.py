import asyncio
import os
import re
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from google import genai
import yt_dlp

# =====================================================================
# TOKENS & KEYS (O'z ma'lumotlaringizni qo'ying)
# =====================================================================
TOKEN = "8853912401:AAEvwDxh-xw0vJY1pT_c-KEVwfGQ4lUkodw"
GEMINI_API_KEY = "AQ.Ab8RN6LCPVr6NAOTQ2ETewyNP-N5rddVuEUvtXHxoaqvqV1gJw"
# =====================================================================

dp = Dispatcher()
client = genai.Client(api_key=GEMINI_API_KEY)

user_data = {}

TEXTS = {
    'uz': {
        'welcome': "🌟 *NOVA AI BOTIGA XUSH KELIBSIZ!* 🌟\n\nQuyidagi tugmalardan birini tanlang:",
        'btn_ai': "🤖 AI CHAT",
        'btn_music': "🎵 QOʻSHIQ TOPISH",
        'btn_settings': "⚙️ SOZLAMALAR",
        'btn_info': "ℹ️ BOT HAQIDA",
        'btn_lang': "🌐 TILNI O'ZGARTIRISH",
        'btn_back': "⬅️ ORQAGA",
        'prompt_ai': "🚀 *AI Chat rejimi faol!* \n\nSavolingizni yozishingiz mumkin:",
        'prompt_music': "🎵 *Qo'shiq topish rejimi faol!* \n\nQuyidagi tugmalardan foydalanib qidiruvni boshlang:",
        'settings_msg': "⚙️ *Sozlamalar bo'limi:* \n\nTilni o'zgartirishingiz mumkin.",
        'info_msg': "*Nova AI v1.0*\n\nUshbu bot Gemini AI va Multimanbali musiqa qidiruv tizimi asosida ishlaydi. Qo'shiqlarni har qanday holatda ham topib beradi.",
        'error': "⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring!",
        'remind': "💡 *Eslatma:* Ishni boshlash uchun ekrandagi menyudan foydalaning!",
        'enter_track': "📝 Qo'shiq nomi yoki ijrochisini yozing:",
        'recommend_title': "🔥 *Siz uchun topilgan variantlar:* \n",
        'music_lang_msg': "🎵 Qaysi tildagi qo'shiqlarni qidirmoqchisiz?"
    },
    'ru': {
        'welcome': "🌟 *ДОБРО ПОЖАЛОВАТЬ В NOVA AI БОТ!* 🌟\n\nВыберите одну из кнопок:",
        'btn_ai': "🤖 ИИ ЧАТ",
        'btn_music': "🎵 НАЙТИ ПЕСНЮ",
        'btn_settings': "⚙️ НАСТРОЙКИ",
        'btn_info': "ℹ️ О БОТЕ",
        'btn_lang': "🌐 ИЗМЕНИТЬ ЯЗЫК",
        'btn_back': "⬅️ НАЗАД",
        'prompt_ai': "🚀 *Режим ИИ Чата активен!* \n\nВы можете задать свой вопрос:",
        'prompt_music': "🎵 *Режим поиска песен активен!* \n\nИспользуйте кнопки ниже для поиска треков:",
        'settings_msg': "⚙️ *Раздел настроек:* \n\nВы можете изменить язык.",
        'info_msg': "*Nova AI v1.0*\n\nЭтот бот работает на базе Gemini AI и мультиресурсной системы поиска. Находит треки в любом случае.",
        'error': "⚠️ Произшла ошибка. Попробуйте позже!",
        'remind': "💡 *Напоминание:* Чтобы начать, используйте меню на экране!",
        'enter_track': "📝 Напишите название песни или исполнителя:",
        'recommend_title': "🔥 *Найденные варианты для вас:* \n",
        'music_lang_msg': "🎵 Песни на каком языке вы хотите искать?"
    }
}

def clean_query(text: str) -> str:
    return re.sub(r'[^\w\s\-\(\)]', '', text).strip()

# --- 🎵 MULTI-BOT VA KO'P BOSQICHLI YUKLASH TIZIMI ---
async def download_track(search_text: str):
    cleaned_text = clean_query(search_text)
    
    strategies = [
        {"source": f"scsearch1:{cleaned_text}", "type": "soundcloud"},
        {"source": f"ytsearch1:{cleaned_text} audio", "type": "youtube"},
        {"source": f"ytsearch1:{cleaned_text}", "type": "youtube_backup"}
    ]

    loop = asyncio.get_event_loop()

    for strategy in strategies:
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "outtmpl": "downloads/%(id)s.%(ext)s", 
            "quiet": True,
            "ignoreerrors": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        }
        
        try:
            print(f"🔎 {strategy['type'].upper()} orqali qidirilmoqda: {cleaned_text}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(strategy["source"], download=True)
                )

                if info and 'entries' in info and len(info['entries']) > 0:
                    entry = info["entries"][0]
                    if entry:
                        title = entry.get("title", search_text)
                        performer = entry.get("uploader", "Nova Music")
                        video_id = entry.get("id")
                        ext = entry.get("ext", "mp3")

                        file_path = f"downloads/{video_id}.{ext}"

                        if os.path.exists(file_path):
                            return {
                                "file_path": file_path,
                                "title": title,
                                "performer": performer,
                                "source_type": strategy["type"]
                            }
        except Exception as e:
            print(f"⚠️ {strategy['type']}da xatolik bo'ldi, keyingi manbaga o'tilyapti... {e}")
            continue

    return None

# --- EKRANDAGI INLINE KLAVIATURALAR ---
def get_main_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS[lang]['btn_ai'], callback_data="menu_ai"), 
         InlineKeyboardButton(text=TEXTS[lang]['btn_music'], callback_data="menu_music")],
        [InlineKeyboardButton(text=TEXTS[lang]['btn_settings'], callback_data="menu_settings"), 
         InlineKeyboardButton(text=TEXTS[lang]['btn_info'], callback_data="menu_info")]
    ])

def get_settings_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS[lang]['btn_lang'], callback_data="menu_change_lang")],
        [InlineKeyboardButton(text=TEXTS[lang]['btn_back'], callback_data="menu_back")]
    ])

def get_lang_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz"), 
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")]
    ])

def get_music_lang_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha qo'shiqlar", callback_data="tracklang_uz"), 
         InlineKeyboardButton(text="🇷🇺 Русские песни", callback_data="tracklang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English songs", callback_data="tracklang_en")],
        [InlineKeyboardButton(text="⬅️ ORQAGA / НАЗАД", callback_data="menu_back")]
    ])

# --- TIMER (Kuzatuvchi va yuklash tugagach o'chuvchi xabar) ---
async def waiting_timer(message: Message, stop_event: asyncio.Event):
    seconds = 0
    clocks = ["⌛", "⏳"]
    wait_msg = await message.reply("⌛ *Barcha musiqiy bazalardan qidirilmoqda...* `(0s)`", parse_mode=ParseMode.MARKDOWN)
    try:
        while not stop_event.is_set():
            await asyncio.sleep(1)
            seconds += 1
            current_clock = clocks[seconds % len(clocks)]
            # Agar orqa fonda jarayon tugagan bo'lsa, xabarni tahrirlamaydi
            if stop_event.is_set():
                break
            await wait_msg.edit_text(f"{current_clock} *Iltimos kuting, eng yaxshi variant yuklanyapti...* `({seconds}s)`", parse_mode=ParseMode.MARKDOWN)
    except:
        pass
    finally:
        try:
            await wait_msg.delete()
        except:
            pass

# --- HANDLERS ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    chat_id = message.chat.id
    user_data[chat_id] = {'lang': 'uz', 'state': None}
    await message.reply(text="🤖 *Tilni tanlang / Выберите язык:*", reply_markup=get_lang_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

# --- EKRANDAGI TUGMALAR BOSILGANDA (CALLBACK QUERIES) ---
@dp.callback_query()
async def process_callbacks(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data

    if chat_id not in user_data:
        user_data[chat_id] = {'lang': 'uz', 'state': None}

    if data.startswith("setlang_"):
        lang = data.split("_")[1]
        user_data[chat_id]['lang'] = lang
        await callback_query.message.edit_text(TEXTS[lang]['welcome'], reply_markup=get_main_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)
        return

    lang = user_data[chat_id]['lang']

    if data == "menu_ai":
        user_data[chat_id]['state'] = "waiting_for_ai"
        await callback_query.message.edit_text(TEXTS[lang]['prompt_ai'], reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS[lang]['btn_back'], callback_data="menu_back")]]), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_music":
        user_data[chat_id]['state'] = "waiting_for_music_lang"
        await callback_query.message.edit_text(TEXTS[lang]['music_lang_msg'], reply_markup=get_music_lang_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_settings":
        await callback_query.message.edit_text(TEXTS[lang]['settings_msg'], reply_markup=get_settings_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_info":
        await callback_query.message.edit_text(TEXTS[lang]['info_msg'], reply_markup=get_main_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_change_lang":
        await callback_query.message.edit_text("🤖 *Tilni tanlang / Выберите язык:*", reply_markup=get_lang_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_back":
        user_data[chat_id]['state'] = None
        await callback_query.message.edit_text(TEXTS[lang]['welcome'], reply_markup=get_main_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("tracklang_"):
        user_data[chat_id]['state'] = "waiting_for_track_name"
        await callback_query.message.edit_text(TEXTS[lang]['enter_track'], reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS[lang]['btn_back'], callback_data="menu_back")]]), parse_mode=ParseMode.MARKDOWN)

# --- MATNLI XABARLAR HANDLERI ---
@dp.message(F.text)
async def handle_message(message: Message, bot: Bot):
    chat_id = message.chat.id
    text = message.text

    if chat_id not in user_data:
        user_data[chat_id] = {'lang': 'uz', 'state': None}

    lang = user_data[chat_id]['lang']
    state = user_data[chat_id]['state']

    if state in ["waiting_for_ai", "waiting_for_track_name"]:
        stop_timer = asyncio.Event()
        timer_task = asyncio.create_task(waiting_timer(message, stop_timer))
        
        try:
            if state == "waiting_for_track_name":
                track_info = await download_track(text)
                
                # Srazu taymerni to'xtatamiz va uning xabarini o'chiramiz, shunda fonda aylanib turmaydi
                stop_timer.set()
                await asyncio.sleep(0.1) # Taymer to'liq o'chishi uchun kichik tanaffus

                if track_info and os.path.exists(track_info['file_path']):
                    title = track_info['title']
                    performer = track_info['performer']
                    source = track_info['source_type']
                    
                    caption_text = f"🎼 *{title}*\n👤 *Ijrochi:* {performer}\n⚡ *Manba:* {source.upper()}\n\n" + TEXTS[lang]['recommend_title']
                    caption_text += f"🔗 [Ushbu qo'shiqni qidirish](https://www.google.com/search?q={text}+music)"
                    
                    audio_file = FSInputFile(track_info['file_path'])
                    
                    await message.reply_audio(
                        audio=audio_file,
                        caption=caption_text,
                        title=title,
                        performer=performer,
                        reply_markup=get_main_inline_keyboard(lang),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    try:
                        os.remove(track_info['file_path'])
                    except:
                        pass
                else:
                    msg_err = "❌ Qo'shiq biror bir bazadan topilmadi! Nomini tekshirib qaytadan yozing." if lang == 'uz' else "❌ Трек не найден ни в одной базе! Проверьте название."
                    await message.reply(msg_err, reply_markup=get_main_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)

            elif state == "waiting_for_ai":
                system_instruction = (
                    f"Sen professional AI mentorsan. Savolga {lang} tilida, "
                    f"aniq va qisqa (2-3 ta gap bilan) markdown holatida javob qaytar."
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{system_instruction}\n\nsavol: {text}"
                )
                stop_timer.set() # AI javob berganda ham taymer srazu o'chadi
                await message.reply(response.text, reply_markup=get_main_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            stop_timer.set()
            await message.reply(TEXTS[lang]['error'], reply_markup=get_main_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)
            
    else:
        await message.reply(TEXTS[lang]['remind'], reply_markup=get_main_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)

async def main() -> None:
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("="*60)
    print(" 🚀 NOVA MULTI-SOURCE MUSIC BOT ISHLAVOTTI...")
    print("="*60)
    asyncio.run(main())
