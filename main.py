import logging
import os
import json
import re
import time
from dotenv import load_dotenv
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, filters, ContextTypes, ChatMemberHandler, CommandHandler

from games import create_account, my_account, send_money, salary, gamble, invest, guess, toggle_games, bakhshish, steal, flag_game, math_game, rps_game, roulette_game, dice_game_free, check_game_answers

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# المالك الافتراضي
DEFAULT_OWNER_ID = 5415189680

# ملفات التخزين
WARNS_FILE = "warns.json"
SPECIAL_FILE = "specials.json"
SETTINGS_FILE = "settings.json"

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
    return settings_data.get(f"{chat_id}_owner", DEFAULT_OWNER_ID)

def is_owner(user_id, chat_id):
    return user_id == get_chat_owner(chat_id)

async def is_admin(update, user_id):
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

async def is_special(chat_id, user_id):
    key = f"{chat_id}_{user_id}"
    return specials_data.get(key, False)

async def get_user_rank(update, user_id, chat_id):
    if is_owner(user_id, chat_id):
        return "👑 **المالك**\n\n✅ جميع الصلاحيات\n✅ رفع/تنزيل مشرفين\n✅ رفع/تنزيل مميزين\n✅ كتم/طرد/تقييد/تحذير الكل"
    
    try:
        member = await update.effective_chat.get_member(user_id)
        if member.status == 'administrator':
            return "🛡️ **مشرف**\n\n✅ كتم/طرد/تقييد/تحذير الأعضاء\n✅ رفع/تنزيل مميزين\n✅ غلق/فتح الشات\n❌ لا يستطيع رفع/تنزيل مشرفين"
    except:
        pass
    
    if await is_special(chat_id, user_id):
        return "⭐ **مميز**\n\n✅ إرسال روابط (حتى لو ممنوعة)\n✅ حماية من التحذير على التكرار\n❌ ليس لديه صلاحيات إدارة"
    
    return "👤 **عضو عادي**\n\n❌ ليس لديه أي صلاحيات إدارة\n❌ ممنوع منه إرسال روابط\n❌ ممنوع منه التكرار"

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

