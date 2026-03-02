import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

questions = []
current_question = {}
used_questions = {}
wrong_questions = {}
score = {}
leaderboard = []

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Send CSV text like this:\n\n"
        "Question,Option A,Option B,Option C,Option D,Answer\n"
        "Capital of India?,Mumbai,Delhi,Kolkata,Chennai,B\n\n"
        "/test - start test\n"
        "/wrongtest - practice wrong questions\n"
        "/result - show result\n"
        "/leaderboard - show scores"
    )

# LOAD CSV TEXT
async def load_csv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global questions

    text = update.message.text

    if "Question,Option A" not in text:
        return

    lines = text.split("\n")

    data = []

    for line in lines[1:]:

        parts = line.split(",")

        if len(parts) < 6:
            continue

        q = {
            "Question": parts[0],
            "Option A": parts[1],
            "Option B": parts[2],
            "Option C": parts[3],
            "Option D": parts[4],
            "Answer": parts[5].strip()
        }

        data.append(q)

    questions = data

    await update.message.reply_text(f"{len(questions)} questions loaded.")

# SEND QUESTION
async def send_question(user, message):

    if user not in used_questions:
        used_questions[user] = []

    remaining = [q for q in questions if q not in used_questions[user]]

    if not remaining:
        await message.reply_text("Test finished. Use /result")
        return

    q = random.choice(remaining)

    used_questions[user].append(q)
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

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# START TEST
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if not questions:
        await update.message.reply_text("Send CSV text first.")
        return

    await send_question(user, update.message)

# ANSWER
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.id
    name = query.from_user.first_name

    choice = query.data
    q = current_question[user]

    if user not in score:
        score[user] = 0

    if choice == q["Answer"]:

        score[user] += 1
        msg = "✅ Correct"

    else:

        msg = f"❌ Wrong\nCorrect answer: {q['Answer']}"

        if user not in wrong_questions:
            wrong_questions[user] = []

        wrong_questions[user].append(q)

    msg += f"\nScore: {score[user]}"

    await query.message.reply_text(msg)

    # NEXT QUESTION AUTOMATICALLY
    await send_question(user, query.message)

# WRONG TEST
async def wrongtest(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in wrong_questions or not wrong_questions[user]:
        await update.message.reply_text("No wrong questions.")
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

# RESULT
async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    name = update.effective_user.first_name

    correct = score.get(user, 0)
    wrong = len(wrong_questions.get(user, []))

    total = correct + wrong

    if total == 0:
        await update.message.reply_text("No test taken.")
        return

    accuracy = round((correct / total) * 100, 2)

    leaderboard.append((name, correct))

    msg = (
        f"Result\n\n"
        f"Correct: {correct}\n"
        f"Wrong: {wrong}\n"
        f"Accuracy: {accuracy}%"
    )

    await update.message.reply_text(msg)

# LEADERBOARD
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not leaderboard:
        await update.message.reply_text("No scores yet.")
        return

    top = sorted(leaderboard, key=lambda x: x[1], reverse=True)

    msg = "🏆 Leaderboard\n\n"

    rank = 1

    for name, sc in top[:10]:

        msg += f"{rank}. {name} — {sc}\n"
        rank += 1

    await update.message.reply_text(msg)

# RESET
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    used_questions[user] = []
    wrong_questions[user] = []
    score[user] = 0

    await update.message.reply_text("Test reset.")

# BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("test", test))
app.add_handler(CommandHandler("wrongtest", wrongtest))
app.add_handler(CommandHandler("result", result))
app.add_handler(CommandHandler("leaderboard", show_leaderboard))
app.add_handler(CommandHandler("reset", reset))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, load_csv_text))
app.add_handler(CallbackQueryHandler(answer))

app.run_polling()
