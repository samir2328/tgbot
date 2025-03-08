import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Configuration
TOKEN = "7946382116:AAGnlkHIEFiDqUotoViCKDxtS9s5BwF_-iA"
TELEGRAM_LINK = "https://t.me/CrafterCraft"
BONUS_AMOUNT = 5
WITHDRAWAL_THRESHOLD = 50
DAILY_BONUS = 2

# Temporary in-memory storage
users_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Shows main menu & asks users to join the Telegram group."""
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name

    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "referrals": 0, "claimed_bonus": False, "joined": False, "referred_users": []}

    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id and user_id not in users_data[referrer_id]["referred_users"]:
                users_data[referrer_id]["balance"] += BONUS_AMOUNT
                users_data[referrer_id]["referrals"] += 1
                users_data[referrer_id]["referred_users"].append(user_id)
        except (ValueError, KeyError):
            pass  

    if not users_data[user_id]["joined"]:
        keyboard = [
            [InlineKeyboardButton("📢 Join Telegram Group", url=TELEGRAM_LINK)],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
        ]
        await update.message.reply_text("🚀 Please join our Telegram group before using the bot:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await main_menu(update.message)

async def main_menu(message):
    """Show the main menu with buttons."""
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("🔗 Referral", callback_data="referral")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus"), InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Invite List", callback_data="invite_list"), InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("ℹ How to Earn?", callback_data="earn_info")]
    ]
    await message.reply_text("📋 Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "referrals": 0, "claimed_bonus": False, "joined": False, "referred_users": []}

    if query.data == "check_join":
        users_data[user_id]["joined"] = True
        await query.message.delete()
        await main_menu(query.message)

    elif query.data == "balance":
        balance = users_data[user_id]["balance"]
        await query.edit_message_text(f"💰 Your current balance: ₹{balance}", reply_markup=back_button())

    elif query.data == "referral":
        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(f"🔗 Share this link to earn ₹5 per referral:\n{referral_link}", reply_markup=back_button())

    elif query.data == "daily_bonus":
        if not users_data[user_id]["claimed_bonus"]:
            users_data[user_id]["balance"] += DAILY_BONUS
            users_data[user_id]["claimed_bonus"] = True
            await query.edit_message_text(f"🎁 You have claimed ₹{DAILY_BONUS} as your daily bonus!", reply_markup=back_button())
        else:
            await query.edit_message_text("⚠ You have already claimed your daily bonus today.", reply_markup=back_button())

    elif query.data == "withdraw":
        balance = users_data[user_id]["balance"]
        if balance >= WITHDRAWAL_THRESHOLD:
            users_data[user_id]["balance"] = 0
            await query.edit_message_text("✅ Withdrawal request received! You will be contacted soon.", reply_markup=back_button())
        else:
            await query.edit_message_text(f"❌ You need at least ₹{WITHDRAWAL_THRESHOLD} to withdraw.", reply_markup=back_button())

    elif query.data == "invite_list":
        referred_users = users_data[user_id]["referred_users"]
        if referred_users:
            referred_list = "\n".join([f"👤 User ID: {uid}" for uid in referred_users])
            await query.edit_message_text(f"📜 Your Invite List:\n\n{referred_list}", reply_markup=back_button())
        else:
            await query.edit_message_text("❌ You haven't referred anyone yet.", reply_markup=back_button())

    elif query.data == "leaderboard":
        leaderboard_text = "🏆 **Top Referrers** 🏆\n\n"
        sorted_users = sorted(users_data.items(), key=lambda x: x[1]["referrals"], reverse=True)
        top_users = sorted_users[:5]  

        for rank, (user_id, data) in enumerate(top_users, start=1):
            leaderboard_text += f"🥇 {rank}. User ID: {user_id} - {data['referrals']} Referrals\n"

        if not top_users:
            leaderboard_text += "No referrals yet."

        await query.edit_message_text(leaderboard_text, reply_markup=back_button())

    elif query.data == "earn_info":
        await query.edit_message_text(
            "📢 How to Earn:\n\n"
            "1️⃣ Refer friends and earn ₹5 per referral.\n"
            "2️⃣ Claim your ₹2 daily bonus.\n"
            "3️⃣ Withdraw once you reach ₹50.",
            reply_markup=back_button()
        )

    elif query.data == "back":
        await query.message.delete()
        await main_menu(query.message)

def back_button():
    """Returns a 'Back' button markup."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handles errors and logs them."""
    logger.error(f"Error: {context.error}")

def main():
    """Start the bot using ApplicationBuilder (compatible with latest versions)."""
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
