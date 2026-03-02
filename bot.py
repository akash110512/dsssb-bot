import os
import random
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

questions = []
user_data = {}
leaderboard = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send a CSV file OR paste CSV text.\nThen type /practice"
    )

# LOAD CSV FILE
async def load_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global questions

    file = await update.message.document.get_file()
    await file.download_to_drive("questions.csv")

    df = pd.read_csv("questions.csv")

    df["Answer"] = df["Answer"].astype(str).str.strip().str.upper()

    questions = df.to_dict("records")

    await update.message.reply_text(f"{len(questions)} questions loaded.\nType /practice")


# LOAD CSV TEXT
async def load_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global questions

    text = update.message.text

    if "Question" not in text:
        return

    from io import StringIO

    df = pd.read_csv(StringIO(text))

    df["Answer"] = df["Answer"].astype(str).str.strip().str.upper()

    questions = df.to_dict("records")

    await update.message.reply_text(f"{len(questions)} questions loaded.\nType /practice")


# START PRACTICE
async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not questions:
        await update.message.reply_text("Please send CSV first.")
        return

    user = update.effective_user.id
    name = update.effective_user.first_name

    user_data[user] = {
        "name": name,
        "remaining": questions.copy(),
        "score": 0,
        "wrong": []
    }

    await send_question(update, context, user)


# SEND QUESTION
async def send_question(update, context, user):

    data = user_data[user]

    if not data["remaining"]:
        leaderboard[data["name"]] = data["score"]

        await context.bot.send_message(
            chat_id=user,
            text=f"🏁 Test Finished!\nScore: {data['score']}\n\nType /wrong to retry wrong questions\nType /leaderboard"
        )
        return

    q = random.choice(data["remaining"])
    data["remaining"].remove(q)

    data["current"] = q

    keyboard = [
        [InlineKeyboardButton("A", callback_data="A"),
         InlineKeyboardButton("B", callback_data="B")],
        [InlineKeyboardButton("C", callback_data="C"),
         InlineKeyboardButton("D", callback_data="D")]
    ]

    text = (
        f"{q['Question']}\n\n"
        f"A. {q['Option A']}\n"
        f"B. {q['Option B']}\n"
        f"C. {q['Option C']}\n"
        f"D. {q['Option D']}"
    )

    await context.bot.send_message(
        chat_id=user,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ANSWER HANDLER
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.id

    data = user_data[user]
    q = data["current"]

    choice = query.data
    correct = str(q["Answer"]).strip().upper()

    if choice == correct:

        data["score"] += 1
        msg = f"✅ Correct\nScore: {data['score']}"

    else:

        msg = f"❌ Wrong\nCorrect answer: {correct}\nScore: {data['score']}"
        data["wrong"].append(q)

    await context.bot.send_message(
        chat_id=user,
        text=msg
    )

    await send_question(update, context, user)


# WRONG PRACTICE
async def wrong(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in user_data or not user_data[user]["wrong"]:
        await update.message.reply_text("No wrong questions.")
        return

    user_data[user]["remaining"] = user_data[user]["wrong"].copy()
    user_data[user]["wrong"] = []

    await send_question(update, context, user)


# LEADERBOARD
async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not leaderboard:
        await update.message.reply_text("No scores yet.")
        return

    text = "🏆 Leaderboard\n\n"

    sorted_scores = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    for i, (name, score) in enumerate(sorted_scores[:10], start=1):
        text += f"{i}. {name} — {score}\n"

    await update.message.reply_text(text)


# MAIN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("practice", practice))
app.add_handler(CommandHandler("wrong", wrong))
app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))

app.add_handler(MessageHandler(filters.Document.ALL, load_csv))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, load_text))

app.add_handler(CallbackQueryHandler(answer))

app.run_polling()
