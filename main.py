import asyncio
import re
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.error import TelegramError
import html
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# ===== CONFIG =====
TOKEN = "8528647202:AAHrcOe4Zg6lAaxQweqxiVqljXMuqsD6da8"  # <-- TOKEN ni xavfsizlik uchun o'zgartiring

# ===== States =====
TIL, MINTQA, MENU, BOLM, LINK, MATN, VAQT, TAKROR, OLDINDAN, TAHRIR, EXIT_EDIT, YORDAM = range(12)

# ===== Database (Memory) =====
users = {}
tasks = {}

# ===== Static Data =====
ZONE_MAP = {
    "toshkent": "Asia/Tashkent",
    "ташкент": "Asia/Tashkent",
    "uzbekistan": "Asia/Tashkent",
    "узбекистан": "Asia/Tashkent",
    "samarqand": "Asia/Tashkent",
    "самарканд": "Asia/Tashkent",
    "andijon": "Asia/Tashkent",
    "андижан": "Asia/Tashkent",
    "rossiya": "Europe/Moscow",
    "russia": "Europe/Moscow",
    "россия": "Europe/Moscow",
    "moskva": "Europe/Moscow",
    "москва": "Europe/Moscow",
    "sankt-peterburg": "Europe/Moscow",
    "питер": "Europe/Moscow",
    "new york": "America/New_York",
    "newyork": "America/New_York",
    "ny": "America/New_York",
    "нью-йорк": "America/New_York",
    "washington": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "london": "Europe/London",
    "londan": "Europe/London",
    "лондон": "Europe/London",
    "uk": "Europe/London",
    "istanbul": "Europe/Istanbul",
    "istanbol": "Europe/Istanbul",
    "истамбул": "Europe/Istanbul",
    "turkiya": "Europe/Istanbul",
    "berlin": "Europe/Berlin",
    "берлин": "Europe/Berlin",
    "germany": "Europe/Berlin",
    "parij": "Europe/Paris",
    "paris": "Europe/Paris",
    "париж": "Europe/Paris",
    "beijing": "Asia/Shanghai",
    "pekin": "Asia/Shanghai",
    "пекин": "Asia/Shanghai",
    "china": "Asia/Shanghai",
    "tokyo": "Asia/Tokyo",
    "tokio": "Asia/Tokyo",
    "токио": "Asia/Tokyo",
    "seoul": "Asia/Seoul",
    "seul": "Asia/Seoul",
    "сеул": "Asia/Seoul",
    "dubai": "Asia/Dubai",
    "дубай": "Asia/Dubai",
    "uae": "Asia/Dubai"
}