# ========== ترحيب في الخاص عند /start ==========
async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name
    await update.message.reply_text(f"🎉 أهلاً بك يا {first_name}! أنا بوت مارو، أضفني إلى جروبك وارفعني مشرف عشان أحمي الجروب 🤖")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip().lower()
    current_time = time.time()
    first_name = update.message.from_user.first_name
    
    is_admin_user = await is_admin(update, user_id)
    is_special_user = await is_special(chat_id, user_id)
    is_owner_user = is_owner(user_id, chat_id)
    
    # ========== التحقق من إجابات الألعاب أولاً ==========
    if text and not text.startswith(('حساب', 'راتب', 'حظ', 'استثمار', 'تخمين', 'تحويل', 'بقشيش', 'سرقه', 'علم', 'نرد', 'حجر', 'ورق', 'مقص', 'روليت', 'الالعاب', 'اعدادات', 'تفعيل', 'تعطيل', 'رتبتي', 'اوامر', 'طرد', 'كتم', 'فك', 'الغاء', 'تقييد', 'تحذير', 'تحذيراتي', 'مسح', 'غلق', 'فتح', 'مارو', 'معلومات', 'رفع', 'تنزيل')):
        await check_game_answers(update, context)
        return
    
    # ========== معلومات البوت ==========
    if text == 'معلومات' or text == 'معلومات البوت':
        info_text = f"""
🤖 **بوت مارو** 🛡️

👑 **المطور:** @MaroZayed1
📝 **الاصدار:** 3.0
🎮 **المميزات:**
• حماية كاملة (كتم - طرد - تقييد - تحذير)
• منع الروابط والتكرار والشتم
• نظام تحذيرات (3 = طرد)
• رفع/تنزيل مشرفين ومميزين
• نظام بنكي وألعاب متكامل
• ألعاب ترفيهية (نرد - حظ - استثمار - تخمين - حجرة ورقة مقص - روليت - أعلام - حسابات)

📌 **للاستفسار:** @MaroZayed1
"""
        await update.message.reply_text(info_text, parse_mode="Markdown")
        return
    
    # ========== أوامر الألعاب ==========
    if text == 'حساب جديد':
        await create_account(update, context)
        return
    elif text == 'حسابي':
        await my_account(update, context)
        return
    elif text == 'راتب':
        await salary(update, context)
        return
    elif text.startswith('تحويل'):
        await send_money(update, context)
        return
    elif text.startswith('حظ'):
        await gamble(update, context)
        return
    elif text.startswith('استثمار'):
        await invest(update, context)
        return
    elif text.startswith('تخمين'):
        await guess(update, context)
        return
    elif text.startswith('الالعاب'):
        await toggle_games(update, context)
        return
    elif text == 'بقشيش':
        await bakhshish(update, context)
        return
    elif text.startswith('سرقه'):
        await steal(update, context)
        return
    elif text == 'علم':
        await flag_game(update, context)
        return
    elif text == 'حساب':
        await math_game(update, context)
        return
    elif text.startswith('حجر') or text.startswith('ورق') or text.startswith('مقص'):
        await rps_game(update, context)
        return
    elif text == 'نرد':
        await dice_game_free(update, context)
        return
    elif text.startswith('روليت'):
        await roulette_game(update, context)
        return
    
    # ========== رتبتي ==========
    if text == 'رتبتي':
        rank = await get_user_rank(update, user_id, chat_id)
        await update.message.reply_text(rank, parse_mode="Markdown")
        return
    
    # ========== إعدادات الحماية ==========
    if text == 'اعدادات' or text == 'الاعدادات':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        
        block_links = settings_data.get(f"{chat_id}_block_links", True)
        anti_spam = settings_data.get(f"{chat_id}_anti_spam", True)
        block_badwords = settings_data.get(f"{chat_id}_block_badwords", True)
        welcome = settings_data.get(f"{chat_id}_welcome", True)
        
        status = f"""
⚙️ **إعدادات الحماية**

🚫 منع الروابط: {'✅ مفعل' if block_links else '❌ معطل'}
🔄 منع التكرار: {'✅ مفعل' if anti_spam else '❌ معطل'}
🤬 منع الشتم: {'✅ مفعل' if block_badwords else '❌ معطل'}
👋 الترحيب: {'✅ مفعل' if welcome else '❌ معطل'}

📝 **لتغيير الإعدادات:**
تفعيل منع الروابط - تعطيل منع الروابط
تفعيل منع التكرار - تعطيل منع التكرار
تفعيل منع الشتم - تعطيل منع الشتم
تفعيل الترحيب - تعطيل الترحيب
"""
        await update.message.reply_text(status, parse_mode="Markdown")
        return
    
    # ========== تفعيل/تعطيل الإعدادات ==========
    elif text == 'تفعيل منع الروابط':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_block_links"] = True
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("✅ تم تفعيل منع الروابط")
        return
    
    elif text == 'تعطيل منع الروابط':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_block_links"] = False
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("❌ تم تعطيل منع الروابط")
        return
    
    elif text == 'تفعيل منع التكرار':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_anti_spam"] = True
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("✅ تم تفعيل منع التكرار")
        return
    
    elif text == 'تعطيل منع التكرار':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_anti_spam"] = False
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("❌ تم تعطيل منع التكرار")
        return
    
    elif text == 'تفعيل منع الشتم':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_block_badwords"] = True
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("✅ تم تفعيل منع الشتم")
        return
    
    elif text == 'تعطيل منع الشتم':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_block_badwords"] = False
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("❌ تم تعطيل منع الشتم")
        return
    
    elif text == 'تفعيل الترحيب':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_welcome"] = True
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("✅ تم تفعيل الترحيب")
        return
    
    elif text == 'تعطيل الترحيب':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        settings_data[f"{chat_id}_welcome"] = False
        save_json(SETTINGS_FILE, settings_data)
        await update.message.reply_text("❌ تم تعطيل الترحيب")
        return
    
    # ========== حماية الشتم ==========
    block_badwords = settings_data.get(f"{chat_id}_block_badwords", True)
    if block_badwords and not (is_owner_user or is_admin_user):
        if is_bad_word(text):
            try:
                await update.message.delete()
                await add_warning(chat_id, user_id, first_name, "شتم", update)
            except:
                pass
            return
    
    # ========== منع الروابط ==========
    block_links = settings_data.get(f"{chat_id}_block_links", True)
    if block_links and not (is_owner_user or is_admin_user or is_special_user):
        if re.search(r'(https?://|www\.|\.com|\.net|\.org|\.xyz|t\.me|telegram\.me)', update.message.text, re.IGNORECASE):
            try:
                await update.message.delete()
                await add_warning(chat_id, user_id, first_name, "نشر رابط", update)
            except:
                pass
            return
    
    # ========== منع التكرار ==========
    anti_spam = settings_data.get(f"{chat_id}_anti_spam", True)
    if anti_spam and not (is_owner_user or is_admin_user):
        user_key = f"{chat_id}_{user_id}"
        
        if user_key not in user_messages:
            user_messages[user_key] = []
        
        current = time.time()
        user_messages[user_key] = [msg for msg in user_messages[user_key] if current - msg[1] <= 60]
        
        same_messages = [msg for msg in user_messages[user_key] if msg[0] == text]
        repeat_count = len(same_messages) + 1
        
        if repeat_count == 4:
            try:
                await update.message.delete()
                await update.message.reply_text(f"⚠️ {first_name} ممنوع التكرار! تحذير 1/3")
            except:
                pass
            return
        elif repeat_count == 5:
            try:
                await update.message.delete()
                await update.message.reply_text(f"⚠️ {first_name} ممنوع التكرار! تحذير 2/3")
            except:
                pass
            return
        elif repeat_count == 6:
            try:
                await update.message.delete()
                await update.message.reply_text(f"⚠️ {first_name} ممنوع التكرار! تحذير 3/3")
            except:
                pass
            return
        elif repeat_count >= 7:
            try:
                await update.message.delete()
                await update.effective_chat.ban_member(user_id)
                await update.message.reply_text(f"🚫 {first_name} تم طرده بسبب التكرار المستمر")
            except:
                pass
            return
        
        user_messages[user_key].append([text, current, repeat_count])
    
    # ========== عرض الأوامر ==========
    if text == 'اوامر' or text == 'الاوامر':
        commands_text = """
📋 **قائمة أوامر مارو** 🛡️

👑 **للمالك فقط:**  
رفع مشرف - تنزيل مشرف

🛠️ **للأدمن والمالك:**  
كتم - فك كتم - طرد - تقييد  
تحذير - مسح تحذيرات  
رفع مميز - تنزيل مميز  
غلق - فتح  
اعدادات

👤 **للجميع:**  
تحذيراتي - رتبتي - حساب جديد - حسابي - راتب - حظ - استثمار - تخمين - تحويل - بقشيش - سرقه - علم - حساب - حجر - ورق - مقص - نرد - روليت - معلومات

💡 **طريقة الاستخدام:**  
• اكتب الأمر في رسالة جديدة  
• أو رد على رسالة العضو واكتب الأمر

⚠️ **ملاحظات:**  
• التحذير الثالث = طرد تلقائي  
• لازم البوت يكون أدمن في الجروب
"""
        await update.message.reply_text(commands_text, parse_mode="Markdown")
        return
    
    # ========== باقي الأوامر ==========
    elif text.startswith('رفع مشرف'):
        if not is_owner_user:
            await update.message.reply_text("⛔ رفع المشرفين للمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        try:
            await update.effective_chat.promote_member(target, can_manage_chat=True, can_delete_messages=True, can_restrict_members=True, can_promote_members=False)
            await update.message.reply_text(f"✅ تم رفع العضو كمشرف")
        except:
            await update.message.reply_text(f"❌ فشل رفع المشرف")
        return
    
    elif text.startswith('تنزيل مشرف'):
        if not is_owner_user:
            await update.message.reply_text("⛔ تنزيل المشرفين للمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        try:
            await update.effective_chat.promote_member(target, can_manage_chat=False, can_delete_messages=False, can_restrict_members=False, can_promote_members=False)
            await update.message.reply_text(f"✅ تم تنزيل العضو من المشرفين")
        except:
            await update.message.reply_text(f"❌ فشل تنزيل المشرف")
        return
    
    elif text.startswith('رفع مميز'):
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        key = f"{chat_id}_{target}"
        specials_data[key] = True
        save_json(SPECIAL_FILE, specials_data)
        await update.message.reply_text(f"✅ تم رفع العضو كمميز")
        return
    
    elif text.startswith('تنزيل مميز'):
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        key = f"{chat_id}_{target}"
        specials_data[key] = False
        save_json(SPECIAL_FILE, specials_data)
        await update.message.reply_text(f"✅ تم تنزيل العضو من المميزين")
        return
    
    elif text == 'طرد':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        try:
            await update.effective_chat.ban_member(target)
            await update.message.reply_text("✅ تم طرد العضو")
        except:
            await update.message.reply_text("❌ فشل الطرد")
        return
    
    elif text == 'كتم':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        try:
            await update.effective_chat.restrict_member(target, ChatPermissions(can_send_messages=False))
            await update.message.reply_text("✅ تم كتم العضو")
        except:
            await update.message.reply_text("❌ فشل الكتم")
        return
    
    elif text == 'فك كتم' or text == 'الغاء كتم':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        try:
            await update.effective_chat.restrict_member(target, ChatPermissions(can_send_messages=True))
            await update.message.reply_text("✅ تم فك الكتم عن العضو")
        except:
            await update.message.reply_text("❌ فشل فك الكتم")
        return
    
    elif text == 'تقييد':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        try:
            await update.effective_chat.restrict_member(target, ChatPermissions(can_send_messages=False, can_send_media=False, can_send_other_messages=False))
            await update.message.reply_text("✅ تم تقييد العضو")
        except:
            await update.message.reply_text("❌ فشل التقييد")
        return
    
    elif text == 'تحذير':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.first_name
        await add_warning(chat_id, target, target_name, "تحذير من مشرف", update)
        return
    
    elif text == 'تحذيراتي':
        key = f"{chat_id}_{user_id}"
        count = warns_data.get(key, 0)
        await update.message.reply_text(f"📊 عدد تحذيراتك: {count}/3")
        return
    
    elif text == 'مسح تحذيرات':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ رد على رسالة العضو أولاً")
            return
        target = update.message.reply_to_message.from_user.id
        key = f"{chat_id}_{target}"
        warns_data[key] = 0
        save_json(WARNS_FILE, warns_data)
        await update.message.reply_text(f"✅ تم مسح تحذيرات العضو")
        return
    
    elif text == 'غلق':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        try:
            await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
            await update.message.reply_text("🔒 تم غلق الشات")
        except:
            await update.message.reply_text("❌ فشل الغلق")
        return
    
    elif text == 'فتح':
        if not (is_owner_user or is_admin_user):
            await update.message.reply_text("⛔ للأدمن والمالك فقط")
            return
        try:
            await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True))
            await update.message.reply_text("🔓 تم فتح الشات")
        except:
            await update.message.reply_text("❌ فشل الفتح")
        return
    
    elif text == 'مارو':
        await update.message.reply_text("أنا مارو، تحت أمرك يا باشا 🤖")
        return

