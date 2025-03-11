import os
import telebot
import datetime
import json
import warnings
from dotenv import load_dotenv
warnings.filterwarnings("ignore", category=UserWarning, module='datetime')
load_dotenv(dotenv_path="path/.env")

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
    "Здравствуйте! Я бот для сна.\n\n"
    "Вот команды, которые я понимаю:\n"
    f"/{START_COMMAND} или /{HEY_COMMAND} - начать работу со мной.\n"
    f"/{SLEEP_COMMAND} - сказать мне, что Вы спите.\n"
    f"/{WAKE_COMMAND} - сказать мне, что Вы проснулись.\n"
    f"/{QUALITY_COMMAND} - записать данные о качестве Вашего сна.\n"
    f"/{NOTES_COMMAND} - записать заметку о сессии сна.\n"
    f"/{VIEW_RECORDS_COMMAND} - посмотреть ваши записи сна.\n"
    f"/{VIEW_LAST_RECORD_COMMAND} - посмотреть последнюю запись сна.\n"
    f"/{STOP_COMMAND} - остановить работу со мной.\n\n"
)
SLEEP_RESPONSE = 'Спокойной ночи! Не забудьте сообщить мне, когда проснетесь командой /wake'
NO_SLEEP_RECORD = 'Вы еще не сообщили, когда легли спать. Используйте /sleep перед /wake.'
WAKE_RESPONSE = 'Доброе утро!☀️ {duration_message}. Не забудьте оценить качество сна командой /quality и оставить заметку командой /notes'
QUALITY_PROMPT = 'Введите оценку сна от 0 до 10:'
QUALITY_INVALID = 'Пожалуйста, введите число от 0 до 10.'
QUALITY_NOT_DIGIT = 'По-моему, это не цифры. Пожалуйста, введите число от 0 до 10.'
QUALITY_THANKS = 'Спасибо за оценку качества сна! Воспользуйтесь /notes, чтобы записать заметку про этот сон.'
NOTES_PROMPT = 'Введите заметку о вашей сессии сна:'
NOTES_THANKS = 'Заметка успешно сохранена! Воспользуйтесь /view_last_record, чтобы посмотреть последнюю запись или /view_records, чтобы посмортеть все записи.'
NO_RECORDS = 'У вас пока нет записей сна.'
STOP_RESPONSE = 'Спасибо за использование бота для сна. До встречи!'

THE_BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(THE_BOT_TOKEN)

user_data = {}


DATA_FILE = "sleep_data.json"


def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            user_data = json.load(file)


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(user_data, file, default=str, indent=4)


load_data()

@bot.message_handler(commands=[START_COMMAND, HEY_COMMAND])
def start_command_handler(message):
    bot.reply_to(message, START_TEXT)

