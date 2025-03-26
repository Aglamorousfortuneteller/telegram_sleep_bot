import os
import telebot
import datetime
import warnings
from dotenv import load_dotenv
from database import init_db, get_connection

init_db()
warnings.filterwarnings("ignore", category=UserWarning, module='datetime')

load_dotenv(".env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

START_COMMAND = 'start'
HEY_COMMAND = 'hey'
SLEEP_COMMAND = 'sleep'
WAKE_COMMAND = 'wake'
QUALITY_COMMAND = 'quality'
NOTES_COMMAND = 'notes'
VIEW_RECORDS_COMMAND = 'view_records'
VIEW_LAST_RECORD_COMMAND = 'view_last_record'
STOP_COMMAND = 'stop'

START_TEXT = (
    "Hello! I'm your sleep tracking bot. \U0001F62B\n\n"
    "Here are the commands I understand:\n"
    f"/{START_COMMAND} or /{HEY_COMMAND} – start using the bot.\n"
    f"/{SLEEP_COMMAND} – let me know when you're going to sleep.\n"
    f"/{WAKE_COMMAND} – let me know when you woke up.\n"
    f"/{QUALITY_COMMAND} – rate the quality of your sleep.\n"
    f"/{NOTES_COMMAND} – add a note about your sleep session.\n"
    f"/{VIEW_RECORDS_COMMAND} – view all your sleep records.\n"
    f"/{VIEW_LAST_RECORD_COMMAND} – view your most recent sleep record.\n"
    f"/{STOP_COMMAND} – stop using the bot.\n"
)

SLEEP_RESPONSE = "Good night! \U0001F319 Don't forget to use /wake when you wake up."
NO_SLEEP_RECORD = "You haven't told me when you went to sleep. Use /sleep before /wake."
WAKE_RESPONSE = "Good morning! ☀️ {duration_message} Don't forget to rate your sleep with /quality and add a note with /notes."
QUALITY_PROMPT = "Enter your sleep quality rating from 0 to 10:"
QUALITY_INVALID = "Please enter a number between 0 and 10."
QUALITY_NOT_DIGIT = "That doesn't look like a number. Please enter a number from 0 to 10."
QUALITY_THANKS = "Thanks for rating your sleep! Use /notes to add a note about it."
NOTES_PROMPT = "Please enter a note about your sleep session:"
NOTES_THANKS = "Note saved! You can use /view_last_record to view your last record or /view_records to view all."
NO_RECORDS = "You don't have any sleep records yet."
STOP_RESPONSE = "Thank you for using the sleep bot. See you later!"

@bot.message_handler(commands=[START_COMMAND, HEY_COMMAND])
def start_command_handler(message):
    bot.reply_to(message, START_TEXT)

@bot.message_handler(commands=[SLEEP_COMMAND])
def sleep_command_handler(message):
    user_id = message.chat.id
    name = message.chat.first_name or "Unknown"
    bed_time = datetime.datetime.now()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user_id, name))
    cursor.execute("INSERT INTO sleep_records (user_id, sleep_time) VALUES (?, ?)", (user_id, bed_time))
    conn.commit()
    conn.close()
    bot.reply_to(message, SLEEP_RESPONSE)

@bot.message_handler(commands=[WAKE_COMMAND])
def wake_command_handler(message):
    user_id = message.chat.id
    wake_time = datetime.datetime.now()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sleep_time FROM sleep_records 
        WHERE user_id = ? AND wake_time IS NULL 
        ORDER BY sleep_time DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    if not row:
        bot.reply_to(message, NO_SLEEP_RECORD)
        return
    record_id, bed_time = row
    sleep_duration = wake_time - datetime.datetime.fromisoformat(bed_time)
    cursor.execute("UPDATE sleep_records SET wake_time = ? WHERE id = ?", (wake_time, record_id))
    conn.commit()
    conn.close()
    h, m, s = sleep_duration.seconds // 3600, (sleep_duration.seconds % 3600) // 60, sleep_duration.seconds % 60
    duration_message = f"Sleep duration: {h}h {m}min {s}sec"
    bot.reply_to(message, WAKE_RESPONSE.format(duration_message=duration_message))

@bot.message_handler(commands=[QUALITY_COMMAND])
def quality_command_handler(message):
    bot.reply_to(message, QUALITY_PROMPT)
    bot.register_next_step_handler(message, get_sleep_quality)

