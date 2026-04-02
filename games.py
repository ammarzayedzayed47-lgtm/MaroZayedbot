import json
import random
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# ==================== الملفات ====================
BANK_FILE = "bank.json"
GAME_SETTINGS_FILE = "game_settings.json"

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

bank_data = load_json(BANK_FILE)
game_settings = load_json(GAME_SETTINGS_FILE)

# ==================== المتغيرات ====================
last_salary = {}
last_gamble = {}
last_invest = {}
last_guess = {}
last_bakhshish = {}
last_steal = {}
last_rps_game = {}
last_dice_game = {}
last_roulette_game = {}

JOBS = [
    "مبرمج", "طيار", "طبيب", "مهندس", "معلم", "محامي", "تاجر", "صيدلي",
    "عسكري", "شرطي", "صحفي", "كاتب", "فنان", "موسيقي", "رياضي", "مدرب",
    "سائق", "بحار", "فلاح", "نجار", "سباك", "كهربائي", "طباخ", "خباز"
]

JOB_SALARIES = {
    "مبرمج": 500, "طيار": 600, "طبيب": 550, "مهندس": 450,
    "معلم": 300, "محامي": 400, "تاجر": 350, "صيدلي": 380,
    "عسكري": 420, "شرطي": 380, "صحفي": 320, "كاتب": 280,
    "فنان": 400, "موسيقي": 350, "رياضي": 450, "مدرب": 380,
    "سائق": 250, "بحار": 300, "فلاح": 200, "نجار": 220,
    "سباك": 250, "كهربائي": 280, "طباخ": 240, "خباز": 220
}

# ==================== قائمة الأعلام ====================
FLAGS = {
    "🇸🇦": "السعودية",
    "🇪🇬": "مصر",
    "🇦🇪": "الإمارات",
    "🇰🇼": "الكويت",
    "🇶🇦": "قطر",
    "🇧🇭": "البحرين",
    "🇴🇲": "عمان",
    "🇯🇴": "الأردن",
    "🇱🇧": "لبنان",
    "🇵🇸": "فلسطين",
    "🇸🇾": "سوريا",
    "🇮🇶": "العراق",
    "🇾🇪": "اليمن",
    "🇸🇩": "السودان",
    "🇱🇾": "ليبيا",
    "🇹🇳": "تونس",
    "🇩🇿": "الجزائر",
    "🇲🇦": "المغرب",
    "🇹🇷": "تركيا",
    "🇮🇷": "إيران",
    "🇵🇰": "باكستان",
    "🇮🇳": "الهند",
    "🇨🇳": "الصين",
    "🇯🇵": "اليابان",
    "🇺🇸": "أمريكا",
    "🇬🇧": "بريطانيا",
    "🇫🇷": "فرنسا",
    "🇩🇪": "ألمانيا",
    "🇮🇹": "إيطاليا",
    "🇪🇸": "إسبانيا",
    "🇷🇺": "روسيا",
    "🇧🇷": "البرازيل",
    "🇦🇺": "أستراليا",
    "🇨🇦": "كندا",
    "🇲🇽": "المكسيك",
    "🇿🇦": "جنوب أفريقيا"
}

# ==================== حساب جديد ====================
async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name
    
    if user_id in bank_data:
        await update.message.reply_text("✅ أنت عندك حساب بالفعل! استخدم `حسابي`")
        return
    
    account_number = str(random.randint(100000, 999999))
    
    bank_data[user_id] = {
        "name": first_name,
        "account_number": account_number,
        "balance": 1000,
        "job": random.choice(JOBS),
        "created_at": str(datetime.now())
    }
    
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"🎉 **تم إنشاء حسابك!**\n\n"
        f"👤 الاسم: {first_name}\n"
        f"🏦 رقم الحساب: `{account_number}`\n"
        f"💰 الرصيد: 1000 جنيه\n"
        f"💼 وظيفتك: {bank_data[user_id]['job']}\n\n"
        f"استخدم `راتب` كل 15 دقيقة\n"
        f"استخدم `حسابي` لعرض حسابك",
        parse_mode="Markdown"
    )