@bot.message_handler(commands=[SLEEP_COMMAND])
def sleep_command_handler(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = []

    bed_time = datetime.datetime.now()
    user_data[user_id].append({"bed_time": bed_time, "wake_time": None, "sleep_quality": None, "notes": None, "sleep_duration": None})
    save_data()
    bot.reply_to(message, SLEEP_RESPONSE)
    print(f"Время отхода ко сну (пользователь {user_id}): {bed_time}")

@bot.message_handler(commands=[WAKE_COMMAND])
def wake_command_handler(message):
    user_id = message.chat.id
    if user_id not in user_data or not user_data[user_id] or user_data[user_id][-1]['bed_time'] is None:
        bot.reply_to(message, NO_SLEEP_RECORD)
    else:
        wake_time = datetime.datetime.now()
        user_data[user_id][-1]['wake_time'] = wake_time
        sleep_duration = wake_time - user_data[user_id][-1]['bed_time']
        total_seconds = int(sleep_duration.total_seconds())
        hours_duration = total_seconds // 3600
        minutes_duration = (total_seconds % 3600) // 60
        seconds_duration = total_seconds % 60

        duration_message = "Длительность сна составила: "
        if hours_duration > 0:
            duration_message += f"{hours_duration} часов "
        if minutes_duration > 0:
            duration_message += f"{minutes_duration} минут "
        if seconds_duration > 0 or (hours_duration == 0 and minutes_duration == 0):
            duration_message += f"{seconds_duration} секунд"

        user_data[user_id][-1]['sleep_duration'] = duration_message
        save_data()

        bot.reply_to(message, WAKE_RESPONSE.format(duration_message=duration_message))
        print(f"Время побуждения (пользователь {user_id}): {wake_time}")
        print(f"Время сна (пользователь {user_id}): {duration_message}")

@bot.message_handler(commands=[QUALITY_COMMAND])
def quality_command_handler(message):
    bot.reply_to(message, QUALITY_PROMPT)
    bot.register_next_step_handler(message, get_sleep_quality)

@bot.message_handler(commands=[NOTES_COMMAND])
def notes_command_handler(message):
    bot.reply_to(message, NOTES_PROMPT)
    bot.register_next_step_handler(message, get_notes)

@bot.message_handler(commands=[VIEW_RECORDS_COMMAND])
def view_records_command_handler(message):
    view_records(message)

@bot.message_handler(commands=[VIEW_LAST_RECORD_COMMAND])
def view_last_record_command_handler(message):
    view_last_record(message)

@bot.message_handler(commands=[STOP_COMMAND])
def stop_command_handler(message):
    bot.reply_to(message, STOP_RESPONSE)


def get_sleep_quality(message):
    user_id = message.chat.id
    if user_data[user_id] and user_data[user_id][-1]['wake_time'] is not None:
        if message.text.isdigit():
            sleep_quality = int(message.text)
            if 0 <= sleep_quality <= 10:
                user_data[user_id][-1]['sleep_quality'] = sleep_quality
                save_data()
                bot.reply_to(message, QUALITY_THANKS)
            else:
                bot.reply_to(message, QUALITY_INVALID)
                bot.register_next_step_handler(message, get_sleep_quality)
        else:
            bot.reply_to(message, QUALITY_NOT_DIGIT)
            bot.register_next_step_handler(message, get_sleep_quality)
    else:
        bot.reply_to(message, NO_SLEEP_RECORD)

def get_notes(message):
    user_id = message.chat.id
    if user_data[user_id] and user_data[user_id][-1]['wake_time'] is not None:
        user_data[user_id][-1]['notes'] = message.text
        save_data()
        bot.reply_to(message, NOTES_THANKS)
    else:
        bot.reply_to(message, NO_SLEEP_RECORD)


def view_records(message):
    user_id = message.chat.id
    if user_id in user_data and user_data[user_id]:
        response = "Все ваши записи сна:\n"
        for i, record in enumerate(user_data[user_id], 1):

            bed_time = record['bed_time'].strftime('%Y-%m-%d %H:%M:%S') if record['bed_time'] else 'Не указано'
            wake_time = record['wake_time'].strftime('%Y-%m-%d %H:%M:%S') if record['wake_time'] else 'Не указано'
            sleep_quality = record['sleep_quality'] if record['sleep_quality'] is not None else 'Не указано'
            notes = record['notes'] if record['notes'] else 'Не указано'
            sleep_duration = record['sleep_duration'] if record['sleep_duration'] else 'Не указано'

            response += (
                f"Запись {i}:\n"
                f"Время отхода ко сну: {bed_time}\n"
                f"Время пробуждения: {wake_time}\n"
                f"{sleep_duration}\n"
                f"Качество сна: {sleep_quality}\n"
                f"Заметка: {notes}\n\n"
            )
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, NO_RECORDS)

def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            try:
                user_data = json.load(file)
                print("Данные успешно загружены из файла.")
            except json.JSONDecodeError as e:
                print(f"Ошибка при чтении JSON: {e}")
    else:
        print("Файл данных не найден.")

def view_last_record(message):
    user_id = message.chat.id
    if user_id in user_data and user_data[user_id]:
        record = user_data[user_id][-1]
        bed_time = record['bed_time'].strftime('%Y-%m-%d %H:%M:%S') if record['bed_time'] else 'Не указано'
        wake_time = record['wake_time'].strftime('%Y-%m-%d %H:%M:%S') if record['wake_time'] else 'Не указано'
        sleep_quality = record['sleep_quality'] if record['sleep_quality'] is not None else 'Не указано'
        notes = record['notes'] if record['notes'] else 'Не указано'
        sleep_duration = record['sleep_duration'] if record['sleep_duration'] else 'Не указано'

        response = (
            f"Ваша последняя запись сна:\n"
            f"Время отхода ко сну: {bed_time}\n"
            f"Время пробуждения: {wake_time}\n"
            f"{sleep_duration}\n"
            f"Качество сна: {sleep_quality}\n"
            f"Заметка: {notes}"
        )
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, NO_RECORDS)

try:
    bot.polling()
except Exception as e:
    print(f"Error: {e}")