STRINGS = {
    "UZ": {
        "start": "🌍 Tilni tanlang / Выберите язык",
        "ask_tz": "🕙 Endi esa vaqt mintaqasini o'rnating!\n\n✍️ O'z vaqtingizga mos keladigan shahar nomini yuboring.\n\nMisol uchun: Toshkent",
        "menu": "<b>📌 Asosiy menyu!</b>\n\nKerakli bo'limni tanlang 👇\n\n➕ <b>Eslatma qo'shish</b> — yangi eslatma yarating va vaqtini belgilang\n\n📋 <b>Eslatmalar ro'yxati</b> — barcha eslatmalarni ko'rish va tahrirlash\n\n📖 <b>Qo'llanma va yordam</b> — botdan foydalanish bo'yicha yo'riqnoma",
        "btn_new": "➕ Eslatma qo'shish",
        "btn_list": "📋 Eslatmalar ro'yxati",
        "btn_back": "⬅️ Orqaga",
        "ask_bolm": "🔔 <b>Eslatma turini tanlang!</b>\n\nIltimos, quyidagi variantlardan birini tanlang:\n\n👤 <b>Shaxsiy</b> — eslatma faqat sizga keladi\n\n👥 <b>Guruh</b> — eslatma guruhlarda keladi\n\n📢 <b>Kanal</b> — eslatma kanallarda keladi",
        "ask_link": (
            "🔗 <b>{}</b> uchun <b>ID</b> yoki <b>Linkni</b> kiriting:\n\n"
            "⚠️ <b>DIQQAT:</b> Botni kanal/guruhga <b>ADMIN</b> qiling, aks holda xabar yubora olmaydi!\n\n"
            "🔓 Agar guruh ochiq bo‘lsa — linkni yuboring.\n"
            "🔒 Agar guruh yopiq bo‘lsa — ID ni yuboring. ID ni @userinfebot orqali olishingiz mumkin.\n\n"
            "❗️ Har ikkala holatda ham botni admin qiling!\n\n"
            "📹 Guruh qo‘shish bo‘yicha video:\n"
            "https://t.me/+UFffYEZkqt02NzEy"
        ),
        "ask_text": "📝 <b>Eslatma matnini kiriting.</b>\n\nMasalan:\n— Hisobotni topshirish;\n— Do'stimning tug'ilgan kuni bilan tabriklash;\n— Har 3 oyda tish schetkalarni almashtirish;\nva hokazo...",
        "ask_time": "⏰ <b>⏳ Eslatma vaqtini kiriting</b>\n\nFormat: 01.01.2026 14:00:",
        "ask_rep": "🔁 <b>Eslatma takrorlansinmi?</b>\n\nMasalan:\n— Har kuni\n— Har hafta\n— Har oy\nva hokazo...",
        "ask_pre": "⏰ <b>Oldindan eslatilsinmi?</b>\n\nMasalan:\n— 5 daqiqa oldin\n— 1 soat oldin\n— 1 kun oldin\nva hokazo...\n\n1 d = 1 daqiqa\n1 s = 1 soat\n1 k = 1 kun",
        "error_tz": "⚠️ <b>Mintaqa topilmadi</b>, Toshkent vaqti o'rnatildi.",
        "error_time": "❌ <b>Vaqt o'tmishda yoki noto'g'ri!</b>",
        "success": "✅ <b>Eslatma muvaffaqiyatli o'rnatildi!</b>",
        "no_rem": "📭 Bu bo'limda eslatmalar yo'q.",
        "btn_edit_text": "📝 Matn",
        "btn_edit_time": "⏰ Vaqt",
        "btn_edit_rep": "🔁 Takrorlash",
        "btn_edit_pre": "🔔 Oldindan",
        "btn_toggle": "❌ Faolsiz/✅ Faol",
        "btn_del": "🗑 O'chirish",
        "status_on": "<b>✅ Faol</b>",
        "status_off": "<b>❌ Faolsiz</b>",
        "btn_personal": "👤 Shaxsiy",
        "btn_group": "👥 Guruh",
        "btn_channel": "📢 Kanal",
        "ask_list_bolm": "📋 Eslatmalar ro'yxati!\n\nAvval eslatma turini tanlang:👇",
        "section": "<b>Bo'lim</b>",
        "location": "<b>Manzil</b>",
        "text": "<b>Matn</b>",
        "time": "<b>Vaqt</b>",
        "repeat": "<b>Takror</b>",
        "pre_rem": "<b>Oldindan</b>",
        "status": "<b>Holat</b>",
        "btn_help": "📖 Qo'llanma va yordam",
        "help_text": "🔗 Havola orqali kanalga o'tib video-qo'llanmalarni ko'rishingiz mumkin👇\n\nhttps://t.me/+UFffYEZkqt02NzEy\n\nAgar sizda yana savollar bo'lsa, bot administratori @iam_mkhmmd ga murojaat qiling. 🧑‍💻"
    },
    "RU": {
        "start": "🌐 <b>Выберите язык:</b>",
        "ask_tz": "🕙 Теперь установите часовой пояс!\n\n✍️ Отправьте название города, соответствующего вашему времени.\n\nНапример: Ташкент",
        "menu": "<b>📌 Главное меню!</b>\n\nВыберите нужный раздел 👇\n\n➕ <b>Добавить напоминание</b> — создайте новое и укажите время\n\n📋 <b>Список напоминаний</b> — просмотр и редактирование\n\n📖 <b>Инструкция</b> — руководство по использованию",
        "btn_new": "➕ Добавить напоминание",
        "btn_list": "📋 Список напоминаний",
        "btn_back": "⬅️ Назад",
        "ask_bolm": "🔔 <b>Выберите тип напоминания!</b>\n\n👤 <b>Личное</b> — придёт только вам\n\n👥 <b>Группа</b> — придёт в группах\n\n📢 <b>Канал</b> — придёт в каналах",
        "ask_link": (
            "👥 <b>Добавление группы</b>\n\n"
            "В зависимости от типа группы выполните следующие шаги:\n\n"
            "🔓 Если открытая (публичная) группа — отправьте ссылку на группу.\n"
            "🔒 Если закрытая (частная) группа — отправьте ID группы.\n"
            "ID можно получить с помощью @userinfebot.\n\n"
            "❗️ В обоих случаях обязательно назначьте бота администратором этой группы. Иначе напоминания в группе не будут приходить!\n\n"
            "📹 Видео-инструкция по добавлению группы:\n"
            "https://t.me/+p4L7bdZr0asxODVi"
        ),
        "ask_text": "📝 <b>Введите текст напоминания.</b>\n\nНапример:\n— Сдать отчёт;\n— Поздравить друга с днём рождения;\n— Менять зубную щётку каждые 3 месяца;\nи т.д.",
        "ask_time": "⏳ <b>Введите время напоминания.</b>\n\nФормат: 01.01.2026 14:00",
        "ask_rep": "🔁 <b>Повторять напоминание?</b>\n\nНапример:\n— Каждый день\n— Каждую неделю\n— Каждый месяц\nи т.д.",
        "ask_pre": "⏰ <b>Напомнить заранее?</b>\n\nНапример:\n— за 5 минут\n— за 1 час\n— за 1 день\nи т.д.",
        "error_tz": "⚠️ <b>Регион не найден</b>, установлено время Ташкента.",
        "error_time": "❌ <b>Время указано неверно или находится в прошлом!</b>",
        "success": "✅ <b>Напоминание успешно установлено!</b>",
        "no_rem": "📭 В этом разделе нет напоминаний.",
        "btn_edit_text": "📝 Текст",
        "btn_edit_time": "⏰ Время",
        "btn_edit_rep": "🔁 Повтор",
        "btn_edit_pre": "🔔 Заранее",
        "btn_toggle": "❌ Неактивно/✅ Активно",
        "btn_del": "🗑 Удалить",
        "status_on": "<b>✅ Активно</b>",
        "status_off": "<b>❌ Неактивно</b>",
        "btn_personal": "👤 Личное",
        "btn_group": "👥 Группа",
        "btn_channel": "📢 Канал",
        "ask_list_bolm": "📋 <b>Список напоминаний!</b>\n\nВыберите нужный раздел 👇",
        "section": "<b>Раздел</b>",
        "location": "<b>Место</b>",
        "text": "<b>Текст</b>",
        "time": "<b>Время</b>",
        "repeat": "<b>Повтор</b>",
        "pre_rem": "<b>Заранее</b>",
        "status": "<b>Статус</b>",
        "btn_help": "📖 Инструкция и помощь",
        "help_text": "🔗 Вы можете посмотреть видеоинструкции на нашем канале, перейдя по ссылке.👇\n\nhttps://t.me/+p4L7bdZr0asxODVi\n\nЕсли у вас остались ещё вопросы, обращайтесь к администратору бота @iam_mkhmmd 🧑‍💻"
    }
}

# ===== Keyboards =====
def get_rep_kb(uid):
    """Takrorlash tugmalari"""
    lang = users.get(uid, {}).get("lang", "UZ")
    if lang == "UZ":
        return [
            ["Hech qachon", "Har kuni"],
            ["Har hafta", "Har 2 hafta"],
            ["Har oy", "Choraklik (Har 3 oy)"],
            ["Har 6 oy", "Har yili"],
            ["✍️ Qo'lda"]
        ]
    else:
        return [
            ["Никогда", "Каждый день"],
            ["Каждую неделю", "Каждые 2 недели"],
            ["Каждый месяц", "Каждые 3 месяца"],
            ["Каждые 6 месяцев", "Каждый год"],
            ["✍️ Вручную"]
        ]

