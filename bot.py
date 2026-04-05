import logging
import os
import json
import re
import time
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler, ConversationHandler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# المطور (مخفي)
DEVELOPER_ID = 5415189680
BOT_NAME = "مارو"
CREATION_DATE = "2026-04-05"

# حالات المحادثة
AMOUNT_STATE = 1
GIFT_AMOUNT_STATE = 2
GIFT_USES_STATE = 3
TRANSFER_ACCOUNT_STATE = 4
TRANSFER_AMOUNT_STATE = 5
GIFT_CODE_STATE = 6
GAME_BET_STATE = 7

# ملفات التخزين
WARNS_FILE = "warns.json"
SPECIAL_FILE = "specials.json"
SETTINGS_FILE = "settings.json"
BANK_FILE = "bank.json"
COOLDOWN_FILE = "cooldown.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

warns_data = load_json(WARNS_FILE)
specials_data = load_json(SPECIAL_FILE)
settings_data = load_json(SETTINGS_FILE)
bank_data = load_json(BANK_FILE)
cooldown_data = load_json(COOLDOWN_FILE)

user_messages = {}

# ========== قائمة الشتايم ==========
BAD_WORDS = [
    'كس', 'عير', 'قحب', 'منيك', 'متناك', 'شرموط', 'قحبة', 'زبي', 'كسك', 'كسها',
    'عيرك', 'عيرها', 'لحس', 'متناكة', 'منيوك', 'شرموطة', 'قحاب', 'قواد', 'قوادة',
    'ابن اللحس', 'ابن القحبة', 'ابن الشرموطة', 'يلعن ابوك', 'يلعن امك',
    'سحقا', 'سحاق', 'سحاقية', 'لوطي', 'لواط', 'متخول', 'تخول', 'خول',
    'نياكة', 'نيك', 'اكل خرا', 'كل خرا', 'ابن الكلب'
]