# ==================== حسابي ====================
async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    acc = bank_data[user_id]
    text = f"""
🏦 **حسابك البنكي**

👤 الاسم: {acc['name']}
🆔 الايدي: `{user_id}`
🏧 رقم الحساب: `{acc['account_number']}`
💰 الرصيد: {acc['balance']} جنيه
💼 وظيفتك: {acc['job']}
📅 تاريخ الإنشاء: {acc['created_at']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

# ==================== راتب ====================
async def salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = time.time()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if user_id in last_salary:
        diff = now - last_salary[user_id]
        if diff < 900:
            rem = int(900 - diff)
            m, s = rem // 60, rem % 60
            await update.message.reply_text(f"⏰ باقي {m} دقيقة و {s} ثانية للراتب الجاي")
            return
    
    job = bank_data[user_id]['job']
    amount = JOB_SALARIES.get(job, 250)
    
    bank_data[user_id]['balance'] += amount
    last_salary[user_id] = now
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"💼 **تم صرف راتبك!**\n\n"
        f"👔 وظيفتك: {job}\n"
        f"💰 الراتب: {amount} جنيه\n"
        f"💵 رصيدك: {bank_data[user_id]['balance']} جنيه\n\n"
        f"⏰ الراتب الجاي بعد 15 دقيقة",
        parse_mode="Markdown"
    )

# ==================== تحويل ====================
async def send_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    parts = update.message.text.strip().split()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if len(parts) != 3:
        await update.message.reply_text("⚠️ استخدم: `تحويل <رقم_الحساب> <المبلغ>`", parse_mode="Markdown")
        return
    
    target_acc = parts[1]
    try:
        amount = int(parts[2])
    except:
        await update.message.reply_text("⚠️ المبلغ لازم يكون رقم")
        return
    
    if amount <= 0:
        await update.message.reply_text("⚠️ المبلغ لازم أكبر من 0")
        return
    
    if bank_data[user_id]['balance'] < amount:
        await update.message.reply_text("❌ رصيدك مش كافي")
        return
    
    target_id = None
    for uid, data in bank_data.items():
        if data['account_number'] == target_acc:
            target_id = uid
            break
    
    if not target_id:
        await update.message.reply_text("❌ رقم الحساب غلط")
        return
    
    if user_id == target_id:
        await update.message.reply_text("❌ مش هتقدر تحول لنفسك")
        return
    
    bank_data[user_id]['balance'] -= amount
    bank_data[target_id]['balance'] += amount
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"✅ **تم التحويل!**\n\n"
        f"💰 المبلغ: {amount} جنيه\n"
        f"🏦 لحساب: {target_acc}\n"
        f"💵 رصيدك: {bank_data[user_id]['balance']} جنيه",
        parse_mode="Markdown"
    )

# ==================== حظ ====================
async def gamble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    parts = update.message.text.strip().split()
    now = time.time()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not game_settings.get("games_enabled", True):
        await update.message.reply_text("❌ الألعاب موقوفة حالياً")
        return
    
    if len(parts) != 2:
        await update.message.reply_text("⚠️ استخدم: `حظ <المبلغ>`", parse_mode="Markdown")
        return
    
    try:
        amount = int(parts[1])
    except:
        await update.message.reply_text("⚠️ المبلغ لازم يكون رقم")
        return
    
    if amount <= 0:
        await update.message.reply_text("⚠️ المبلغ لازم أكبر من 0")
        return
    
    if bank_data[user_id]['balance'] < amount:
        await update.message.reply_text("❌ رصيدك مش كافي")
        return
    
    if user_id in last_gamble:
        diff = now - last_gamble[user_id]
        if diff < 600:
            rem = int(600 - diff)
            m, s = rem // 60, rem % 60
            await update.message.reply_text(f"⏰ استنى {m} دقيقة و {s} ثانية")
            return
    
    r = random.randint(1, 100)
    
    if r <= 10:
        bank_data[user_id]['balance'] -= amount
        msg = f"😭 **خسارة كبيرة!** خسرت {amount} جنيه"
    elif r <= 30:
        loss = amount // 2
        bank_data[user_id]['balance'] -= loss
        msg = f"😞 **خسارة!** خسرت {loss} جنيه"
    elif r <= 60:
        msg = f"😐 **ولا حاجة!**"
    elif r <= 85:
        win = amount // 2
        bank_data[user_id]['balance'] += win
        msg = f"😊 **ربح صغير!** كسبت {win} جنيه"
    else:
        win = amount * 2
        bank_data[user_id]['balance'] += win
        msg = f"🎉 **ربح كبير!** كسبت {win} جنيه"
    
    last_gamble[user_id] = now
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"🎲 **لعبة الحظ**\n\n{msg}\n\n💰 رصيدك: {bank_data[user_id]['balance']} جنيه\n⏰ تلعب تاني بعد 10 دقائق",
        parse_mode="Markdown"
    )

# ==================== استثمار ====================
async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    parts = update.message.text.strip().split()
    now = time.time()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not game_settings.get("games_enabled", True):
        await update.message.reply_text("❌ الألعاب موقوفة حالياً")
        return
    
    if len(parts) != 2:
        await update.message.reply_text("⚠️ استخدم: `استثمار <المبلغ>`", parse_mode="Markdown")
        return
    
    try:
        amount = int(parts[1])
    except:
        await update.message.reply_text("⚠️ المبلغ لازم يكون رقم")
        return
    
    if amount < 500:
        await update.message.reply_text("⚠️ أقل مبلغ للاستثمار 500 جنيه")
        return
    
    if bank_data[user_id]['balance'] < amount:
        await update.message.reply_text("❌ رصيدك مش كافي")
        return
    
    if user_id in last_invest:
        diff = now - last_invest[user_id]
        if diff < 600:
            rem = int(600 - diff)
            m, s = rem // 60, rem % 60
            await update.message.reply_text(f"⏰ استنى {m} دقيقة و {s} ثانية")
            return
    
    r = random.randint(1, 100)
    
    if r <= 20:
        bank_data[user_id]['balance'] -= amount
        msg = f"📉 **استثمار فاشل!** خسرت {amount} جنيه"
    elif r <= 50:
        profit = int(amount * 0.2)
        bank_data[user_id]['balance'] += profit
        msg = f"📈 **ربح بسيط!** كسبت {profit} جنيه"
    elif r <= 80:
        profit = int(amount * 0.5)
        bank_data[user_id]['balance'] += profit
        msg = f"📊 **ربح جيد!** كسبت {profit} جنيه"
    else:
        profit = amount
        bank_data[user_id]['balance'] += profit
        msg = f"🚀 **استثمار ناجح!** كسبت {profit} جنيه"
    
    last_invest[user_id] = now
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"💼 **الاستثمار**\n\n{msg}\n\n💰 رصيدك: {bank_data[user_id]['balance']} جنيه\n⏰ تستثمر تاني بعد 10 دقائق",
        parse_mode="Markdown"
    )

# ==================== تخمين ====================
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    parts = update.message.text.strip().split()
    now = time.time()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not game_settings.get("games_enabled", True):
        await update.message.reply_text("❌ الألعاب موقوفة حالياً")
        return
    
    if len(parts) != 3:
        await update.message.reply_text("⚠️ استخدم: `تخمين <المبلغ> <رقم 1-10>`", parse_mode="Markdown")
        return
    
    try:
        amount = int(parts[1])
        guess_num = int(parts[2])
    except:
        await update.message.reply_text("⚠️ المبلغ والرقم لازم يكونو أرقام")
        return
    
    if amount <= 0:
        await update.message.reply_text("⚠️ المبلغ لازم أكبر من 0")
        return
    
    if guess_num < 1 or guess_num > 10:
        await update.message.reply_text("⚠️ الرقم لازم بين 1 و 10")
        return
    
    if bank_data[user_id]['balance'] < amount:
        await update.message.reply_text("❌ رصيدك مش كافي")
        return
    
    if user_id in last_guess:
        diff = now - last_guess[user_id]
        if diff < 30:
            rem = int(30 - diff)
            await update.message.reply_text(f"⏰ استنى {rem} ثانية")
            return
    
    secret = random.randint(1, 10)
    
    if guess_num == secret:
        win = amount * 5
        bank_data[user_id]['balance'] += win
        msg = f"🎉 **تخمين صحيح!** الرقم كان {secret}\nكسبت {win} جنيه"
    else:
        bank_data[user_id]['balance'] -= amount
        msg = f"😞 **تخمين خاطئ!** الرقم كان {secret}\nخسرت {amount} جنيه"
    
    last_guess[user_id] = now
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"🔢 **لعبة التخمين**\n\n{msg}\n\n💰 رصيدك: {bank_data[user_id]['balance']} جنيه",
        parse_mode="Markdown"
    )

# ==================== بقشيش ====================
async def bakhshish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = time.time()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if user_id in last_bakhshish:
        diff = now - last_bakhshish[user_id]
        if diff < 1200:
            rem = int(1200 - diff)
            m, s = rem // 60, rem % 60
            await update.message.reply_text(f"⏰ استنى {m} دقيقة و {s} ثانية عشان تاخد بقشيش تاني")
            return
    
    amount = random.randint(10, 3999)
    bank_data[user_id]['balance'] += amount
    last_bakhshish[user_id] = now
    save_json(BANK_FILE, bank_data)
    
    messages = [
        f"🎁 خد يا باشا {amount} جنيه بقشيش 🎉",
        f"💰 اتفضل {amount} جنيه، عينك يا حلو 😎",
        f"🤲 خد بقشيش {amount} جنيه، عقبال ما نكبر 💪",
        f"🎈 يلا بقشيش {amount} جنيه، استلم يا محترم 🫡",
        f"🍀 ربنا يباركلك {amount} جنيه، استلم 🎯"
    ]
    
    await update.message.reply_text(f"💸 **بقشيش!**\n\n{random.choice(messages)}\n\n💰 رصيدك: {bank_data[user_id]['balance']} جنيه", parse_mode="Markdown")

# ==================== سرقة (100% نجاح) ====================
async def steal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    now = time.time()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة الشخص اللي عايز تسرقه", parse_mode="Markdown")
        return
    
    target_id = str(update.message.reply_to_message.from_user.id)
    target_name = update.message.reply_to_message.from_user.first_name
    target_username = update.message.reply_to_message.from_user.username
    
    if user_id == target_id:
        await update.message.reply_text("😐 مش هتسرق نفسك يا فنان")
        return
    
    if target_id not in bank_data:
        await update.message.reply_text("⚠️ الشخص ده ماعندوش حساب بنكي")
        return
    
    if bank_data[target_id]['balance'] < 1000:
        await update.message.reply_text(f"😐 {target_name} رصيده أقل من 1000، مش يستاهل السرقة")
        return
    
    if user_id in last_steal:
        diff = now - last_steal[user_id]
        if diff < 120:
            rem = int(120 - diff)
            await update.message.reply_text(f"⏰ استنى {rem} ثانية عشان تسرق تاني")
            return
    
    max_steal = min(500, bank_data[target_id]['balance'] // 4)
    if max_steal < 10:
        await update.message.reply_text("😐 مافيش فايدة من السرقة دلوقتي")
        return
    
    steal_amount = random.randint(10, max_steal)
    
    # سرقة 100% نجاح
    bank_data[user_id]['balance'] += steal_amount
    bank_data[target_id]['balance'] -= steal_amount
    save_json(BANK_FILE, bank_data)
    
    # اسم الجروب ورابطه
    group_name = update.effective_chat.title if update.effective_chat.title else "جروب خاص"
    group_username = update.effective_chat.username
    
    if group_username:
        group_link = f"https://t.me/{group_username}"
        group_link_text = f"[اضغط هنا للدخول للجروب]({group_link})"
    else:
        group_link_text = "🚫 لا يوجد رابط للجروب (ليس له يوزرنيم)"
    
    messages = [
        f"🦹 خد يا حرامي! سرقت {steal_amount} جنيه من {target_name} 😈",
        f"🏃‍♂️ جري وجبتها! سرقت {steal_amount} جنيه من {target_name} 🤑",
        f"🤫 استنى محدش شافك... سرقت {steal_amount} جنيه من {target_name} 🤐"
    ]
    
    await update.message.reply_text(
        f"🦹 **عملية سرقة!**\n\n{random.choice(messages)}\n\n💰 رصيدك: {bank_data[user_id]['balance']} جنيه",
        parse_mode="Markdown"
    )
    
    # إرسال إشعار للمسروق مع رابط الجروب
    thief_mention = f"@{username}" if username else first_name
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"⚠️ **تنبيه! تمت سرقتك** ⚠️\n\n"
                 f"🦹 **السارق:** {thief_mention}\n"
                 f"🆔 **ايدي السارق:** `{user_id}`\n"
                 f"💰 **المبلغ المسروق:** {steal_amount} جنيه\n"
                 f"📊 **رصيدك الحالي:** {bank_data[target_id]['balance']} جنيه\n"
                 f"👥 **في جروب:** {group_name}\n"
                 f"🔗 **رابط الجروب:** {group_link_text}\n\n"
                 f"💡 استخدم `حسابي` لعرض حسابك\n"
                 f"🛡️ استخدم `اعدادات` لتشغيل الحماية",
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
    except Exception as e:
        print(f"فشل إرسال رسالة للمسروق: {e}")
    
    last_steal[user_id] = now
# ==================== لعبة العلم ====================
async def flag_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not game_settings.get("games_enabled", True):
        await update.message.reply_text("❌ الألعاب موقوفة حالياً")
        return
    
    flag, country = random.choice(list(FLAGS.items()))
    context.user_data['flag_answer'] = country
    context.user_data['flag_amount'] = 50
    
    await update.message.reply_text(
        f"🏳️ **لعبة الأعلام**\n\n"
        f"{flag}\n\n"
        f"ما هي اسم الدولة؟\n\n"
        f"💰 الجائزة: 50 جنيه\n"
        f"💡 اكتب اسم الدولة فقط",
        parse_mode="Markdown"
    )

# ==================== لعبة العمليات الحسابية (بدون وقت) ====================
async def math_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not game_settings.get("games_enabled", True):
        await update.message.reply_text("❌ الألعاب موقوفة حالياً")
        return
    
    operations = ['+', '-', '×', '÷']
    op = random.choice(operations)
    
    if op == '+':
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        answer = a + b
        question = f"{a} + {b}"
    elif op == '-':
        a = random.randint(1, 100)
        b = random.randint(1, a)
        answer = a - b
        question = f"{a} - {b}"
    elif op == '×':
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        answer = a * b
        question = f"{a} × {b}"
    else:
        b = random.randint(1, 20)
        answer = random.randint(1, 20)
        a = answer * b
        question = f"{a} ÷ {b}"
    
    context.user_data['math_answer'] = answer
    context.user_data['math_amount'] = 30
    
    await update.message.reply_text(
        f"🔢 **لعبة الحساب**\n\n"
        f"{question} = ؟\n\n"
        f"💰 الجائزة: 30 جنيه\n"
        f"💡 أجب بـ `حساب <الرقم>`",
        parse_mode="Markdown"
    )

# ==================== حجرة ورقة مقص ====================
async def rps_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = time.time()
    text = update.message.text.strip().lower()
    parts = text.split()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not game_settings.get("games_enabled", True):
        await update.message.reply_text("❌ الألعاب موقوفة حالياً")
        return
    
    if len(parts) != 2:
        await update.message.reply_text("⚠️ استخدم: `حجر <المبلغ>` أو `ورق <المبلغ>` أو `مقص <المبلغ>`", parse_mode="Markdown")
        return
    
    try:
        amount = int(parts[1])
    except:
        await update.message.reply_text("⚠️ المبلغ لازم يكون رقم")
        return
    
    if amount <= 0:
        await update.message.reply_text("⚠️ المبلغ لازم أكبر من 0")
        return
    
    if amount > bank_data[user_id]['balance']:
        await update.message.reply_text("❌ رصيدك مش كافي")
        return
    
    if user_id in last_rps_game:
        diff = now - last_rps_game[user_id]
        if diff < 30:
            rem = int(30 - diff)
            await update.message.reply_text(f"⏰ استنى {rem} ثانية عشان تلعب تاني")
            return
    
    choices = ['حجر', 'ورق', 'مقص']
    bot_choice = random.choice(choices)
    
    user_choice = parts[0]
    if user_choice not in choices:
        await update.message.reply_text("⚠️ اختار: حجر، ورق، أو مقص")
        return
    
    if user_choice == bot_choice:
        result = "تعادل"
        win_amount = 0
        msg = "🤝 **تعادل!** لم تخسر ولا تكسب"
    elif (user_choice == 'حجر' and bot_choice == 'مقص') or \
         (user_choice == 'مقص' and bot_choice == 'ورق') or \
         (user_choice == 'ورق' and bot_choice == 'حجر'):
        result = "فوز"
        win_amount = amount
        bank_data[user_id]['balance'] += win_amount
        msg = f"🎉 **فوز!** {user_choice} يكسر {bot_choice}\nربحت {win_amount} جنيه"
    else:
        result = "خسارة"
        win_amount = -amount
        bank_data[user_id]['balance'] -= amount
        msg = f"😞 **خسارة!** {bot_choice} يكسر {user_choice}\nخسرت {amount} جنيه"
    
    last_rps_game[user_id] = now
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"✊📄✂️ **حجرة ورقة مقص**\n\n"
        f"أنت: {user_choice}\n"
        f"البوت: {bot_choice}\n\n"
        f"{msg}\n\n"
        f"💰 رصيدك: {bank_data[user_id]['balance']} جنيه",
        parse_mode="Markdown"
    )

# ==================== لعبة النرد (بدون فلوس - ترفيهي) ====================
async def dice_game_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice_number = random.randint(1, 6)
    
    dice_emojis = {
        1: "⚀",
        2: "⚁", 
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅"
    }
    
    # محاولة إرسال استكر نرد
    dice_stickers = [
        "CAACAgIAAxkBAAEB9M1nLmNkR_fQ_r-K5vGJmJjLmNjLmQ",  # نرد 1
        "CAACAgIAAxkBAAEB9M9nLmNkR_fQ_r-K5vGJmJjLmNjLmA",  # نرد 2
        "CAACAgIAAxkBAAEB9NFnLmNkR_fQ_r-K5vGJmJjLmNjLmQ",  # نرد 3
        "CAACAgIAAxkBAAEB9NNnLmNkR_fQ_r-K5vGJmJjLmNjLmQ",  # نرد 4
        "CAACAgIAAxkBAAEB9NVnLmNkR_fQ_r-K5vGJmJjLmNjLmQ",  # نرد 5
        "CAACAgIAAxkBAAEB9NdnLmNkR_fQ_r-K5vGJmJjLmNjLmQ"   # نرد 6
    ]
    
    try:
        await update.message.reply_sticker(dice_stickers[dice_number - 1])
    except:
        pass
    
    await update.message.reply_text(
        f"🎲 **رميت النرد!**\n\n"
        f"{dice_emojis[dice_number]} **الرقم: {dice_number}**\n\n"
        f"📌 استخدم `نرد` تاني عشان ترمي تاني",
        parse_mode="Markdown"
    )
# ==================== روليت ====================
async def roulette_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = time.time()
    text = update.message.text.strip().lower()
    parts = text.split()
    
    if user_id not in bank_data:
        await update.message.reply_text("⚠️ ماعندكش حساب! استخدم `حساب جديد`", parse_mode="Markdown")
        return
    
    if not game_settings.get("games_enabled", True):
        await update.message.reply_text("❌ الألعاب موقوفة حالياً")
        return
    
    if len(parts) != 3:
        await update.message.reply_text("⚠️ استخدم: `روليت <لون/رقم> <المبلغ>`\n🎨 الألوان: أحمر، أسود\n🔢 الأرقام: 0-36", parse_mode="Markdown")
        return
    
    try:
        amount = int(parts[2])
    except:
        await update.message.reply_text("⚠️ المبلغ لازم يكون رقم")
        return
    
    if amount <= 0:
        await update.message.reply_text("⚠️ المبلغ لازم أكبر من 0")
        return
    
    if amount > bank_data[user_id]['balance']:
        await update.message.reply_text("❌ رصيدك مش كافي")
        return
    
    if user_id in last_roulette_game:
        diff = now - last_roulette_game[user_id]
        if diff < 30:
            rem = int(30 - diff)
            await update.message.reply_text(f"⏰ استنى {rem} ثانية عشان تلعب تاني")
            return
    
    bet = parts[1]
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    
    result_number = random.randint(0, 36)
    
    if result_number == 0:
        result_color = "صفر"
    elif result_number in red_numbers:
        result_color = "أحمر"
    else:
        result_color = "أسود"
    
    win = False
    multiplier = 0
    
    if bet == 'أحمر' and result_color == 'أحمر':
        win = True
        multiplier = 2
    elif bet == 'أسود' and result_color == 'أسود':
        win = True
        multiplier = 2
    elif bet.isdigit() and int(bet) == result_number:
        win = True
        multiplier = 36
    
    if win:
        win_amount = amount * multiplier
        bank_data[user_id]['balance'] += win_amount
        msg = f"🎉 **فوز!** الرقم {result_number} ({result_color})\nربحت {win_amount} جنيه!"
    else:
        bank_data[user_id]['balance'] -= amount
        msg = f"😞 **خسارة!** الرقم {result_number} ({result_color})\nخسرت {amount} جنيه!"
    
    last_roulette_game[user_id] = now
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"🎰 **لعبة الروليت**\n\n"
        f"🎲 الرقم الفائز: {result_number}\n"
        f"🎨 اللون: {result_color}\n\n"
        f"{msg}\n\n"
        f"💰 رصيدك: {bank_data[user_id]['balance']} جنيه",
        parse_mode="Markdown"
    )

# ==================== تشغيل/إيقاف الألعاب ====================
async def toggle_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    parts = update.message.text.strip().split()
    
    if user_id != 5415189680:
        await update.message.reply_text("⛔ هذا الأمر للمالك فقط!")
        return
    
    if len(parts) != 2:
        await update.message.reply_text("⚠️ استخدم: `الالعاب on` أو `الالعاب off`", parse_mode="Markdown")
        return
    
    status = parts[1].lower()
    
    if status == "on":
        game_settings["games_enabled"] = True
        save_json(GAME_SETTINGS_FILE, game_settings)
        await update.message.reply_text("✅ **تم تشغيل الألعاب!**")
    elif status == "off":
        game_settings["games_enabled"] = False
        save_json(GAME_SETTINGS_FILE, game_settings)
        await update.message.reply_text("❌ **تم إيقاف الألعاب!**")
    else:
        await update.message.reply_text("⚠️ استخدم: `الالعاب on` أو `الالعاب off`", parse_mode="Markdown")

# ==================== التحقق من إجابات الألعاب ====================
async def check_game_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    # التحقق من لعبة العلم (أي نص مش أمر)
    if context.user_data.get('flag_answer'):
        # تنظيف النص المدخل (شيل علامات الترقيم والمسافات الزايدة)
        user_answer = text.lower().strip()
        # إزالة حروف العلة في الآخر (ة, ه, ى, ي)
        user_answer = user_answer.rstrip('ةهىي')
        
        correct_answer = context.user_data['flag_answer'].lower()
        correct_answer = correct_answer.rstrip('ةهىي')
        
        if user_answer == correct_answer or user_answer == correct_answer + 'ة' or user_answer == correct_answer + 'ه':
            amount = context.user_data.get('flag_amount', 50)
            bank_data[user_id]['balance'] += amount
            save_json(BANK_FILE, bank_data)
            await update.message.reply_text(f"🎉 **إجابة صحيحة!**\n\nربحت {amount} جنيه\n💰 رصيدك: {bank_data[user_id]['balance']} جنيه", parse_mode="Markdown")
            context.user_data['flag_answer'] = None
        else:
            await update.message.reply_text(f"❌ إجابة خاطئة! الدولة الصحيحة هي {context.user_data['flag_answer']}", parse_mode="Markdown")
            context.user_data['flag_answer'] = None
        return
    
    # التحقق من لعبة الحساب
    if context.user_data.get('math_answer') and text.startswith('حساب '):
        try:
            answer = int(text[6:].strip())
            if answer == context.user_data['math_answer']:
                amount = context.user_data.get('math_amount', 30)
                bank_data[user_id]['balance'] += amount
                save_json(BANK_FILE, bank_data)
                await update.message.reply_text(f"🎉 **إجابة صحيحة!**\n\nربحت {amount} جنيه\n💰 رصيدك: {bank_data[user_id]['balance']} جنيه", parse_mode="Markdown")
                context.user_data['math_answer'] = None
            else:
                await update.message.reply_text(f"❌ إجابة خاطئة! الإجابة الصحيحة هي {context.user_data['math_answer']}", parse_mode="Markdown")
                context.user_data['math_answer'] = None
        except:
            pass
        return