def get_pre_kb(uid):
    """Oldindan eslatma tugmalari"""
    lang = users.get(uid, {}).get("lang", "UZ")
    if lang == "UZ":
        return [
            ["1 d","5 d","10 d","15 d","30 d"],
            ["1 s","2 s","3 s","6 s","12 s"],
            ["1 k","2 k","3 k","7 k","14 k"],
            [ "❌ Yo'q","✍️ Qo'lda"]
        ]
    else:
        return [
            ["5 минут","15 минут","30 минут"],
            ["1 час","3 часа","6 часа"],
            ["1 день","1 месяц","❌ Нет"],
            ["✍️ Вручную"]
        ]

# ===== Helpers =====
def get_s(uid, key):
    lang = users.get(uid, {}).get("lang", "UZ")
    return STRINGS[lang].get(key, key)

def parse_duration(text):
    text = text.lower().strip()
    match = re.search(r"(\d+)", text)
    if not match: return None
    val = int(match.group(1))
    if any(x in text for x in ["kun", "день", "day"]): return timedelta(days=val)
    if any(x in text for x in ["soat", "час", "h"]): return timedelta(hours=val)
    if any(x in text for x in ["daqiqa", "мин", "m", "min"]): return timedelta(minutes=val)
    if any(x in text for x in ["hafta", "недел", "w", "week"]): return timedelta(weeks=val)
    return None

def ensure_user(uid):
    if uid not in users:
        users[uid] = {"reminders": [], "lang": "UZ", "tz": ZoneInfo("Asia/Tashkent")}

def _human_repeat_label(uid, td):
    """Return localized, human-friendly repeat label for timedelta td."""
    lang = users.get(uid, {}).get("lang", "UZ")
    if td is None:
        return "Yo'q" if lang == "UZ" else "Никогда"

    secs = int(td.total_seconds())
    days = secs // 86400

    common = {
        "UZ": {
            1: "🔄 Har kuni",
            7: "📅 Har hafta",
            14: "🗓 Har 2 haftada",
            30: "Har oy",
            90: "3 oyda",
            180: "6 oyda",
            365: "Har yili",
        },
        "RU": {
            1: "🔄 Каждый день",
            7: "📅 Каждую неделю",
            14: "🗓 Каждые 2 недели",
            30: "Каждый месяц",
            90: "Каждые 3 месяца",
            180: "Каждые 6 месяцев",
            365: "Каждый год",
        },
    }

    if days in common.get(lang):
        return common[lang][days]

    if secs % 86400 == 0:
        return (f"{days} {'kun' if lang == 'UZ' else 'дней'}") if days > 1 else ("1 kun" if lang == "UZ" else "1 день")
    hours = secs // 3600
    if secs % 3600 == 0 and hours > 0:
        return f"{hours} {'soat' if lang == 'UZ' else 'час(а)'}"
    minutes = secs // 60
    return f"{minutes} {'daqiqa' if lang == 'UZ' else 'минут(ы)'}"

def _human_pre_label(uid, minutes):
    """Return localized pre-reminder label."""
    lang = users.get(uid, {}).get("lang", "UZ")
    if not minutes:
        return "Yo'q" if lang == "UZ" else "Нет"
    if minutes < 60:
        return f"{minutes} daqiqa oldin" if lang == "UZ" else f"за {minutes} минут"
    if minutes % 60 == 0 and minutes // 60 < 24:
        hrs = minutes // 60
        return f"{hrs} soat oldin" if lang == "UZ" else f"за {hrs} час(а)"
    days = minutes // 1440
    return f"{days} kun oldin" if lang == "UZ" else f"за {days} день(дней)"

def format_reminder_text(uid, r):
    """Format reminder display with HTML markup."""
    lang = users.get(uid, {}).get("lang", "UZ")

    status_html = STRINGS[lang]["status_on"] if r.get("is_active") else STRINGS[lang]["status_off"]
    text_val = html.escape(r.get("text", "")) or "—"
    
    time_val = r.get("time")
    if time_val:
        time_str = time_val.strftime("%d.%m.%Y %H:%M")
    else:
        time_str = "—"

    rep_label = _human_repeat_label(uid, r.get("repeat"))
    pre_label = _human_pre_label(uid, r.get("pre_rem", 0))

    footer = ("Eslatmani yoqish yoki o'chirish uchun pastdagi tugmani bosing 👇"
              if lang == "UZ"
              else "Чтобы включить или отключить напоминание, нажмите кнопку ниже 👇")

    text = (
        f"🔔 {STRINGS[lang].get('status')}\n— {status_html}\n\n"
        f"📝 {STRINGS[lang].get('text')}\n— <i>{text_val}</i>\n\n"
        f"⏰ {STRINGS[lang].get('time')}\n— <i>{html.escape(time_str)}</i>\n\n"
        f"🔁 {STRINGS[lang].get('repeat')}\n— <i>{html.escape(rep_label)}</i>\n\n"
        f"⏰ {STRINGS[lang].get('pre_rem')}\n— <i>{html.escape(pre_label)}</i>\n\n"
        f"{footer}"
    )
    return text

