from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, MessageHandler, CommandHandler,
                          filters, ContextTypes, ConversationHandler, CallbackQueryHandler)
import os, base64

# --- CONFIGURATION ---
BOT_TOKEN = "8619557293:AAG6IbW52dZfL9adLxlWZM9vBOvuXUORfTM"
ADMIN_ID = 8411839754  # Aapki Chat ID
all_users = set()      # Users ki list save karne ke liye

ASK_FESTIVAL, ASK_NAME, ASK_PHOTO_CHOICE, ASK_PHOTO = range(4)
user_sessions = {}

FESTIVALS = {
    "birthday": {"name": "🎂 Birthday", "message": "Happy Birthday", "bg": "linear-gradient(135deg, #1a1a2e, #16213e)", "confetti": ["#ffd700","#ff6b6b","#4ecdc4","#ff0080"], "emoji": "🎂🎉🎊🎁🎈", "notes": [261.63,261.63,293.66,261.63,349.23,329.63], "dur": [0.4,0.2,0.6,0.6,0.6,1.2]},
    "holi": {"name": "🎨 Holi", "message": "Happy Holi", "bg": "linear-gradient(135deg, #ff9966, #ff5e62)", "confetti": ["#ff0000","#00ff00","#0000ff","#ffff00"], "emoji": "🎨🌈🔫✨🍧", "notes": [392, 392, 440, 392, 523, 493], "dur": [0.3, 0.3, 0.3, 0.6, 0.3, 1.5]},
    "match": {"name": "🏏 Match Jita", "message": "Mubarak Ho! Match Jeet Gaye", "bg": "linear-gradient(135deg, #00b09b, #96c93d)", "confetti": ["#ffffff","#0000ff","#ff0000"], "emoji": "🏏🏆🥇🇮🇳🔥", "notes": [523, 659, 783, 1046], "dur": [0.3,0.3,0.6,1.5]}
}

# --- ADMIN PANEL FUNCTIONS ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Users List", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")]
    ]
    await update.message.reply_text("🛠 *Admin Panel*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID: return
    await query.answer()
    if query.data == "admin_stats":
        await query.edit_message_text(f"📊 *Total Users:* {len(all_users)}", parse_mode="Markdown")
    elif query.data == "admin_users":
        user_list = "\n".join([str(uid) for uid in all_users]) if all_users else "No users."
        await query.edit_message_text(f"👥 *User IDs:*\n{user_list}", parse_mode="Markdown")
    elif query.data == "admin_broadcast":
        await query.edit_message_text("📢 Sabko message bhejne ke liye likhen:\n`/send [Message]`")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Message likhen!")
        return
    count = 0
    for uid in list(all_users):
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 *Notification:*\n\n{msg}", parse_mode="Markdown")
            count += 1
        except: pass
    await update.message.reply_text(f"✅ {count} users ko bhej diya gaya.")

# --- MAIN BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_users.add(update.effective_user.id)
    keyboard = [[InlineKeyboardButton(v["name"], callback_data=k)] for k, v in FESTIVALS.items()]
    await update.message.reply_text("🎊 *Created by Aman*\n\nChoose kijiye:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ASK_FESTIVAL

async def festival_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_sessions[query.from_user.id] = {"type": query.data}
    await query.edit_message_text("✍️ Naam bataiye:")
    return ASK_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id]["name"] = update.message.text
    keyboard = [[InlineKeyboardButton("✅ Yes", callback_data="yes"), InlineKeyboardButton("❌ No", callback_data="no")]]
    await update.message.reply_text("📸 Photos add karni hain?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_PHOTO_CHOICE

async def photo_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "yes":
        user_sessions[user_id]["photos"] = []
        await query.edit_message_text("🖼️ Photos bhejiye (Max 50). Jab ho jaye to /done likhen.")
        return ASK_PHOTO
    else:
        user_sessions[user_id]["photos"] = []
        await create_page(update, context)
        return ConversationHandler.END

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if "photos" not in user_sessions[user_id]: return
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()
    user_sessions[user_id]["photos"].append(base64.b64encode(photo_bytes).decode('utf-8'))
    await update.message.reply_text(f"✅ {len(user_sessions[user_id]['photos'])} photo mili! /done likhen.")
    return ASK_PHOTO

async def create_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_sessions.get(user_id)
    if not data: return
    fest = FESTIVALS[data["type"]]
    name = data["name"]
    photos = data.get("photos", [])
    
    photos_js = "[" + ",".join([f'"{p}"' for p in photos]) + "]" if photos else "[]"
    
    html = f"""<!DOCTYPE html><html><head><title>Happy {fest['name']}</title>
    <style>body{{background:{fest['bg']}; color:#fff; text-align:center; font-family:Arial;}}</style>
    </head><body><h1>{fest['message']} {name}! {fest['emoji']}</h1>
    <script>const photos = {photos_js}; console.log("Celebrate!");</script></body></html>"""

    filename = f"celebration_{name}.html"
    with open(filename, "w", encoding="utf-8") as f: f.write(html)
    with open(filename, "rb") as f:
        await context.bot.send_document(chat_id=user_id, document=f, filename=filename, caption="🎊 Aapki website!")
    user_sessions.pop(user_id, None)

# --- DEPLOYMENT ---
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("send", broadcast_handler))
app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_FESTIVAL: [CallbackQueryHandler(festival_chosen)],
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        ASK_PHOTO_CHOICE: [CallbackQueryHandler(photo_choice)],
        ASK_PHOTO: [MessageHandler(filters.PHOTO, handle_photo), CommandHandler("done", create_page)]
    },
    fallbacks=[CommandHandler("start", start)]
)
app.add_handler(conv)
app.run_polling()