# ========== ترحيب بالأعضاء الجدد وتسجيل المالك ==========
async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    welcome = settings_data.get(f"{chat_id}_welcome", True)
    
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            # البوت دخل الجروب - خلي المالك هو اللي ضاف البوت
            try:
                chat_admins = await update.effective_chat.get_administrators()
                for admin in chat_admins:
                    if admin.status == 'creator':
                        settings_data[f"{chat_id}_owner"] = admin.user.id
                        save_json(SETTINGS_FILE, settings_data)
                        print(f"✅ تم تعيين المالك للجروب {chat_id}: {admin.user.id}")
                        break
            except Exception as e:
                print(f"خطأ في تعيين المالك: {e}")
            continue
        
        if not welcome:
            continue
        
        first_name = member.first_name or ""
        last_name = member.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        username = f"@{member.username}" if member.username else "لا يوجد"
        user_id = member.id
        
        welcome_text = f"""🎉 **أهلاً بك في المجموعة** 🎉

👤 **الاسم:** {full_name}
📝 **اليوزر:** {username}
🆔 **الايدي:** `{user_id}`

🤖 **البوت:** @{context.bot.username}
👑 **المطور:** @MaroZayed1

نتمنى لك قضاء وقت ممتع ❤️"""
        
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # أمر start في الخاص
    app.add_handler(CommandHandler("start", start_private))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    
    print("✅ البوت شغال مع جميع أوامر الحماية والألعاب")
    print("✅ المالك يتعرف تلقائياً عند إضافة البوت لأي جروب")
    app.run_polling()

if __name__ == "__main__":
    main()