# ===== CORE FUNCTIONS =====
async def send_reminder(context, uid, target, msg_type, r):
    """Send reminder message"""
    try:
        lang = users.get(uid, {}).get("lang", "UZ")
        now = datetime.now(r["time"].tzinfo)
        next_time = None
        if r.get("repeat"):
            next_time = r["time"] + r["repeat"]
        else:
            next_time = r["time"]  # Bir martalikda ham shu vaqt chiqadi

        if lang == "RU":
            header = ""
            test_text = f"🔔 {r['text']}"
            next_label = "📨 следующее уведомление:"
            # Agar bugungi sana bo‘lsa, "сегодня", aks holda to‘liq sana
            if next_time.date() == now.date():
                next_str = f"— сегодня в {next_time.strftime('%H:%M')}"
            else:
                next_str = f"— {next_time.strftime('%d.%m.%Y %H:%M')}"
            msg = f"{header}\n\n{test_text}\n\n{next_label}\n{next_str}"
        else:
            header = ""
            test_text = f"🔔 {r['text']}"
            next_label = "📨 Keyingi eslatma:"
            if next_time.date() == now.date():
                next_str = f"— bugun {next_time.strftime('%H:%M')} da"
            else:
                next_str = f"— {next_time.strftime('%d.%m.%Y %H:%M')} da"
            msg = f"{header}\n\n{test_text}\n\n{next_label}\n{next_str}"

        await context.bot.send_message(chat_id=target, text=msg)
        return True
    except TelegramError as e:
        print(f"Error ({target}): {e}")
        return False
# ...existing code...

async def reminder_scheduler(uid, r, context):
    pre_sent = False
    tz = r["time"].tzinfo

    while True:
        try:
            if r["id"] not in [x["id"] for x in users.get(uid, {}).get("reminders", [])]:
                break

            now = datetime.now(tz)

            if r.get("bolm") == get_s(uid, "btn_personal"):
                target_chat = uid
            else:
                target_chat = r.get("link", uid)

            if r.get("pre_rem", 0) > 0 and not pre_sent:
                if now >= (r["time"] - timedelta(minutes=r["pre_rem"])):
                    if r.get("is_active", True):
                        await send_reminder(context, uid, target_chat, "PRE", r)
                    pre_sent = True

            if now >= r["time"]:
                if r.get("is_active", True):
                    await send_reminder(context, uid, target_chat, "MAIN", r)

                if r.get("repeat"):
                    r["time"] += r["repeat"]
                    pre_sent = False
                    continue
                else:
                    r["is_active"] = False
                    break

            await asyncio.sleep(20)

        except Exception as e:
            print("Scheduler error:", e)
            await asyncio.sleep(60)

async def reschedule_task(uid, r, context):
    if uid in tasks and r["id"] in tasks[uid]:
        tasks[uid][r["id"]].cancel()
    if uid not in tasks: tasks[uid] = {}
    tasks[uid][r["id"]] = asyncio.create_task(reminder_scheduler(uid, r, context))

