import telebot
from telebot import types
import sqlite3

# --- আপনার তথ্যসমূহ ---
API_TOKEN = '8981334551:AAGA86NDDSDEBKBAU84icOjEb49rtzn8L6o'
ADMIN_ID = 7411218371
ADMIN_USERNAME = "@numberhubbot_bd"

CHANNELS = ["@NumberHubSupport", "@NumberHubNews", "@NumberHubUpdates"]
# ---------------------

bot = telebot.TeleBot(API_TOKEN)

conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0.0,
    referred_by INTEGER
)
''')
conn.commit()

def is_subscribed(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def send_join_channels(message):
    markup = types.InlineKeyboardMarkup()
    for ch in CHANNELS:
        btn = types.InlineKeyboardButton(text=f"Join {ch}", url=f"[https://t.me/](https://t.me/){ch.replace('@','')}")
        markup.add(btn)
    check_btn = types.InlineKeyboardButton(text="✅ Joined (চেক করুন)", callback_data="check_join")
    markup.add(check_btn)
    
    bot.send_message(
        message.chat.id,
        "⚠️ বট ব্যবহার করতে নিচের ৩টি চ্যানেলে জয়েন করা বাধ্যতামূলক:",
        reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        referred_by = None
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            if ref_id != user_id:
                referred_by = ref_id
                cursor.execute("UPDATE users SET balance = balance + 0.10 WHERE user_id=?", (ref_id,))
                try:
                    bot.send_message(ref_id, "🎉 আপনার রেফারেল লিংকে কেউ যুক্ত হওয়ায় আপনি ৳০.১০ পেয়েছেন!")
                except:
                    pass
        
        cursor.execute("INSERT INTO users (user_id, balance, referred_by) VALUES (?, ?, ?)", (user_id, 0.0, referred_by))
        conn.commit()

    if not is_subscribed(user_id):
        send_join_channels(message)
        return

    send_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if is_subscribed(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি!", show_alert=True)

def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📱 WhatsApp Number (৳0.50)", "💰 Balance")
    markup.add("📥 Deposit (টাকা রিচার্জ)", "🔗 Refer & Earn")
    markup.add("👨‍💻 Admin Support")
    
    bot.send_message(chat_id, "👋 স্বাগতম! নিচের মেনু থেকে অপশন সিলেক্ট করুন:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    
    if not is_subscribed(user_id):
        send_join_channels(message)
        return

    # এখানে মার্কডাউন পার্সার এরর ঠিক করা হয়েছে, মার্কডাউন মোড বাদ দিয়ে
    if message.text == "💰 Balance":
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]
        bot.reply_to(message, f"💳 আপনার বর্তমান ব্যালেন্স: ৳{balance:.2f} BDT")

    elif message.text == "🔗 Refer & Earn":
        bot_username = bot.get_me().username
        ref_link = f"[https://t.me/](https://t.me/){bot_username}?start={user_id}"
        msg = f"📢 আপনার রেফারেল লিংক:\n{ref_link}\n\nপ্রতি সফল রেফারে পাবেন ৳০.১০ BDT।"
        bot.reply_to(message, msg)

    elif message.text == "📥 Deposit (টাকা রিচার্জ)":
        msg = (
            f"💳 টাকা রিচার্জ করার নিয়ম:\n\n"
            f"সর্বনিম্ন রিচার্জ: ৳৫০ BDT\n"
            f"পেমেন্ট মেথড: বিকাশ / নগদ\n\n"
            f"টাকা পাঠাতে এডমিনের সাথে যোগাযোগ করুন:\n"
            f"👤 Owner Username: {ADMIN_USERNAME}\n\n"
            f"টাকা পাঠানোর পর আপনার ইউজার ID ({user_id}) এবং পেমেন্ট প্রুফ এডমিনকে পাঠান।"
        )
        bot.reply_to(message, msg)

    elif message.text == "📱 WhatsApp Number (৳0.50)":
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]
        
        if balance < 0.50:
            bot.reply_to(message, "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! অন্তত ৳০.৫০ পয়সা লাগবে। টাকা রিচার্জ করুন।")
            return

        markup = types.InlineKeyboardMarkup(row_width=2)
        countries = [
            "USA", "UK", "India", "Canada", "Germany", "France", "Russia", "Brazil",
            "Nigeria", "Indonesia", "Pakistan", "Vietnam", "Philippines", "Turkey", "Egypt",
            "Mexico", "Spain", "Italy", "Poland", "Ukraine", "Netherlands", "South Africa",
            "Kenya", "Malaysia", "Thailand", "Argentina", "Colombia", "Romania", "Sweden", "Ghana"
        ]
        buttons = [types.InlineKeyboardButton(text=c, callback_data=f"buy_{c}") for c in countries]
        markup.add(*buttons)
        
        bot.reply_to(message, "🌍 WhatsApp নম্বরের জন্য দেশ নির্বাচন করুন (ফি: ৳০.৫০ BDT):", reply_markup=markup)

    elif message.text == "👨‍💻 Admin Support":
        bot.reply_to(message, f"যেকোনো প্রয়োজনে যোগাযোগ করুন: {ADMIN_USERNAME}")

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        target_id = int(target_id)
        amount = float(amount)
        
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, target_id))
        conn.commit()
        
        bot.reply_to(message, f"✅ User {target_id} এর অ্যাকাউন্টে ৳{amount} যোগ করা হয়েছে।")
        bot.send_message(target_id, f"🎉 আপনার অ্যাকাউন্টে ৳{amount} BDT যোগ করা হয়েছে!")
    except Exception as e:
        bot.reply_to(message, "ব্যবহারের নিয়ম: `/addbalance <user_id> <amount>`")

print("Bot status: Running successfully with fixed deposit button and message...")
bot.polling(none_stop=True)