def get_sleep_quality(message):
    user_id = message.chat.id
    text = message.text.strip()
    if not text.isdigit():
        bot.reply_to(message, QUALITY_NOT_DIGIT)
        bot.register_next_step_handler(message, get_sleep_quality)
        return
    quality = int(text)
    if not 0 <= quality <= 10:
        bot.reply_to(message, QUALITY_INVALID)
        bot.register_next_step_handler(message, get_sleep_quality)
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM sleep_records
        WHERE user_id = ? AND wake_time IS NOT NULL AND sleep_quality IS NULL
        ORDER BY sleep_time DESC LIMIT 1
    """, (user_id,))
    record = cursor.fetchone()
    if not record:
        bot.reply_to(message, NO_SLEEP_RECORD)
    else:
        cursor.execute("UPDATE sleep_records SET sleep_quality = ? WHERE id = ?", (quality, record[0]))
        conn.commit()
        bot.reply_to(message, QUALITY_THANKS)
    conn.close()

@bot.message_handler(commands=[NOTES_COMMAND])
def notes_command_handler(message):
    bot.reply_to(message, NOTES_PROMPT)
    bot.register_next_step_handler(message, get_notes)

def get_notes(message):
    user_id = message.chat.id
    text = message.text.strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM sleep_records
        WHERE user_id = ? AND wake_time IS NOT NULL
        ORDER BY sleep_time DESC LIMIT 1
    """, (user_id,))
    record = cursor.fetchone()
    if not record:
        bot.reply_to(message, NO_SLEEP_RECORD)
    else:
        cursor.execute("INSERT INTO notes (text, sleep_record_id) VALUES (?, ?)", (text, record[0]))
        conn.commit()
        bot.reply_to(message, NOTES_THANKS)
    conn.close()

@bot.message_handler(commands=[VIEW_RECORDS_COMMAND])
def view_records_command_handler(message):
    user_id = message.chat.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sleep_time, wake_time, sleep_quality FROM sleep_records
        WHERE user_id = ?
        ORDER BY sleep_time DESC
    """, (user_id,))
    records = cursor.fetchall()
    if not records:
        bot.reply_to(message, NO_RECORDS)
        conn.close()
        return
    response = "Your sleep records:\n"
    for i, (record_id, bed_time, wake_time, quality) in enumerate(records, 1):
        cursor.execute("SELECT text FROM notes WHERE sleep_record_id = ?", (record_id,))
        notes = cursor.fetchall()
        notes_text = "\n".join(f"- {n[0]}" for n in notes) if notes else "No notes"
        duration_str = "Unknown"
        if bed_time and wake_time:
            duration = datetime.datetime.fromisoformat(wake_time) - datetime.datetime.fromisoformat(bed_time)
            h, m, s = duration.seconds // 3600, (duration.seconds % 3600) // 60, duration.seconds % 60
            duration_str = f"{h}h {m}min {s}sec"
        response += (
            f"\nRecord {i}:\n"
            f"🛏️ Sleep time: {bed_time}\n"
            f"⏰ Wake time: {wake_time or '—'}\n"
            f"⌛ Duration: {duration_str}\n"
            f"⭐ Quality: {quality if quality is not None else '—'}\n"
            f"📝 Notes:\n{notes_text}\n"
        )
    conn.close()
    bot.reply_to(message, response)

@bot.message_handler(commands=[VIEW_LAST_RECORD_COMMAND])
def view_last_record_command_handler(message):
    user_id = message.chat.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sleep_time, wake_time, sleep_quality FROM sleep_records
        WHERE user_id = ?
        ORDER BY sleep_time DESC LIMIT 1
    """, (user_id,))
    record = cursor.fetchone()
    if not record:
        bot.reply_to(message, NO_RECORDS)
        conn.close()
        return
    record_id, bed_time, wake_time, quality = record
    duration_str = "Unknown"
    if bed_time and wake_time:
        duration = datetime.datetime.fromisoformat(wake_time) - datetime.datetime.fromisoformat(bed_time)
        h, m, s = duration.seconds // 3600, (duration.seconds % 3600) // 60, duration.seconds % 60
        duration_str = f"{h}h {m}min {s}sec"
    cursor.execute("SELECT text FROM notes WHERE sleep_record_id = ?", (record_id,))
    notes = cursor.fetchall()
    notes_text = "\n".join(f"- {n[0]}" for n in notes) if notes else "No notes"
    conn.close()
    response = (
        f"🛏️ Sleep time: {bed_time}\n"
        f"⏰ Wake time: {wake_time or '—'}\n"
        f"⌛ Duration: {duration_str}\n"
        f"⭐ Quality: {quality if quality is not None else '—'}\n"
        f"📝 Notes:\n{notes_text}"
    )
    bot.reply_to(message, response)

@bot.message_handler(commands=[STOP_COMMAND])
def stop_command_handler(message):
    bot.reply_to(message, STOP_RESPONSE)

try:
    bot.polling()
except Exception as e:
    print(f"Error: {e}")
