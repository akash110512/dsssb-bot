import os
import random
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

current_question = {}
user_score = {}
wrong_questions = {}

def get_questions():
    if not os.path.exists("questions.csv"):
        return []
    df = pd.read_csv("questions.csv")
    return df.to_dict("records")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send CSV file with MCQ questions.\nThen type /practice")

async def load_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = await update.message.document.get_file()
    await file.download_to_drive("questions.csv")

    df = pd.read_csv("questions.csv")

    await update.message.reply_text(f"{len(df)} questions loaded.\nType /practice")

async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    questions = get_questions()

    if not questions:
        await update.message.reply_text("Please send CSV file first.")
        return

    user = update.effective_user.id
    q = random.choice(questions)

    current_question[user] = q

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

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.id
    choice = query.data

    if user not in current_question:
        return

    q = current_question[user]

    if user not in user_score:
        user_score[user] = 0

    if choice == q["Answer"]:
        user_score[user] += 1
        msg = "✅ Correct"
    else:
        msg = f"❌ Wrong\nCorrect answer: {q['Answer']}"

        if user not in wrong_questions:
            wrong_questions[user] = []

        wrong_questions[user].append(q)

    msg += f"\n\nScore: {user_score[user]}"
    msg += "\n\nType /practice"

    await query.edit_message_text(msg)

async def wrong(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in wrong_questions or not wrong_questions[user]:
        await update.message.reply_text("No wrong questions yet.")
        return

    q = random.choice(wrong_questions[user])
    current_question[user] = q

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

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("practice", practice))
app.add_handler(CommandHandler("wrong", wrong))
app.add_handler(MessageHandler(filters.Document.ALL, load_csv))
app.add_handler(CallbackQueryHandler(answer))

app.run_polling()