# ===== HANDLERS =====
async def send(update, text, kb=None):
    """Universal send function with HTML support"""
    await update.message.reply_text(
        text,
        reply_markup=kb,
        parse_mode="HTML"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # Always ask for language first
    if uid not in users or not users[uid].get("lang"):
        users[uid] = {"reminders": [], "lang": None, "tz": None}
        kb = [["🇺🇿 O'zbekcha", "🇷🇺 Русский"]]
        await send(
            update,
            STRINGS["UZ"]["start"],  # Always show UZ start, or use get_s(uid, "start")
            ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return TIL

    # If language is set but no timezone, ask for timezone
    if not users[uid].get("tz"):
        await send(
            update,
            get_s(uid, "ask_tz"),
            ReplyKeyboardRemove()
        )
        return MINTQA

    # If both are set, go to menu
    return await menu_display(update, context)

async def go_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users[uid].pop("current", None)
    users[uid].pop("edit_target", None)
    users[uid].pop("list_bolm", None)
    users[uid].pop("list_link", None)
    users[uid].pop("target_map", None)
    return await menu_display(update, context)

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)
    kb = [["🇺🇿 O'zbekcha", "🇷🇺 Русский"]]
    await send(
        update,
        get_s(uid, "start"),
        ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return TIL

async def til_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if "Рус" in text or "🇷🇺" in text:
        users[uid]["lang"] = "RU"
    else:
        users[uid]["lang"] = "UZ"

    # Agar timezone allaqachon bor bo'lsa, menyuga o'tkazamiz
    if users[uid].get("tz"):
        return await menu_display(update, context)

    # Timezone yo'q bo'lsa, so'raymiz
    await send(
        update,
        get_s(uid, "ask_tz"),
        ReplyKeyboardRemove()
    )
    return MINTQA

async def set_time_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in users:
        users[uid] = {
            "reminders": [],
            "lang": "UZ",
            "tz": ZoneInfo("Asia/Tashkent")
        }

    await send(
        update,
        get_s(uid, "ask_tz"),
        ReplyKeyboardRemove()
    )
    return MINTQA

async def mintqa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower().strip()

    zone = None
    for k, v in ZONE_MAP.items():
        if k in text:
            zone = v
            break

    if not zone:
        await send(
            update,
            "❌ <b>Mintaqa topilmadi!</b>\n\n"
            "👉 <b>Faqat shularni kiriting:</b>\n"
            "• Toshkent\n"
            "• Rossiya\n"
            "• New York\n\n"
            "📝 Ruscha yoki lotincha yozish mumkin"
        )
        return MINTQA

    users[uid]["tz"] = ZoneInfo(zone)
    return await menu_display(update, context)

async def menu_display(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, MENU, None)

    kb = [
        [get_s(uid, "btn_new")],
        [get_s(uid, "btn_list")],
        [get_s(uid, "btn_help")]
    ]

    await send(
        update, 
        get_s(uid, "menu"), 
        ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    if text == get_s(uid, "btn_new"):
        users[uid]["current"] = {
            "is_active": True,
            "id": str(uuid.uuid4())
        }

        kb = [
            [get_s(uid, "btn_personal")],
            [get_s(uid, "btn_group")],
            [get_s(uid, "btn_channel")],
            [get_s(uid, "btn_back")]
        ]

        await send(
            update,
            get_s(uid, "ask_bolm"),
            ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return BOLM

    elif text == get_s(uid, "btn_list"):
        kb = [
            [get_s(uid, "btn_personal")],
            [get_s(uid, "btn_group")],
            [get_s(uid, "btn_channel")],
            [get_s(uid, "btn_back")]
        ]

        await send(
            update,
            get_s(uid, "ask_list_bolm"),
            ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return TAHRIR

    elif text == get_s(uid, "btn_help"):
        return await yordam_handler(update, context)

    return MENU

async def yordam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, YORDAM, MENU)

    await send(
        update,
        get_s(uid, "help_text"),
        ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )
    return MENU

async def bolm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, BOLM, MENU)

    val = update.message.text

    if val == get_s(uid, "btn_back"):
        return await menu_display(update, context)

    users.setdefault(uid, {}).setdefault("current", {})["bolm"] = val

    # --- Yangi: Guruh/Kanal tanlashda ro'yxat chiqsin va "Eslatma qo'shish" tugmasi bo'lsin ---
    if val in [get_s(uid, "btn_group"), get_s(uid, "btn_channel")]:
        existing_links = []
        for r in users[uid]["reminders"]:
            if r["bolm"] == val and r.get("link") not in existing_links:
                existing_links.append(r.get("link"))

        kb = []
        group_names = {}
        for link in existing_links:
            try:
                chat = await context.bot.get_chat(link)
                name = chat.title or chat.username or str(link)
            except Exception:
                name = str(link)
            kb.append([name])
            group_names[name] = link

        lang = users[uid].get("lang", "UZ")
        # Tugma va matnlarni tilga qarab o'zgartirish
        if lang == "RU":
            add_btn = f"➕ {val} добавить"
            empty_msg = f"{val}\n\nСписок пуст. Добавить новую {val.lower()}? 👇"
            choose_msg = f"{val}\n\nВыберите одну из существующих или добавьте новую {val.lower()}: 👇"
        else:
            add_btn = f"➕ {val} qo'shish"
            empty_msg = f"{val}\n\nRo'yxati bo'sh. Yangi {val.lower()} qo'shamizmi? 👇"
            choose_msg = f"{val}\n\nQuyidagilardan birini tanlang yoki yangi {val.lower()} qo'shing: 👇"

        if not kb:
            kb = [[add_btn]]
            msg = empty_msg
        else:
            kb.append([add_btn])
            msg = choose_msg

        kb.append([get_s(uid, "btn_back")])

        users[uid]["group_select_mode"] = val
        users[uid]["group_names"] = group_names

        await send(
            update,
            msg,
            ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return "GROUP_SELECT"

    if val == get_s(uid, "btn_personal"):
        users[uid]["current"]["link"] = uid
        await send(
            update,
            get_s(uid, "ask_text"),
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return MATN

    return await menu_display(update, context)

async def group_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, "GROUP_SELECT", BOLM)

    text = update.message.text
    val = users[uid].get("group_select_mode")
    lang = users[uid].get("lang", "UZ")

    # Tugma matni tilga qarab
    if lang == "RU":
        add_btn = f"➕ {val} добавить"
    else:
        add_btn = f"➕ {val} qo'shish"

    if text == get_s(uid, "btn_back"):
        users[uid].pop("group_select_mode", None)
        users[uid].pop("group_names", None)
        return await menu_display(update, context)

    if text.startswith("➕"):
        # Yangi guruh/kanal uchun link so'raladi (eski usul)
        await send(
            update,
            get_s(uid, "ask_link").format(val),
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return LINK

    # Mavjud guruh/kanal tanlandi, endi eslatma qo'shish
    group_names = users[uid].get("group_names", {})
    link = group_names.get(text)
    if link:
        users[uid]["current"] = {
            "is_active": True,
            "id": str(uuid.uuid4()),
            "bolm": val,
            "link": link
        }
        await send(
            update,
            get_s(uid, "ask_text"),
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return MATN

    # Noto'g'ri tanlov
    await send(
        update,
        "❌ Неверный выбор!" if lang == "RU" else "❌ Noto'g'ri tanlov!",
        ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )
    return "GROUP_SELECT"

async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, LINK, "GROUP_SELECT")

    text = update.message.text.strip()

    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    target = normalize_chat_id(text)

    if not target and "t.me/" in text:
        username = text.split("t.me/")[-1].replace("/", "")
        target = "@" + username

    if not target and text.startswith("@"):
        target = text

    if not target:
        await send(
            update,
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "🔒 <b>Maxfiy kanal / guruh:</b>\n-1001234567890\n\n"
            "📢 <b>Ochiq kanal:</b>\n@kanal_nomi",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return LINK

    users[uid]["current"]["link"] = target

    await send(
        update,
        get_s(uid, "ask_text"),
        ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )
    return MATN

async def matn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, MATN, BOLM)

    text = update.message.text

    target = users[uid].get("edit_target", users[uid]["current"])
    target["text"] = text

    if "edit_target" in users[uid]:
        return await tahrir_item_display(update, context)

    await send(update, get_s(uid, "ask_time"))
    return VAQT

async def vaqt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, VAQT, MATN)

    if uid not in users:
        users[uid] = {
            "reminders": [],
            "lang": "UZ",
            "tz": ZoneInfo("Asia/Tashkent")
        }
        return await start(update, context)

    target = users[uid].get("edit_target") or users[uid].get("current")
    if not target:
        return await menu_display(update, context)

    tz = users[uid].get("tz", ZoneInfo("Asia/Tashkent"))
    text = update.message.text.strip()

    try:
        if ":" in text:
            dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
        else:
            dt = datetime.strptime(text, "%d.%m.%Y").replace(hour=9, minute=0)

        dt = dt.replace(tzinfo=tz)
        now = datetime.now(tz)

        if dt < now:
            await send(
                update,
                get_s(uid, "error_time"),
                ReplyKeyboardMarkup(
                    [[get_s(uid, "btn_back")]],
                    resize_keyboard=True
                )
            )
            return VAQT

        target["time"] = dt

        if "edit_target" in users[uid]:
            await reschedule_task(uid, target, context)
            return await tahrir_item_display(update, context)

        await send(
            update,
            get_s(uid, "ask_rep"),
            ReplyKeyboardMarkup(
                get_rep_kb(uid) + [[get_s(uid, "btn_back")]],
                resize_keyboard=True
            )
        )
        return TAKROR

    except ValueError:
        await send(
            update,
            get_s(uid, "error_time"),
            ReplyKeyboardMarkup(
                [[get_s(uid, "btn_back")]],
                resize_keyboard=True
            )
        )
        return VAQT

async def takror_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, TAKROR, VAQT)

    text = update.message.text.strip()
    td = None
    lang = users[uid]["lang"]

    rep_map = {
        "UZ": {
            "Hech qachon": None,
            "Har kuni": timedelta(days=1),
            "Har hafta": timedelta(weeks=1),
            "Har 2 hafta": timedelta(weeks=2),
            "Har oy": timedelta(days=30),
            "Choraklik (Har 3 oy)": timedelta(days=90),
            "Har 6 oy": timedelta(days=180),
            "Har yili": timedelta(days=365),
        },
        "RU": {
            "Никогда": None,
            "Каждый день": timedelta(days=1),
            "Каждую неделю": timedelta(weeks=1),
            "Каждые 2 недели": timedelta(weeks=2),
            "Каждый месяц": timedelta(days=30),
            "Каждые 3 месяца": timedelta(days=90),
            "Каждые 6 месяцев": timedelta(days=180),
            "Каждый год": timedelta(days=365),
        }
    }

    for k, v in rep_map.get(lang, {}).items():
        if k == text:
            td = v
            break

    if td is None and (("Qo'lda" in text) or ("Вручную" in text)):
        await send(
            update,
            "✍️ Masalan: 2 kun, 5 soat yoki 1 hafta:"
            if lang == "UZ"
            else "✍️ Например: 2 дня, 5 часов или 1 неделя:",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return TAKROR

    if td is None:
        td = parse_duration(text)

    target = users[uid].get("edit_target", users[uid]["current"])
    target["repeat"] = td

    if "edit_target" in users[uid]:
        await reschedule_task(uid, target, context)
        return await tahrir_item_display(update, context)

    await send(
        update,
        get_s(uid, "ask_pre"),
        ReplyKeyboardMarkup(get_pre_kb(uid) + [[get_s(uid, "btn_back")]], resize_keyboard=True)
    )
    return OLDINDAN

async def oldindan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, OLDINDAN, TAKROR)

    text = update.message.text.strip()
    norm = text.replace(" ", "").lower()
    lang = users[uid]["lang"]
    pre = None

    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    # No reminder
    if text in ["❌ Yo'q", "❌ Нет"]:
        pre = 0

    # Minutes (d / м)
    elif norm.endswith(("d", "м")) and not norm.endswith(("kd",)):
        match = re.search(r"(\d+)", norm)
        if match:
            n = int(match.group(1))
            if "k" in text.lower() or ("kun" in text.lower()):
                pre = n * 1440
            else:
                pre = n

    # Hours (s / ч)
    elif norm.endswith(("s", "ч")):
        match = re.search(r"(\d+)", norm)
        if match:
            n = int(match.group(1))
            pre = n * 60

    # Days (k / д)
    elif norm.endswith(("k", "д")):
        match = re.search(r"(\d+)", norm)
        if match:
            n = int(match.group(1))
            pre = n * 1440

    # Manual input
    elif "Qo'lda" in text or "Вручную" in text:
        await send(
            update,
            "✍️ Masalan: 10d, 1s, 2k yoki 15 daqiqa:"
            if lang == "UZ"
            else "✍️ Например: 10м, 1ч, 2д или 15 минут:",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return OLDINDAN

    # Free text parsing
    else:
        nums = re.findall(r"\d+", text)
        if not nums:
            await send(
                update,
                "❌ <b>Vaqt topilmadi!</b>" if lang == "UZ" else "❌ <b>Время не найдено!</b>",
                ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
            )
            return OLDINDAN

        n = int(nums[0])

        if lang == "UZ":
            if any(x in text.lower() for x in ["daqiqa", "min"]):
                pre = n
            elif any(x in text.lower() for x in ["soat", "s"]):
                pre = n * 60
            elif any(x in text.lower() for x in ["kun", "k"]):
                pre = n * 1440
        else:
            if any(x in text.lower() for x in ["мин", "м"]):
                pre = n
            elif any(x in text.lower() for x in ["час", "ч"]):
                pre = n * 60
            elif any(x in text.lower() for x in ["день", "д"]):
                pre = n * 1440

    if pre is None or pre < 0:
        await send(
            update,
            "❌ <b>Vaqt topilmadi!</b>" if lang == "UZ" else "❌ <b>Время не найдено!</b>",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return OLDINDAN

    target = users[uid].get("edit_target", users[uid]["current"])
    target["pre_rem"] = pre

    if "edit_target" in users[uid]:
        await reschedule_task(uid, target, context)
        return await tahrir_item_display(update, context)

    users[uid]["reminders"].append(target)
    await reschedule_task(uid, target, context)

    await send(
        update,
        get_s(uid, "success"),
        ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )

    return await menu_display(update, context)

async def tahrir_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    set_prev_step(uid, TAHRIR, MENU)

    btn_personal = get_s(uid, "btn_personal")
    btn_group = get_s(uid, "btn_group")
    btn_channel = get_s(uid, "btn_channel")
    btn_back = get_s(uid, "btn_back")

    if text == btn_back:
        users[uid].pop("list_bolm", None)
        users[uid].pop("target_map", None)
        return await menu_display(update, context)

    # ✅ Agar guruh/kanal ro'yxatidan eslatma tanlansa
    if "target_map" in users[uid] and text in users[uid]["target_map"]:
        selected_link = users[uid]["target_map"][text]
        selected_display_name = text
        list_bolm = users[uid].get("list_bolm", "")
        items = [r for r in users[uid]["reminders"] if str(r.get("link")) == str(selected_link)]
        
        if not items:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        kb = [[f"📌 {r['text'][:30]}"] for r in items]
        kb.append([btn_back])
        
        # ✅ GURUH yoki KANAL ga qarab xabar
        if users[uid]["lang"] == "RU":
            if "Группа" in list_bolm:
                msg = (
                    f"<b>📋 Список напоминаний!</b>\n\n"
                    f"Здесь находятся все напоминания в группе {selected_display_name}.\n\n"
                    f"Вы можете просматривать, редактировать, изменять статус или удалять напоминания.\n\n"
                    f"Выберите нужное напоминание для редактирования: "
                )
            else:  # Kanal
                msg = (
                    f"<b>📋 Список напоминаний!</b>\n\n"
                    f"Здесь находятся все напоминания в канале <b>{selected_display_name}</b>.\n\n"
                    f"Вы можете просматривать, редактировать, изменять статус или удалять напоминания.\n\n"
                    f"Выберите нужное напоминание для редактирования: 👇"
                )
        else:  # UZ
            if "Guruh" in list_bolm:
                msg = (
                    f"<b>📋 Eslatmalar ro'yxati!</b>\n\n"
                    f"Bu yerda barcha <b>{selected_display_name}</b> guruhdagi eslatmalaringiz mavjud.\n\n"
                    f"Eslatmalarni ko'rish, tahrirlash, holatini o'zgartirish yoki o'chirish mumkin.\n\n"
                    f"Tahrirlash uchun kerakli eslatmani tanlang: 👇"
                )
            else:  # Kanal
                msg = (
                    f"<b>📋 Eslatmalar ro'yxati!</b>\n\n"
                    f"Bu yerda barcha <b>{selected_display_name}</b> kanaldagi eslatmalaringiz mavjud.\n\n"
                    f"Eslatmalarni ko'rish, tahrirlash, holatini o'zgartirish yoki o'chirish mumkin.\n\n"
                    f"Tahrirlash uchun kerakli eslatmani tanlang: 👇"
                )
        
        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return EXIT_EDIT

    # ✅ SHAXSIY ESLATMALAR
    if text == btn_personal:
        items = [r for r in users[uid]["reminders"] if r["bolm"] == btn_personal]
        if not items:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        kb = [[f"📌 {r['text'][:30]}"] for r in items]
        kb.append([btn_back])
        
        if users[uid]["lang"] == "RU":
            msg = (
                f"<b>📋 Список напоминаний!</b>\n\n"
                f"Здесь находятся все ваши личные напоминания.\n\n"
                f"Вы можете просматривать, редактировать, изменять статус или удалять напоминания.\n\n"
                f"Выберите нужное напоминание для редактирования: 👇"
            )
        else:
            msg = (
                f"<b>📋 Eslatmalar ro'yxati!</b>\n\n"
                f"Bu yerda barcha shaxsiy eslatmalaringiz mavjud.\n\n"
                f"Eslatmalarni ko'rish, tahrirlash, holatini o'zgartirish yoki o'chirish mumkin.\n\n"
                f"Tahrirlash uchun kerakli eslatmani tanlang: 👇"
            )
        
        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return EXIT_EDIT

    # ✅ GURUH YOKI KANAL
    if text in [btn_group, btn_channel]:
        users[uid]["list_bolm"] = text
        users[uid]["target_map"] = {}
        kb = []
        seen = set()

        for r in users[uid]["reminders"]:
            if r["bolm"] == text:
                link = str(r.get("link"))
                if link not in seen:
                    seen.add(link)
                    try:
                        chat = await context.bot.get_chat(link)
                        name = chat.title or chat.username or link
                        if isinstance(link, int) and link < 0:
                            display_name = f"{name} — id({link})"
                        elif isinstance(chat.username, str):
                            display_name = f"{name} — (https://t.me/{chat.username})"
                        else:
                            display_name = name
                    except:
                        if isinstance(link, int) and link < 0:
                            display_name = f"Группа — id({link})"
                        else:
                            display_name = str(link)
                    
                    kb.append([display_name])
                    users[uid]["target_map"][display_name] = link

        if not kb:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        kb.append([btn_back])
        
        # ✅ GURUH yoki KANAL uchun turli xabarlar
        if users[uid]["lang"] == "RU":
            if "Группа" in text:
                msg = (
                    f"<b>👥 Список группы:</b>\n\n"
                    f"🔔 Чтобы просмотреть напоминания выберите нужную группу 👇"
                )
            else:  # Kanal
                msg = (
                    f"<b>📢 Список канала:</b>\n\n"
                    f"🔔 Чтобы просмотреть напоминания выберите нужный канал 👇"
                )
        else:  # UZ
            if "Guruh" in text:
                msg = (
                    f"<b>👥 Guruhlar ro'yxati:</b>\n\n"
                    f"🔔 Eslatmalarni ko'rish uchun kerakli guruhni tanlang 👇"
                )
            else:  # Kanal
                msg = (
                    f"<b>📢 Kanallar ro'yxati:</b>\n\n"
                    f"🔔 Eslatmalarni ko'rish uchun kerakli kanalni tanlang 👇"
                )
        
        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return TAHRIR

    # ✅ BOSH BO'LIM TANLASH
    kb = [[btn_personal, btn_group, btn_channel], [btn_back]]
    
    if users[uid]["lang"] == "RU":
        msg = "📋 <b>Выберите раздел:</b>"
    else:
        msg = "📋 <b>Bo'limni tanlang:</b>"
    
    await update.message.reply_text(
        msg,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return TAHRIR

# Bosqichlar zanjiri
STEP_CHAIN = {
    MENU: None,
    BOLM: MENU,
    "GROUP_SELECT": BOLM,
    LINK: "GROUP_SELECT",
    MATN: BOLM,
    VAQT: MATN,
    TAKROR: VAQT,
    OLDINDAN: TAKROR,
    TAHRIR: MENU,
    EXIT_EDIT: TAHRIR,
    YORDAM: MENU,
    MINTQA: TIL,
    TIL: None
}

def set_prev_step(uid, current, prev):
    users[uid]["prev_step"] = prev
    users[uid]["current_step"] = current

def get_prev_step(uid):
    return users[uid].get("prev_step", MENU)

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur = users[uid].get("current_step", MENU)
    prev = STEP_CHAIN.get(cur, MENU)

    # Tozalash (faqat bir bosqich ortga)
    if cur == EXIT_EDIT:
        users[uid].pop("edit_target", None)
    if cur == TAHRIR:
        users[uid].pop("list_bolm", None)
        users[uid].pop("target_map", None)
    if cur == "GROUP_SELECT":
        users[uid].pop("group_select_mode", None)
        users[uid].pop("group_names", None)
    if cur == BOLM:
        users[uid].pop("current", None)

    # Faqat bitta bosqich ortga qaytish
    if prev == MENU or prev is None:
        return await menu_display(update, context)
    if prev == TIL:
        return await change_lang(update, context)
    if prev == MINTQA:
        return await set_time_zone(update, context)
    if prev == BOLM:
        return await bolm_handler(update, context)
    if prev == "GROUP_SELECT":
        return await group_select_handler(update, context)
    if prev == LINK:
        return await link_handler(update, context)
    if prev == MATN:
        return await matn_handler(update, context)
    if prev == VAQT:
        return await vaqt_handler(update, context)
    if prev == TAKROR:
        return await takror_handler(update, context)
    if prev == OLDINDAN:
        return await oldindan_handler(update, context)
    if prev == TAHRIR:
        return await tahrir_list(update, context)
    return await menu_display(update, context)

# ...existing code...

async def tahrir_item_display(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display reminder details with edit options"""
    uid = update.effective_user.id
    r = users[uid]["edit_target"]
    set_prev_step(uid, EXIT_EDIT, TAHRIR)

    # Tugma matni dinamik: UZ va RU uchun to'g'ri chiqadi
    if users[uid]["lang"] == "UZ":
        toggle_text = "❌ Faolsiz" if r.get("is_active", True) else "✅ Faol"
    else:
        toggle_text = "❌ Неактивно" if r.get("is_active", True) else "✅ Активно"

    kb = [
        [toggle_text],
        [get_s(uid, "btn_edit_text"), get_s(uid, "btn_edit_time")],
        [get_s(uid, "btn_edit_rep"), get_s(uid, "btn_edit_pre")],
        [get_s(uid, "btn_del")],
        [get_s(uid, "btn_back")]
    ]
    await send(update, format_reminder_text(uid, r), ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return EXIT_EDIT

# ...existing code...

async def exit_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_prev_step(uid, EXIT_EDIT, TAHRIR)

    text = update.message.text

    # Toggle tugmasi matni har doim dinamik bo'lgani uchun, har ikkala variantni tekshiramiz
    if users[uid]["lang"] == "UZ":
        toggle_on = "❌ Faolsiz"
        toggle_off = "✅ Faol"
    else:
        toggle_on = "❌ Неактивно"
        toggle_off = "✅ Активно"

    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    if "edit_target" not in users[uid]:
        for r in users[uid]["reminders"]:
            if r["text"][:30] in text:
                users[uid]["edit_target"] = r
                return await tahrir_item_display(update, context)

    r = users[uid].get("edit_target")
    if not r:
        return MENU

    if text == get_s(uid, "btn_edit_text"):
        await send(update, get_s(uid, "ask_text"), ReplyKeyboardRemove())
        return MATN

    elif text == get_s(uid, "btn_edit_time"):
        await send(update, get_s(uid, "ask_time"), ReplyKeyboardRemove())
        return VAQT

    elif text == get_s(uid, "btn_edit_rep"):
        await send(update, get_s(uid, "ask_rep"), 
                   ReplyKeyboardMarkup(get_rep_kb(uid), resize_keyboard=True))
        return TAKROR

    elif text == get_s(uid, "btn_edit_pre"):
        await send(update, get_s(uid, "ask_pre"), 
                   ReplyKeyboardMarkup(get_pre_kb(uid), resize_keyboard=True))
        return OLDINDAN

    # Toggle tugmasi har ikkala variant uchun
    elif text == toggle_on or text == toggle_off:
        r["is_active"] = not r.get("is_active", True)
        await reschedule_task(uid, r, context)
        return await tahrir_item_display(update, context)

    elif text == get_s(uid, "btn_del"):
        users[uid]["reminders"] = [
            x for x in users[uid]["reminders"]
            if x["id"] != r["id"]
        ]
        if r["id"] in tasks.get(uid, {}):
            tasks[uid][r["id"]].cancel()
        users[uid].pop("edit_target", None)
        return await menu_display(update, context)

    return EXIT_EDIT

def back_filter():
    return filters.Regex(r"^⬅️")

def normalize_chat_id(text: str):
    """Normalize chat ID from user input"""
    text = text.strip()
    if text.startswith("-100") and text[4:].isdigit():
        return int(text)
    if text.startswith("-") and text[1:].isdigit():
        return int("-100" + text[1:])
    return None

# ...existing code...

def main():
    import logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    app = Application.builder().token(TOKEN).build()    

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("change_lang", change_lang),
            CommandHandler("set_time_zone", set_time_zone),
        ],
        states={
            TIL: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, til_handler),
            ],
            MINTQA: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, mintqa_handler),
            ],
            MENU: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler),
            ],
            YORDAM: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, yordam_handler),
            ],
            BOLM: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bolm_handler),
            ],
            "GROUP_SELECT": [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, group_select_handler),
            ],
            LINK: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler),
            ],
            MATN: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, matn_handler),
            ],
            VAQT: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, vaqt_handler),
            ],
            TAKROR: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, takror_handler),
            ],
            OLDINDAN: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, oldindan_handler),
            ],
            TAHRIR: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tahrir_list),
            ],
            EXIT_EDIT: [
                MessageHandler(back_filter(), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, exit_edit_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    app.add_handler(conv)

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()