def is_bad_word(text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False

def get_chat_owner(chat_id):
    return settings_data.get(f"{chat_id}_owner", DEVELOPER_ID)

def is_owner(user_id, chat_id):
    return user_id == get_chat_owner(chat_id) or user_id == DEVELOPER_ID

async def is_admin(update, user_id):
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

async def is_special(chat_id, user_id):
    key = f"{chat_id}_{user_id}"
    return specials_data.get(key, False)

def check_cooldown(user_id, action, minutes):
    key = f"{user_id}_{action}"
    if key in cooldown_data:
        last = datetime.fromisoformat(cooldown_data[key])
        if datetime.now() - last < timedelta(minutes=minutes):
            remain = minutes - (datetime.now() - last).seconds // 60
            return False, remain
    return True, 0

def set_cooldown(user_id, action):
    key = f"{user_id}_{action}"
    cooldown_data[key] = datetime.now().isoformat()
    save_json(COOLDOWN_FILE, cooldown_data)

async def get_user_rank(update, user_id, chat_id):
    if user_id == DEVELOPER_ID:
        return "👑 **المالك الأساسي**"
    
    if is_owner(user_id, chat_id):
        return "👑 **مالك الجروب**"
    
    try:
        member = await update.effective_chat.get_member(user_id)
        if member.status == 'administrator':
            return "🛡️ **مشرف**"
    except:
        pass
    
    if await is_special(chat_id, user_id):
        return "⭐ **مميز**"
    
    return "👤 **عضو عادي**"

async def add_warning(chat_id, user_id, first_name, reason, update=None):
    key = f"{chat_id}_{user_id}"
    warns_data[key] = warns_data.get(key, 0) + 1
    
    if warns_data[key] >= 3:
        try:
            if update:
                await update.effective_chat.ban_member(user_id)
                await update.message.reply_text(f"🚫 {first_name} تم طرده بسبب {reason} (3 تحذيرات)")
            warns_data[key] = 0
        except:
            pass
    else:
        if update:
            await update.message.reply_text(f"⚠️ {first_name} {reason}\n⚠️ تحذير {warns_data[key]}/3")
    
    save_json(WARNS_FILE, warns_data)
    return warns_data[key]

# ========== دوال البنك ==========
def get_bank_account(user_id, username, first_name):
    key = str(user_id)
    if key not in bank_data:
        bank_data[key] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "account_number": str(random.randint(100000, 999999)),
            "balance": 1000,
            "job": random.choice(["مبرمج", "طبيب", "مهندس", "معلم", "تاجر", "فلاح", "سائق", "صانع محتوى"]),
            "last_salary": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        save_json(BANK_FILE, bank_data)
    return bank_data[key]

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_list = [
        f"🎉 أهلاً بك يا {user.first_name} في بوت {BOT_NAME}",
        f"🤖 مرحباً {user.first_name}! أنا {BOT_NAME}، جاهز لخدمتك",
        f"✨ يسعدنا رؤيتك يا {user.first_name} في عالم {BOT_NAME}",
    ]
    msg = random.choice(welcome_list)
    msg += f"\n\n**اسم البوت:** {BOT_NAME}\n**تاريخ الإنشاء:** {CREATION_DATE}\n\n**نبذة:** بوت متكامل لإدارة الجروبات والألعاب الاقتصادية."
    
    keyboard = [
        [InlineKeyboardButton("📜 نبذة", callback_data="about")],
        [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
        [InlineKeyboardButton("📊 حسابي", callback_data="my_account")],
        [InlineKeyboardButton("📋 الأوامر", callback_data="help_menu")]
    ]
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ========== دوال البنك الأساسية ==========
async def create_account(update, context):
    user = update.effective_user
    user_id = user.id
    key = str(user_id)
    
    if key in bank_data:
        acc = bank_data[key]
        await update.message.reply_text(
            f"⚠️ **لديك حساب بالفعل!**\n\n"
            f"🏦 رقم حسابك: `{acc['account_number']}`\n"
            f"💰 رصيدك الحالي: {acc['balance']} جنيه\n\n"
            f"📝 استخدم 'حسابي' لعرض جميع معلوماتك",
            parse_mode="Markdown"
        )
        return
    
    account = get_bank_account(user.id, user.username or str(user.id), user.first_name)
    await update.message.reply_text(
        f"✅ **تم إنشاء حسابك بنجاح!**\n\n"
        f"🏦 رقم حسابك: `{account['account_number']}`\n"
        f"💼 الوظيفة: {account['job']}\n"
        f"💰 الرصيد الافتتاحي: 1000 جنيه\n\n"
        f"📝 احتفظ برقم حسابك للتحويلات",
        parse_mode="Markdown"
    )

async def my_account(update, context):
    user = update.effective_user
    key = str(user.id)
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return
    
    acc = bank_data[key]
    text = (
        f"🏦 **معلومات حسابك**\n\n"
        f"👤 الاسم: {acc['first_name']}\n"
        f"📝 اليوزر: @{acc['username'] if acc['username'] != str(user.id) else 'لا يوجد'}\n"
        f"🆔 الايدي: `{acc['user_id']}`\n"
        f"🔢 رقم الحساب: `{acc['account_number']}`\n"
        f"💼 الوظيفة: {acc['job']}\n"
        f"💰 الرصيد: {acc['balance']} جنيه"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def salary(update, context):
    user = update.effective_user
    key = str(user.id)
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return
    
    acc = bank_data[key]
    last = datetime.fromisoformat(acc["last_salary"])
    
    if datetime.now() - last < timedelta(minutes=15):
        remain = 15 - (datetime.now() - last).seconds // 60
        await update.message.reply_text(f"⏳ انتظر {remain} دقيقة للراتب القادم")
        return
    
    amount = random.randint(500, 3000)
    acc["balance"] += amount
    acc["last_salary"] = datetime.now().isoformat()
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(f"💰 تم صرف راتبك كـ {acc['job']}: +{amount} جنيه\n💵 رصيدك الآن: {acc['balance']} جنيه")

# تحويل برقم الحساب
async def transfer_start(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return ConversationHandler.END
    
    await update.message.reply_text("📝 **تحويل فلوس**\n\nأرسل رقم حساب المستخدم اللي عايز تحوله:")
    return TRANSFER_ACCOUNT_STATE

async def transfer_get_account(update, context):
    account_num = update.message.text.strip()
    context.user_data['transfer_account'] = account_num
    
    found = None
    for uid, data in bank_data.items():
        if data.get("account_number") == account_num:
            found = data
            break
    
    if not found:
        await update.message.reply_text("❌ رقم الحساب غير صحيح! جرب تاني")
        return TRANSFER_ACCOUNT_STATE
    
    context.user_data['transfer_target'] = found
    await update.message.reply_text(f"✅ تم العثور على المستخدم: {found['first_name']}\n\nأرسل المبلغ اللي عايز تحوله:")
    return TRANSFER_AMOUNT_STATE

async def transfer_get_amount(update, context):
    try:
        amount = int(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ المبلغ غير صحيح! أرسل رقماً موجباً")
        return TRANSFER_AMOUNT_STATE
    
    sender_id = update.effective_user.id
    sender_key = str(sender_id)
    target_data = context.user_data['transfer_target']
    receiver_id = target_data['user_id']
    
    if sender_id == receiver_id:
        await update.message.reply_text("❌ لا يمكنك التحويل لنفسك")
        return ConversationHandler.END
    
    sender = bank_data[sender_key]
    if sender["balance"] < amount:
        await update.message.reply_text(f"❌ رصيدك لا يكفي. رصيدك: {sender['balance']} جنيه")
        return ConversationHandler.END
    
    sender["balance"] -= amount
    target_data["balance"] += amount
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(f"✅ تم تحويل {amount} جنيه إلى {target_data['first_name']}\n💰 رصيدك الآن: {sender['balance']} جنيه")
    
    try:
        await update.message.bot.send_message(
            receiver_id,
            f"💸 **استلمت حوالة!**\n\n"
            f"📥 المبلغ: {amount} جنيه\n"
            f"👤 من: {update.effective_user.first_name}\n"
            f"💰 رصيدك الجديد: {target_data['balance']} جنيه",
            parse_mode="Markdown"
        )
    except:
        pass
    
    return ConversationHandler.END

# بقشيش كل 15 دقيقة
async def bakhshish(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return
    
    can, remain = check_cooldown(user_id, "bakhshish", 15)
    if not can:
        await update.message.reply_text(f"⏳ استنى {remain} دقيقة عشان تاخد بقشيش جديد")
        return
    
    amount = random.randint(50, 500)
    old_balance = bank_data[key]["balance"]
    bank_data[key]["balance"] += amount
    save_json(BANK_FILE, bank_data)
    set_cooldown(user_id, "bakhshish")
    
    await update.message.reply_text(
        f"🎁 **بقشيش!**\n\n"
        f"💰 المبلغ: +{amount} جنيه\n"
        f"📊 الرصيد قبل: {old_balance} جنيه\n"
        f"📈 الرصيد بعد: {bank_data[key]['balance']} جنيه",
        parse_mode="Markdown"
    )

# ========== ألعاب الرهان (بمبلغ محدد) ==========

# لعبة حظ - رهان بمبلغ
async def gamble_start(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return ConversationHandler.END
    
    can, remain = check_cooldown(user_id, "gamble", 10)
    if not can:
        await update.message.reply_text(f"⏳ استنى {remain} دقيقة للعبة الحظ")
        return ConversationHandler.END
    
    await update.message.reply_text("🎲 **لعبة الحظ**\n\nأرسل المبلغ اللي عايز تراهن بيه:\n(الحد الأدنى 50 جنيه)")
    return GAME_BET_STATE

async def gamble_bet(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    try:
        bet = int(update.message.text.strip())
        if bet < 50:
            await update.message.reply_text("❌ الحد الأدنى للرهان 50 جنيه")
            return GAME_BET_STATE
    except:
        await update.message.reply_text("❌ أرسل رقماً صحيحاً")
        return GAME_BET_STATE
    
    acc = bank_data[key]
    if acc["balance"] < bet:
        await update.message.reply_text(f"❌ رصيدك لا يكفي. رصيدك: {acc['balance']} جنيه")
        return ConversationHandler.END
    
    # نسب الفوز 45% - خسارة 55%
    win_percentage = 45
    is_win = random.randint(1, 100) <= win_percentage
    
    old_balance = acc["balance"]
    
    if is_win:
        # الربح من 10% لـ 80% من قيمة الرهان
        profit_percent = random.randint(10, 80)
        profit = int(bet * profit_percent / 100)
        acc["balance"] += profit
        result_text = f"🎉 **فزت!**\n\n💰 رهانك: {bet} جنيه\n📈 نسبة الربح: {profit_percent}%\n💵 المكسب: +{profit} جنيه"
    else:
        loss = bet
        acc["balance"] -= loss
        result_text = f"😞 **خسرت!**\n\n💰 رهانك: {bet} جنيه\n💸 الخسارة: -{loss} جنيه"
    
    save_json(BANK_FILE, bank_data)
    set_cooldown(user_id, "gamble")
    
    await update.message.reply_text(
        f"{result_text}\n\n📊 الرصيد قبل: {old_balance} جنيه\n📈 الرصيد بعد: {acc['balance']} جنيه",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# لعبة استثمار - رهان بمبلغ
async def invest_start(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return ConversationHandler.END
    
    can, remain = check_cooldown(user_id, "invest", 10)
    if not can:
        await update.message.reply_text(f"⏳ استنى {remain} دقيقة للاستثمار")
        return ConversationHandler.END
    
    await update.message.reply_text("📈 **لعبة الاستثمار**\n\nأرسل المبلغ اللي عايز تستثمره:\n(الحد الأدنى 100 جنيه)")
    return GAME_BET_STATE

async def invest_bet(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    try:
        bet = int(update.message.text.strip())
        if bet < 100:
            await update.message.reply_text("❌ الحد الأدنى للاستثمار 100 جنيه")
            return GAME_BET_STATE
    except:
        await update.message.reply_text("❌ أرسل رقماً صحيحاً")
        return GAME_BET_STATE
    
    acc = bank_data[key]
    if acc["balance"] < bet:
        await update.message.reply_text(f"❌ رصيدك لا يكفي. رصيدك: {acc['balance']} جنيه")
        return ConversationHandler.END
    
    # نسب الربح 60% - خسارة 40%
    win_percentage = 60
    is_win = random.randint(1, 100) <= win_percentage
    
    old_balance = acc["balance"]
    
    if is_win:
        # الربح من 5% لـ 50% من قيمة الاستثمار
        profit_percent = random.randint(5, 50)
        profit = int(bet * profit_percent / 100)
        acc["balance"] += profit
        result_text = f"📈 **استثمار ناجح!**\n\n💰 المبلغ المستثمر: {bet} جنيه\n📈 نسبة الربح: {profit_percent}%\n💵 المكسب: +{profit} جنيه"
    else:
        # الخسارة من 10% لـ 60% من قيمة الاستثمار
        loss_percent = random.randint(10, 60)
        loss = int(bet * loss_percent / 100)
        acc["balance"] -= loss
        result_text = f"📉 **استثمار خاسر!**\n\n💰 المبلغ المستثمر: {bet} جنيه\n📉 نسبة الخسارة: {loss_percent}%\n💸 الخسارة: -{loss} جنيه"
    
    save_json(BANK_FILE, bank_data)
    set_cooldown(user_id, "invest")
    
    await update.message.reply_text(
        f"{result_text}\n\n📊 الرصيد قبل: {old_balance} جنيه\n📈 الرصيد بعد: {acc['balance']} جنيه",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# لعبة مضاربة - رهان بمبلغ
async def fight_start(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return ConversationHandler.END
    
    can, remain = check_cooldown(user_id, "fight", 15)
    if not can:
        await update.message.reply_text(f"⏳ استنى {remain} دقيقة للمضاربة")
        return ConversationHandler.END
    
    await update.message.reply_text("⚔️ **لعبة المضاربة**\n\nأرسل المبلغ اللي عايز تراهن بيه:\n(الحد الأدنى 200 جنيه)")
    return GAME_BET_STATE

async def fight_bet(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    try:
        bet = int(update.message.text.strip())
        if bet < 200:
            await update.message.reply_text("❌ الحد الأدنى للمضاربة 200 جنيه")
            return GAME_BET_STATE
    except:
        await update.message.reply_text("❌ أرسل رقماً صحيحاً")
        return GAME_BET_STATE
    
    acc = bank_data[key]
    if acc["balance"] < bet:
        await update.message.reply_text(f"❌ رصيدك لا يكفي. رصيدك: {acc['balance']} جنيه")
        return ConversationHandler.END
    
    # نسب الفوز 50% - خسارة 50%
    win_percentage = 50
    is_win = random.randint(1, 100) <= win_percentage
    
    old_balance = acc["balance"]
    
    if is_win:
        # الربح من 20% لـ 100% من قيمة الرهان
        profit_percent = random.randint(20, 100)
        profit = int(bet * profit_percent / 100)
        acc["balance"] += profit
        result_text = f"⚔️ **انتصار!**\n\n💰 رهانك: {bet} جنيه\n📈 نسبة الربح: {profit_percent}%\n💵 المكسب: +{profit} جنيه"
    else:
        # الخسارة من 30% لـ 90% من قيمة الرهان
        loss_percent = random.randint(30, 90)
        loss = int(bet * loss_percent / 100)
        acc["balance"] -= loss
        result_text = f"💀 **هزيمة!**\n\n💰 رهانك: {bet} جنيه\n📉 نسبة الخسارة: {loss_percent}%\n💸 الخسارة: -{loss} جنيه"
    
    save_json(BANK_FILE, bank_data)
    set_cooldown(user_id, "fight")
    
    await update.message.reply_text(
        f"{result_text}\n\n📊 الرصيد قبل: {old_balance} جنيه\n📈 الرصيد بعد: {acc['balance']} جنيه",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== لعبة الأعلام (22 دولة عربية) ==========
FLAGS = {
    "🇪🇬": "مصر",
    "🇸🇦": "السعودية",
    "🇦🇪": "الإمارات",
    "🇰🇼": "الكويت",
    "🇶🇦": "قطر",
    "🇧🇭": "البحرين",
    "🇴🇲": "عمان",
    "🇯🇴": "الأردن",
    "🇵🇸": "فلسطين",
    "🇱🇧": "لبنان",
    "🇮🇶": "العراق",
    "🇸🇾": "سوريا",
    "🇾🇪": "اليمن",
    "🇸🇩": "السودان",
    "🇱🇾": "ليبيا",
    "🇹🇳": "تونس",
    "🇩🇿": "الجزائر",
    "🇲🇦": "المغرب",
    "🇲🇷": "موريتانيا",
    "🇸🇴": "الصومال",
    "🇩🇯": "جيبوتي",
    "🇰🇲": "جزر القمر"
}

async def flag_game(update, context):
    flag_emoji = random.choice(list(FLAGS.keys()))
    correct_country = FLAGS[flag_emoji]
    context.user_data['flag_emoji'] = flag_emoji
    context.user_data['flag_correct'] = correct_country
    
    await update.message.reply_text(
        f"🏳️ **لعبة الأعلام**\n\n{flag_emoji}\n\nما اسم هذه الدولة؟"
    )

async def check_flag_answer(update, context):
    if 'flag_correct' not in context.user_data:
        return
    
    user_answer = update.message.text.strip()
    correct = context.user_data['flag_correct']
    flag_emoji = context.user_data['flag_emoji']
    
    if user_answer == correct:
        user_id = update.effective_user.id
        key = str(user_id)
        if key in bank_data:
            old_balance = bank_data[key]["balance"]
            bank_data[key]["balance"] += 50
            save_json(BANK_FILE, bank_data)
            await update.message.reply_text(
                f"✅ **صحيح!**\n\n"
                f"🏳️ العلم: {flag_emoji}\n"
                f"🌍 الدولة: {correct}\n\n"
                f"💰 المكسب: +50 جنيه\n"
                f"📊 الرصيد قبل: {old_balance} جنيه\n"
                f"📈 الرصيد بعد: {bank_data[key]['balance']} جنيه",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ صحيح! العلم لـ {correct}\n⚠️ ليس لديك حساب لحفظ المكسب")
    else:
        await update.message.reply_text(f"❌ **خطأ!**\n\n🏳️ العلم: {flag_emoji}\n🌍 الإجابة الصحيحة: {correct}")
    
    del context.user_data['flag_emoji']
    del context.user_data['flag_correct']

# ========== لعبة تخمين الرقم ==========
async def guess_game(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return
    
    can, remain = check_cooldown(user_id, "guess", 5)
    if not can:
        await update.message.reply_text(f"⏳ استنى {remain} دقيقة للتخمين")
        return
    
    number = random.randint(1, 10)
    context.user_data['guess_number'] = number
    context.user_data['guess_user'] = user_id
    set_cooldown(user_id, "guess")
    await update.message.reply_text("🔢 **خمن الرقم**\n\nخمن رقم من 1 إلى 10:")

async def check_guess_answer(update, context):
    if 'guess_number' not in context.user_data:
        return
    
    user_id = update.effective_user.id
    if context.user_data.get('guess_user') != user_id:
        return
    
    try:
        user_guess = int(update.message.text.strip())
        correct = context.user_data['guess_number']
        
        if user_guess == correct:
            key = str(user_id)
            if key in bank_data:
                old_balance = bank_data[key]["balance"]
                bank_data[key]["balance"] += 30
                save_json(BANK_FILE, bank_data)
                await update.message.reply_text(
                    f"🎉 **صحيح!**\n\n"
                    f"🔢 الرقم كان: {correct}\n"
                    f"💰 المكسب: +30 جنيه\n"
                    f"📊 الرصيد قبل: {old_balance} جنيه\n"
                    f"📈 الرصيد بعد: {bank_data[key]['balance']} جنيه",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(f"🎉 صحيح! الرقم كان {correct}")
        else:
            await update.message.reply_text(f"❌ **خطأ!**\n\n🔢 الرقم الصحيح كان: {correct}")
    except:
        pass
    
    del context.user_data['guess_number']
    del context.user_data['guess_user']

# ========== لعبة حسابية ==========
async def math_game(update, context):
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)
    op = random.choice(['+', '-', '*'])
    
    if op == '+':
        answer = num1 + num2
        question = f"{num1} + {num2}"
    elif op == '-':
        answer = num1 - num2
        question = f"{num1} - {num2}"
    else:
        answer = num1 * num2
        question = f"{num1} × {num2}"
    
    context.user_data['math_answer'] = answer
    context.user_data['math_user'] = update.effective_user.id
    await update.message.reply_text(f"🧮 **حل المسألة**\n\n{question} = ؟")

async def check_math_answer(update, context):
    if 'math_answer' not in context.user_data:
        return
    
    user_id = update.effective_user.id
    if context.user_data.get('math_user') != user_id:
        return
    
    try:
        user_ans = int(update.message.text.strip())
        correct = context.user_data['math_answer']
        
        if user_ans == correct:
            key = str(user_id)
            if key in bank_data:
                gain = random.randint(20, 80)
                old_balance = bank_data[key]["balance"]
                bank_data[key]["balance"] += gain
                save_json(BANK_FILE, bank_data)
                await update.message.reply_text(
                    f"✅ **إجابة صحيحة!**\n\n"
                    f"💰 المكسب: +{gain} جنيه\n"
                    f"📊 الرصيد قبل: {old_balance} جنيه\n"
                    f"📈 الرصيد بعد: {bank_data[key]['balance']} جنيه",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(f"✅ إجابة صحيحة!")
        else:
            await update.message.reply_text(f"❌ **خطأ!**\n\nالإجابة الصحيحة: {correct}")
    except:
        pass
    
    del context.user_data['math_answer']
    del context.user_data['math_user']

# ========== لعبة حجر ورقة مقص ==========
async def rps_game(update, context):
    keyboard = [
        [InlineKeyboardButton("🗻 حجر", callback_data="rps_حجر")],
        [InlineKeyboardButton("📄 ورقة", callback_data="rps_ورقة")],
        [InlineKeyboardButton("✂️ مقص", callback_data="rps_مقص")]
    ]
    await update.message.reply_text("🎮 **حجر ورقة مقص**\n\nاختر:", reply_markup=InlineKeyboardMarkup(keyboard))

async def rps_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_choice = query.data.split("_")[1]
    bot_choice = random.choice(["حجر", "ورقة", "مقص"])
    
    if user_choice == bot_choice:
        result = "تعادل 🤝"
        gain = 0
    elif (user_choice == "حجر" and bot_choice == "مقص") or \
         (user_choice == "مقص" and bot_choice == "ورقة") or \
         (user_choice == "ورقة" and bot_choice == "حجر"):
        result = "فزت 🎉"
        gain = 30
    else:
        result = "خسرت 😢"
        gain = -20
    
    user_id = query.from_user.id
    key = str(user_id)
    
    if gain != 0 and key in bank_data:
        old_balance = bank_data[key]["balance"]
        bank_data[key]["balance"] += gain
        save_json(BANK_FILE, bank_data)
        await query.edit_message_text(
            f"🗻 **حجر ورقة مقص**\n\n"
            f"أنت: {user_choice}\n"
            f"البوت: {bot_choice}\n\n"
            f"{result}\n"
            f"{'+' + str(gain) if gain > 0 else gain} جنيه\n\n"
            f"📊 الرصيد قبل: {old_balance} جنيه\n"
            f"📈 الرصيد بعد: {bank_data[key]['balance']} جنيه",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            f"🗻 **حجر ورقة مقص**\n\n"
            f"أنت: {user_choice}\n"
            f"البوت: {bot_choice}\n\n"
            f"{result}",
            parse_mode="Markdown"
        )

# ========== هدية ومكافأة ==========
async def gift(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return
    
    can, remain = check_cooldown(user_id, "gift", 15)
    if not can:
        await update.message.reply_text(f"⏳ استنى {remain} دقيقة عشان تاخد هدية جديدة")
        return
    
    amount = random.randint(50, 500)
    old_balance = bank_data[key]["balance"]
    bank_data[key]["balance"] += amount
    save_json(BANK_FILE, bank_data)
    set_cooldown(user_id, "gift")
    
    await update.message.reply_text(
        f"🎁 **هدية!**\n\n"
        f"💰 المبلغ: +{amount} جنيه\n"
        f"📊 الرصيد قبل: {old_balance} جنيه\n"
        f"📈 الرصيد بعد: {bank_data[key]['balance']} جنيه",
        parse_mode="Markdown"
    )

async def daily_reward(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد'")
        return
    
    can, remain = check_cooldown(user_id, "daily", 1440)
    if not can:
        hours = remain // 60
        mins = remain % 60
        await update.message.reply_text(f"⏳ استنى {hours} ساعة و {mins} دقيقة للمكافأة اليومية")
        return
    
    amount = random.randint(500, 2000)
    old_balance = bank_data[key]["balance"]
    bank_data[key]["balance"] += amount
    save_json(BANK_FILE, bank_data)
    set_cooldown(user_id, "daily")
    
    await update.message.reply_text(
        f"🎉 **المكافأة اليومية!**\n\n"
        f"💰 المبلغ: +{amount} جنيه\n"
        f"📊 الرصيد قبل: {old_balance} جنيه\n"
        f"📈 الرصيد بعد: {bank_data[key]['balance']} جنيه",
        parse_mode="Markdown"
    )

async def steal(update, context):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة الشخص اللي عاوز تسرقه")
        return
    
    target = update.message.reply_to_message.from_user
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if target.id == user_id:
        await update.message.reply_text("❌ لا يمكنك سرقة نفسك")
        return
    
    can, remain = check_cooldown(user_id, "steal", 10)
    if not can:
        await update.message.reply_text(f"⏳ استنى {remain} دقيقة عشان تقدر تسرق تاني")
        return
    
    target_key = str(target.id)
    thief_key = str(user_id)
    
    if thief_key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب")
        return
    if target_key not in bank_data:
        await update.message.reply_text("❌ المستخدم ليس لديه حساب")
        return
    
    target_acc = bank_data[target_key]
    if target_acc["balance"] < 1000:
        await update.message.reply_text("❌ الهدف ليس لديه رصيد كافٍ للسرقة (يحتاج أكثر من 1000)")
        return
    
    stolen = random.randint(1, min(3000, target_acc["balance"]))
    old_thief_balance = bank_data[thief_key]["balance"]
    old_target_balance = target_acc["balance"]
    
    target_acc["balance"] -= stolen
    bank_data[thief_key]["balance"] += stolen
    save_json(BANK_FILE, bank_data)
    set_cooldown(user_id, "steal")
    
    keyboard = []
    if update.effective_chat.username:
        keyboard = [[InlineKeyboardButton("🎯 اذهب للجروب", url=f"https://t.me/{update.effective_chat.username}")]]
    
    await update.message.reply_text(
        f"🕵️ **سرقة!**\n\n"
        f"💰 المبلغ المسروق: {stolen} جنيه\n"
        f"👤 من: {target.first_name}\n\n"
        f"📊 رصيدك قبل: {old_thief_balance} جنيه\n"
        f"📈 رصيدك بعد: {bank_data[thief_key]['balance']} جنيه",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )
    
    try:
        await update.message.bot.send_message(
            target.id,
            f"⚠️ **تنبيه!**\n\n"
            f"🕵️ {update.effective_user.first_name} سرق {stolen} جنيه من حسابك\n"
            f"📍 في جروب: {update.effective_chat.title}\n"
            f"📊 رصيدك قبل: {old_target_balance} جنيه\n"
            f"📉 رصيدك بعد: {target_acc['balance']} جنيه",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 اذهب للجروب", url=f"https://t.me/{update.effective_chat.username}")]]) if update.effective_chat.username else None
        )
    except:
        pass

# ========== أوامر الإدارة ==========
async def warn(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    await add_warning(chat_id, target.id, target.first_name, "تحذير من مشرف", update)

async def unwarn(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    key = f"{chat_id}_{target.id}"
    
    if warns_data.get(key, 0) > 0:
        warns_data[key] -= 1
        save_json(WARNS_FILE, warns_data)
        await update.message.reply_text(f"✅ تم إلغاء آخر تحذير لـ {target.first_name}")
    else:
        await update.message.reply_text(f"✅ {target.first_name} ليس لديه تحذيرات")

async def my_warns(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    key = f"{chat_id}_{user_id}"
    count = warns_data.get(key, 0)
    await update.message.reply_text(f"📊 عدد تحذيراتك: {count}/3")

async def ban(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.ban_member(target.id)
        await update.message.reply_text(f"✅ تم حظر {target.first_name}")
    except:
        await update.message.reply_text("❌ فشل الحظر")

async def unban(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.unban_member(target.id)
        await update.message.reply_text(f"✅ تم إلغاء حظر {target.first_name}")
    except:
        await update.message.reply_text("❌ فشل إلغاء الحظر")

async def mute(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.restrict_member(target.id, ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 تم كتم {target.first_name}")
    except:
        await update.message.reply_text("❌ فشل الكتم")

async def unmute(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.restrict_member(target.id, ChatPermissions(can_send_messages=True))
        await update.message.reply_text(f"🔊 تم فك الكتم عن {target.first_name}")
    except:
        await update.message.reply_text("❌ فشل فك الكتم")

async def promote_admin(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not is_owner(user_id, chat_id):
        await update.message.reply_text("⛔ رفع المشرفين للمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.promote_member(
            target.id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_promote_members=False,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        await update.message.reply_text(f"✅ تم رفع {target.first_name} مشرفاً")
    except:
        await update.message.reply_text("❌ فشل رفع المشرف")

async def demote_admin(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not is_owner(user_id, chat_id):
        await update.message.reply_text("⛔ تنزيل المشرفين للمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.promote_member(
            target.id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        await update.message.reply_text(f"✅ تم تنزيل {target.first_name} من المشرفين")
    except:
        await update.message.reply_text("❌ فشل تنزيل المشرف")

async def promote_vip(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    key = f"{chat_id}_{target.id}"
    specials_data[key] = True
    save_json(SPECIAL_FILE, specials_data)
    await update.message.reply_text(f"⭐ تم رفع {target.first_name} مميزاً")

async def demote_vip(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    key = f"{chat_id}_{target.id}"
    specials_data[key] = False
    save_json(SPECIAL_FILE, specials_data)
    await update.message.reply_text(f"⬇️ تم تنزيل {target.first_name} من المميزين")

async def kick(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.ban_member(target.id)
        await update.effective_chat.unban_member(target.id)
        await update.message.reply_text(f"✅ تم طرد {target.first_name}")
    except:
        await update.message.reply_text("❌ فشل الطرد")

async def restrict(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.restrict_member(
            target.id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        await update.message.reply_text(f"🔒 تم تقييد {target.first_name}")
    except:
        await update.message.reply_text("❌ فشل التقييد")

async def close_chat(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    try:
        await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
        await update.message.reply_text("🔒 تم غلق الشات")
    except:
        await update.message.reply_text("❌ فشل الغلق")

async def open_chat(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    try:
        await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True))
        await update.message.reply_text("🔓 تم فتح الشات")
    except:
        await update.message.reply_text("❌ فشل الفتح")

async def settings(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return
    
    block_links = settings_data.get(f"{chat_id}_block_links", True)
    anti_spam = settings_data.get(f"{chat_id}_anti_spam", True)
    block_badwords = settings_data.get(f"{chat_id}_block_badwords", True)
    welcome = settings_data.get(f"{chat_id}_welcome", True)
    
    await update.message.reply_text(
        f"⚙️ **إعدادات الحماية**\n\n"
        f"🚫 منع الروابط: {'✅ مفعل' if block_links else '❌ معطل'}\n"
        f"🔄 منع التكرار: {'✅ مفعل' if anti_spam else '❌ معطل'}\n"
        f"🤬 منع الشتم: {'✅ مفعل' if block_badwords else '❌ معطل'}\n"
        f"👋 الترحيب: {'✅ مفعل' if welcome else '❌ معطل'}\n\n"
        f"📝 **لتغيير الإعدادات:**\n"
        f"• `تفعيل منع الروابط` / `تعطيل منع الروابط`\n"
        f"• `تفعيل منع التكرار` / `تعطيل منع التكرار`\n"
        f"• `تفعيل منع الشتم` / `تعطيل منع الشتم`\n"
        f"• `تفعيل الترحيب` / `تعطيل الترحيب`",
        parse_mode="Markdown"
    )

async def toggle_setting(update, context, setting_name, setting_key):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (await is_admin(update, user_id) or is_owner(user_id, chat_id)):
        await update.message.reply_text("⛔ للأدمن والمالك فقط")
        return False
    
    current = settings_data.get(f"{chat_id}_{setting_key}", True)
    new_val = not current
    settings_data[f"{chat_id}_{setting_key}"] = new_val
    save_json(SETTINGS_FILE, settings_data)
    
    status = "✅ تم تفعيل" if new_val else "❌ تم تعطيل"
    await update.message.reply_text(f"{status} {setting_name}")
    return True

# ========== أوامر المطور (مخفية) ==========
async def dev_add_balance_start(update, context):
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("⛔ أمر غير معروف")
        return ConversationHandler.END
    
    await update.message.reply_text("💰 أرسل المبلغ اللي عايز تضيفه لحسابك:")
    return AMOUNT_STATE

async def dev_add_balance_amount(update, context):
    if update.effective_user.id != DEVELOPER_ID:
        return ConversationHandler.END
    
    try:
        amount = int(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ المبلغ غير صحيح! أرسل رقماً موجباً")
        return AMOUNT_STATE
    
    dev_key = str(DEVELOPER_ID)
    if dev_key not in bank_data:
        bank_data[dev_key] = {
            "user_id": DEVELOPER_ID,
            "username": "MaroZayed1",
            "first_name": "المطور",
            "account_number": str(random.randint(100000, 999999)),
            "balance": amount,
            "job": "مطور",
            "last_salary": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
    else:
        bank_data[dev_key]["balance"] += amount
    
    save_json(BANK_FILE, bank_data)
    await update.message.reply_text(f"✅ تم إضافة {amount} جنيه إلى حسابك\n💰 رصيدك الآن: {bank_data[dev_key]['balance']} جنيه")
    return ConversationHandler.END

async def dev_giftcode_start(update, context):
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("⛔ أمر غير معروف")
        return ConversationHandler.END
    
    await update.message.reply_text("🎁 أرسل المبلغ اللي عايزه في الكود:")
    return GIFT_AMOUNT_STATE

async def dev_giftcode_amount(update, context):
    if update.effective_user.id != DEVELOPER_ID:
        return ConversationHandler.END
    
    try:
        amount = int(update.message.text.strip())
        if amount <= 0:
            raise ValueError
        context.user_data['gift_amount'] = amount
    except:
        await update.message.reply_text("❌ المبلغ غير صحيح! أرسل رقماً موجباً")
        return GIFT_AMOUNT_STATE
    
    await update.message.reply_text("👥 أرسل عدد الأشخاص اللي يقدر يستخدموا الكود:")
    return GIFT_USES_STATE

async def dev_giftcode_uses(update, context):
    if update.effective_user.id != DEVELOPER_ID:
        return ConversationHandler.END
    
    try:
        max_uses = int(update.message.text.strip())
        if max_uses <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ العدد غير صحيح! أرسل رقماً موجباً")
        return GIFT_USES_STATE
    
    amount = context.user_data['gift_amount']
    code = f"MARO{random.randint(10000, 99999)}"
    
    gift_codes = load_json("gift_codes.json")
    gift_codes[code] = {
        "amount": amount,
        "max_uses": max_uses,
        "used_count": 0
    }
    save_json("gift_codes.json", gift_codes)
    
    await update.message.reply_text(
        f"🎁 **تم إنشاء الكود!**\n\n"
        f"🔑 الكود: `{code}`\n"
        f"💰 المبلغ: {amount} جنيه\n"
        f"👥 عدد المستخدمين: {max_uses}\n\n"
        f"📝 الأعضاء يستخدموه بكتابة: استخدم كود",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def use_giftcode_start(update, context):
    user_id = update.effective_user.id
    key = str(user_id)
    
    if key not in bank_data:
        await update.message.reply_text("❌ ليس لديك حساب! اكتب 'حساب جديد' أولاً")
        return ConversationHandler.END
    
    await update.message.reply_text("🎁 **استخدام كود هدية**\n\nأرسل الكود الآن:")
    return GIFT_CODE_STATE

async def use_giftcode_code(update, context):
    user_id = update.effective_user.id
    user_key = str(user_id)
    code = update.message.text.strip()
    
    gift_codes = load_json("gift_codes.json")
    
    if code not in gift_codes:
        await update.message.reply_text("❌ كود غير صالح! جرب تاني")
        return GIFT_CODE_STATE
    
    code_data = gift_codes[code]
    
    if code_data["used_count"] >= code_data["max_uses"]:
        await update.message.reply_text("❌ هذا الكود انتهت صلاحيته")
        return ConversationHandler.END
    
    old_balance = bank_data[user_key]["balance"]
    bank_data[user_key]["balance"] += code_data["amount"]
    code_data["used_count"] += 1
    gift_codes[code] = code_data
    save_json("gift_codes.json", gift_codes)
    save_json(BANK_FILE, bank_data)
    
    await update.message.reply_text(
        f"🎉 **تم استخدام الكود بنجاح!**\n\n"
        f"💰 المبلغ: +{code_data['amount']} جنيه\n"
        f"📊 رصيدك قبل: {old_balance} جنيه\n"
        f"📈 رصيدك بعد: {bank_data[user_key]['balance']} جنيه",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== عرض الأوامر ==========
async def show_all_commands(update, context):
    await update.message.reply_text(
        f"📋 **قائمة أوامر {BOT_NAME}** 📋\n\n"
        f"**👑 أوامر المالك:**\n"
        f"• `رفع مشرف` - رد على رسالة العضو\n"
        f"• `تنزيل مشرف` - رد على رسالة العضو\n\n"
        f"**🛡️ أوامر الأدمن والمالك:**\n"
        f"• `كتم` / `فك كتم` - رد على رسالة العضو\n"
        f"• `طرد` / `تقييد` - رد على رسالة العضو\n"
        f"• `تحذير` / `الغاء تحذير` - رد على رسالة العضو\n"
        f"• `رفع مميز` / `تنزيل مميز` - رد على رسالة العضو\n"
        f"• `غلق` / `فتح` - غلق/فتح الشات\n"
        f"• `اعدادات` - عرض إعدادات الحماية\n\n"
        f"**👤 أوامر الأعضاء:**\n"
        f"• `حساب جديد` - إنشاء حساب بنكي\n"
        f"• `حسابي` - عرض معلومات حسابك\n"
        f"• `راتبي` - صرف الراتب (كل 15 دقيقة)\n"
        f"• `بقشيش` - هدية (كل 15 دقيقة)\n"
        f"• `هدية` / `مكافأة` - هدايا يومية\n"
        f"• `تحويل` - تحويل فلوس برقم الحساب\n"
        f"• `سرقه` - رد على رسالة الشخص\n"
        f"• `رتبتي` / `تحذيراتي`\n\n"
        f"**🎮 الألعاب:**\n"
        f"• `حظ` - راهن بمبلغ (كل 10 دقائق)\n"
        f"• `استثمار` - استثمر بمبلغ (كل 10 دقائق)\n"
        f"• `مضاربة` - راهن بمبلغ (كل 15 دقيقة)\n"
        f"• `تخمين` - خمن الرقم (كل 5 دقائق)\n"
        f"• `علم` - لعبة أعلام الدول\n"
        f"• `حساب` - مسائل حسابية\n"
        f"• `حجر` - حجر ورقة مقص\n\n"
        f"📌 **ملاحظة:** البوت لازم يكون مشرف في الجروب",
        parse_mode="Markdown"
    )

# ========== معالج الرسائل الرئيسي ==========
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    first_name = update.message.from_user.first_name
    
    is_admin_user = await is_admin(update, user_id)
    is_special_user = await is_special(chat_id, user_id)
    is_owner_user = is_owner(user_id, chat_id)
    is_dev = (user_id == DEVELOPER_ID)
    
    # التحقق من إجابات الألعاب
    if 'guess_number' in context.user_data:
        await check_guess_answer(update, context)
        return
    
    if 'flag_correct' in context.user_data:
        await check_flag_answer(update, context)
        return
    
    if 'math_answer' in context.user_data:
        await check_math_answer(update, context)
        return
    
    # عرض الأوامر
    if text == 'اوامر':
        await show_all_commands(update, context)
        return
    
    elif text == 'معلومات':
        await update.message.reply_text(
            f"🤖 **بوت {BOT_NAME}** 🛡️\n\n"
            f"📅 **تاريخ الإنشاء:** {CREATION_DATE}\n\n"
            f"🎮 **المميزات:**\n"
            f"• حماية كاملة (كتم - طرد - تحذير)\n"
            f"• منع الروابط والتكرار والشتم\n"
            f"• نظام تحذيرات (3 = طرد)\n"
            f"• نظام بنكي متكامل\n"
            f"• ألعاب رهان: حظ - استثمار - مضاربة\n"
            f"• ألعاب ترفيه: علم - تخمين - حساب - حجر\n\n"
            f"📌 **للاستفسار:** @MaroZayed1",
            parse_mode="Markdown"
        )
        return
    
    # الأوامر الأساسية
    elif text in ['حساب جديد', 'انشاء حساب']:
        await create_account(update, context)
        return
    elif text in ['حسابي', 'رصيدي']:
        await my_account(update, context)
        return
    elif text in ['راتب', 'راتبي']:
        await salary(update, context)
        return
    elif text == 'بقشيش':
        await bakhshish(update, context)
        return
    elif text in ['سرقه', 'سرقة']:
        await steal(update, context)
        return
    elif text == 'هدية':
        await gift(update, context)
        return
    elif text in ['مكافأة', 'يومية']:
        await daily_reward(update, context)
        return
    
    # الألعاب
    elif text == 'حظ':
        await gamble_start(update, context)
        return
    elif text == 'استثمار':
        await invest_start(update, context)
        return
    elif text == 'مضاربة':
        await fight_start(update, context)
        return
    elif text == 'تخمين':
        await guess_game(update, context)
        return
    elif text == 'علم':
        await flag_game(update, context)
        return
    elif text == 'حساب':
        await math_game(update, context)
        return
    elif text in ['حجر', 'ورق', 'مقص']:
        await rps_game(update, context)
        return
    
    # أوامر الإدارة
    elif text == 'رتبتي':
        rank = await get_user_rank(update, user_id, chat_id)
        await update.message.reply_text(f"📊 **رتبتك:** {rank}", parse_mode="Markdown")
        return
    elif text == 'تحذيراتي':
        await my_warns(update, context)
        return
    elif text == 'تحذير':
        await warn(update, context)
        return
    elif text == 'الغاء تحذير':
        await unwarn(update, context)
        return
    elif text == 'حظر':
        await ban(update, context)
        return
    elif text == 'الغاء حظر':
        await unban(update, context)
        return
    elif text == 'كتم':
        await mute(update, context)
        return
    elif text == 'فك كتم':
        await unmute(update, context)
        return
    elif text == 'رفع مشرف':
        await promote_admin(update, context)
        return
    elif text == 'تنزيل مشرف':
        await demote_admin(update, context)
        return
    elif text == 'رفع مميز':
        await promote_vip(update, context)
        return
    elif text == 'تنزيل مميز':
        await demote_vip(update, context)
        return
    elif text == 'طرد':
        await kick(update, context)
        return
    elif text == 'تقييد':
        await restrict(update, context)
        return
    elif text == 'غلق':
        await close_chat(update, context)
        return
    elif text == 'فتح':
        await open_chat(update, context)
        return
    elif text == 'اعدادات':
        await settings(update, context)
        return
    
    # إعدادات الحماية
    elif text == 'تفعيل منع الروابط':
        await toggle_setting(update, context, "منع الروابط", "block_links")
        return
    elif text == 'تعطيل منع الروابط':
        await toggle_setting(update, context, "منع الروابط", "block_links")
        return
    elif text == 'تفعيل منع التكرار':
        await toggle_setting(update, context, "منع التكرار", "anti_spam")
        return
    elif text == 'تعطيل منع التكرار':
        await toggle_setting(update, context, "منع التكرار", "anti_spam")
        return
    elif text == 'تفعيل منع الشتم':
        await toggle_setting(update, context, "منع الشتم", "block_badwords")
        return
    elif text == 'تعطيل منع الشتم':
        await toggle_setting(update, context, "منع الشتم", "block_badwords")
        return
    elif text == 'تفعيل الترحيب':
        await toggle_setting(update, context, "الترحيب", "welcome")
        return
    elif text == 'تعطيل الترحيب':
        await toggle_setting(update, context, "الترحيب", "welcome")
        return
    
    elif text == 'مارو':
        responses = [
            "🎉 أيوه يا باشا، أنا مارو، إزيك؟",
            "🤖 أمرك يا كبير، مارو في خدمتك",
            "🔥 هلا بيك، عايز إيه من مارو؟",
            "💪 مارو موجود، تفضل أمر",
            "✨ لبيه يا غالي، مارو بين إيديك",
        ]
        await update.message.reply_text(random.choice(responses))
        return
    
    # أوامر المطور المخفية
    elif text == 'اضافة رصيد' and is_dev:
        await dev_add_balance_start(update, context)
        return
    elif text == 'كود هدية' and is_dev:
        await dev_giftcode_start(update, context)
        return
    elif text == 'استخدم كود':
        await use_giftcode_start(update, context)
        return
    
    # أمر التحويل
    elif text == 'تحويل':
        await transfer_start(update, context)
        return
    
    # ========== الحماية ==========
    block_badwords = settings_data.get(f"{chat_id}_block_badwords", True)
    if block_badwords and not (is_owner_user or is_admin_user or is_dev):
        if is_bad_word(text):
            try:
                await update.message.delete()
                await add_warning(chat_id, user_id, first_name, "شتم", update)
            except:
                pass
            return
    
    block_links = settings_data.get(f"{chat_id}_block_links", True)
    if block_links and not (is_owner_user or is_admin_user or is_special_user or is_dev):
        if re.search(r'(https?://|www\.|\.com|\.net|\.org|\.xyz|t\.me|telegram\.me)', update.message.text, re.IGNORECASE):
            try:
                await update.message.delete()
                await add_warning(chat_id, user_id, first_name, "نشر رابط", update)
            except:
                pass
            return
    
    anti_spam = settings_data.get(f"{chat_id}_anti_spam", True)
    if anti_spam and not (is_owner_user or is_admin_user or is_dev):
        user_key = f"{chat_id}_{user_id}"
        
        if user_key not in user_messages:
            user_messages[user_key] = []
        
        current = time.time()
        user_messages[user_key] = [msg for msg in user_messages[user_key] if current - msg[1] <= 60]
        
        same_messages = [msg for msg in user_messages[user_key] if msg[0] == text]
        repeat_count = len(same_messages) + 1
        
        if repeat_count >= 4:
            try:
                await update.message.delete()
                if repeat_count == 4:
                    await update.message.reply_text(f"⚠️ {first_name} ممنوع التكرار! تحذير 1/3")
                elif repeat_count == 5:
                    await update.message.reply_text(f"⚠️ {first_name} ممنوع التكرار! تحذير 2/3")
                elif repeat_count == 6:
                    await update.message.reply_text(f"⚠️ {first_name} ممنوع التكرار! تحذير 3/3")
                    await add_warning(chat_id, user_id, first_name, "تكرار", update)
                elif repeat_count >= 7:
                    await update.effective_chat.ban_member(user_id)
                    await update.message.reply_text(f"🚫 {first_name} تم طرده بسبب التكرار المستمر")
            except:
                pass
            return
        
        user_messages[user_key].append([text, current, repeat_count])

# ========== ترحيب بالأعضاء الجدد ==========
async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    welcome = settings_data.get(f"{chat_id}_welcome", True)
    
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            try:
                chat_admins = await update.effective_chat.get_administrators()
                for admin in chat_admins:
                    if admin.status == 'creator':
                        settings_data[f"{chat_id}_owner"] = admin.user.id
                        save_json(SETTINGS_FILE, settings_data)
                        break
            except:
                pass
            continue
        
        if not welcome:
            continue
        
        welcome_texts = [
            f"🎉 أهلاً بك {member.first_name} في المجموعة!",
            f"✨ نورت الجروب يا {member.first_name} 🤖",
            f"🔥 يا مرحباً {member.first_name}",
        ]
        await update.message.reply_text(random.choice(welcome_texts))

# ========== دوال الكولباك ==========
async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"🤖 **بوت {BOT_NAME}**\n\n"
        f"بوت متكامل لإدارة الجروبات والألعاب الاقتصادية.\n"
        f"📅 تاريخ الإنشاء: {CREATION_DATE}\n\n"
        f"🎮 يحتوي على ألعاب رهان وألعاب ترفيهية",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]])
    )

async def games_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎲 حظ", callback_data="game_gamble")],
        [InlineKeyboardButton("📈 استثمار", callback_data="game_invest")],
        [InlineKeyboardButton("⚔️ مضاربة", callback_data="game_fight")],
        [InlineKeyboardButton("🏳️ أعلام", callback_data="game_flag")],
        [InlineKeyboardButton("🧮 أرقام", callback_data="game_math")],
        [InlineKeyboardButton("✂️ حجر ورقة مقص", callback_data="game_rps")],
        [InlineKeyboardButton("🔢 تخمين", callback_data="game_guess")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]
    ]
    await query.edit_message_text("🎮 **اختر اللعبة:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def my_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    key = str(user_id)
    
    if key not in bank_data:
        await query.edit_message_text("❌ ليس لديك حساب! اكتب 'حساب جديد'", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]]))
        return
    
    acc = bank_data[key]
    text = (
        f"🏦 **معلومات حسابك**\n\n"
        f"👤 الاسم: {acc['first_name']}\n"
        f"📝 اليوزر: @{acc['username'] if acc['username'] != str(user_id) else 'لا يوجد'}\n"
        f"🆔 الايدي: `{acc['user_id']}`\n"
        f"🔢 رقم الحساب: `{acc['account_number']}`\n"
        f"💼 الوظيفة: {acc['job']}\n"
        f"💰 الرصيد: {acc['balance']} جنيه"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]]))

async def help_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📋 **قائمة الأوامر**\n\n"
        "اكتب 'اوامر' في الشات لرؤية جميع الأوامر",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]])
    )

async def back_to_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📜 نبذة", callback_data="about")],
        [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
        [InlineKeyboardButton("📊 حسابي", callback_data="my_account")],
        [InlineKeyboardButton("📋 الأوامر", callback_data="help_menu")]
    ]
    await query.edit_message_text("🏠 **القائمة الرئيسية**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def game_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    game = query.data.split("_")[1]
    
    if game == "gamble":
        await gamble_start(update, context)
    elif game == "invest":
        await invest_start(update, context)
    elif game == "fight":
        await fight_start(update, context)
    elif game == "flag":
        await flag_game(update, context)
    elif game == "math":
        await math_game(update, context)
    elif game == "rps":
        await rps_game(update, context)
    elif game == "guess":
        await guess_game(update, context)
    
    try:
        await query.message.delete()
    except:
        pass

# ========== تشغيل البوت ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # أمر start
    app.add_handler(CommandHandler("start", cmd_start))
    
    # محادثة التحويل
    conv_transfer = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^تحويل$'), transfer_start)],
        states={
            TRANSFER_ACCOUNT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_get_account)],
            TRANSFER_AMOUNT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_get_amount)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_transfer)
    
    # محادثة حظ
    conv_gamble = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^حظ$'), gamble_start)],
        states={GAME_BET_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, gamble_bet)]},
        fallbacks=[],
    )
    app.add_handler(conv_gamble)
    
    # محادثة استثمار
    conv_invest = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^استثمار$'), invest_start)],
        states={GAME_BET_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, invest_bet)]},
        fallbacks=[],
    )
    app.add_handler(conv_invest)
    
    # محادثة مضاربة
    conv_fight = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^مضاربة$'), fight_start)],
        states={GAME_BET_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, fight_bet)]},
        fallbacks=[],
    )
    app.add_handler(conv_fight)
    
    # محادثة إضافة رصيد للمطور
    dev_add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^اضافة رصيد$') & filters.User(user_id=DEVELOPER_ID), dev_add_balance_start)],
        states={AMOUNT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dev_add_balance_amount)]},
        fallbacks=[],
    )
    app.add_handler(dev_add_conv)
    
    # محادثة إنشاء كود هدية للمطور
    dev_gift_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^كود هدية$') & filters.User(user_id=DEVELOPER_ID), dev_giftcode_start)],
        states={
            GIFT_AMOUNT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dev_giftcode_amount)],
            GIFT_USES_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dev_giftcode_uses)],
        },
        fallbacks=[],
    )
    app.add_handler(dev_gift_conv)
    
    # محادثة استخدام كود هدية
    use_gift_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^استخدم كود$'), use_giftcode_start)],
        states={GIFT_CODE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, use_giftcode_code)]},
        fallbacks=[],
    )
    app.add_handler(use_gift_conv)
    
    # معالج الرسائل الرئيسي
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    # أحداث الجروب
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    
    # معالجات الكولباك
    app.add_handler(CallbackQueryHandler(about_callback, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(games_menu_callback, pattern="^games_menu$"))
    app.add_handler(CallbackQueryHandler(my_account_callback, pattern="^my_account$"))
    app.add_handler(CallbackQueryHandler(help_menu_callback, pattern="^help_menu$"))
    app.add_handler(CallbackQueryHandler(back_to_start_callback, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(game_callback_handler, pattern="^game_"))
    app.add_handler(CallbackQueryHandler(rps_callback_handler, pattern="^rps_"))
    
    print("=" * 50)
    print(f"✅ بوت {BOT_NAME} شغال!")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()