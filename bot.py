import os
import random
import pandas as pd
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

questions = []
used_questions = {}
current_question = {}
user_score = {}
wrong_questions = {}
leaderboard = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Welcome to MCQ Practice Bot\n\n"
        "Commands:\n"
        "/practice - Start test\n"
        "/wrong - Retry wrong questions\n"
        "/leaderboard - Top scores\n"
        "/result - Show score\n"
        "/polltest - Quiz poll mode\n\n"
        "Send CSV file or CSV text to load questions."
    )

# LOAD CSV FILE
async def load_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global questions

    file = await update.message.document.get_file()
    await file.download_to_drive("questions.csv")

    df = pd.read_csv("questions.csv")
    questions = df.to_dict("records")

    await update.message.reply_text(
        f"✅ {len(questions)} questions loaded.\nType /practice"
    )

# LOAD CSV TEXT
async def load_csv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global questions

    try:
        text = update.message.text.strip().split("\n")

        if "Question" not in text[0]:
            return

        rows = [row.split(",") for row in text[1:]]

        questions = []

        for r in rows:
            questions.append({
                "Question": r[0],
                "Option A": r[1],
                "Option B": r[2],
                "Option C": r[3],
                "Option D": r[4],
                "Answer": r[5]
            })

        await update.message.reply_text(
            f"✅ {len(questions)} questions loaded from text."
        )

    except:
        pass

# SEND QUESTION
async def send_question(update, context, user):

    if user not in used_questions:
        used_questions[user] = []

    remaining = [q for q in questions if q not in used_questions[user]]

    if not remaining:
        await update.message.reply_text(
            f"🏁 Test Finished!\nScore: {user_score.get(user,0)}"
        )

        leaderboard[user] = user_score.get(user,0)

        await update.message.reply_text(
            "Type /wrong to retry wrong questions\n"
            "Type /leaderboard"
        )
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

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# PRACTICE TEST
async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not questions:
        await update.message.reply_text("Send CSV first.")
        return

    user = update.effective_user.id

    user_score[user] = 0
    used_questions[user] = []
    wrong_questions[user] = []

    await send_question(update, context, user)

# ANSWER HANDLER
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.id
    choice = query.data

    q = current_question[user]

    correct = q["Answer"].strip().upper()

    if choice == correct:

        user_score[user] += 1
        msg = f"✅ Correct\nScore: {user_score[user]}"

    else:

        msg = f"❌ Wrong\nCorrect answer: {correct}\nScore: {user_score[user]}"

        wrong_questions[user].append(q)

    await query.message.reply_text(msg)

    await send_question(query.message, context, user)

# WRONG QUESTIONS
async def wrong(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# RESULT
async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    score = user_score.get(user,0)

    await update.message.reply_text(f"📊 Score: {score}")

# LEADERBOARD
async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not leaderboard:
        await update.message.reply_text("No scores yet.")
        return

    sorted_scores = sorted(
        leaderboard.items(),
        key=lambda x: x[1],
        reverse=True
    )

    text = "🏆 Leaderboard\n\n"

    for i,(u,s) in enumerate(sorted_scores[:10],1):
        text += f"{i}. {s}\n"

    await update.message.reply_text(text)

# POLL QUIZ MODE
async def polltest(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not questions:
        await update.message.reply_text("Upload questions first.")
        return

    q = random.choice(questions)

    options = [
        q["Option A"],
        q["Option B"],
        q["Option C"],
        q["Option D"]
    ]

    correct_index = ["A","B","C","D"].index(q["Answer"])

    await update.message.reply_poll(
        question=q["Question"],
        options=options,
        type="quiz",
        correct_option_id=correct_index,
        is_anonymous=False
    )

# APP
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("practice", practice))
app.add_handler(CommandHandler("wrong", wrong))
app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
app.add_handler(CommandHandler("result", result))
app.add_handler(CommandHandler("polltest", polltest))

app.add_handler(MessageHandler(filters.Document.ALL, load_csv))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, load_csv_text))

app.add_handler(CallbackQueryHandler(answer))

app.run_polling()
