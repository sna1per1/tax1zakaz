import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import threading
import time
import sqlite3

# Токен бота
BOT_TOKEN = "7528011013:AAEJgDZPlDX0otvtwq1nD2n5YMxYcWidLQI"

# Состояние бота
bot_faol = True

# Подключение к базе данных SQLite
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если они не существуют
cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date_added TEXT NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY,
    media_type TEXT,
    media_file_id TEXT,
    text TEXT,
    group_ids TEXT,
    date_created TEXT NOT NULL
)''')

conn.commit()

# ID админа (Admin IDlarini yangiladim)
ADMIN_IDS = [7821399237, 7297970875, 52825051]  # О'згартирдим, бу ерда 3 та админ ID

# Список пользователей с правами администратора
admins = ADMIN_IDS  # Endi 3 ta admin ID ishlatilmoqda

# Переменная для хранения рекламы
current_ad = {"media": None, "text": None}

# Запуск бота
bot = telebot.TeleBot(BOT_TOKEN)

# Функция для добавления администратора в базу данных
def add_admin_to_db(user_id):
    cursor.execute('INSERT INTO admins (user_id, date_added) VALUES (?, ?)', (user_id, str(datetime.now())))
    conn.commit()

# Функция для добавления группы в базу данных
def add_group_to_db(group_id):
    cursor.execute('INSERT INTO groups (group_id) VALUES (?)', (group_id,))
    conn.commit()

# Функция для добавления рекламы в базу данных
def save_ad_to_db(media_type, media_file_id, text, group_ids):
    cursor.execute('INSERT INTO ads (media_type, media_file_id, text, group_ids, date_created) VALUES (?, ?, ?, ?, ?)',
                   (media_type, media_file_id, text, ','.join(map(str, group_ids)), str(datetime.now())))
    conn.commit()

# Клавиатура для администратора
def admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("📢 Настроить рекламу"),
        KeyboardButton("⚡ Быстрая отправка"),
        KeyboardButton("🗑️ Удалить рекламу"),
        KeyboardButton("⏰ Время отправки рекламы"),
        KeyboardButton("➕ Добавить администратора"),
        KeyboardButton("➕ Добавить группу")
    )
    return keyboard

# Клавиатура для выбора времени отправки рекламы
def time_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("1 час"),
        KeyboardButton("2 часа"),
        KeyboardButton("3 часа"),
        KeyboardButton("4 часа"),
        KeyboardButton("5 часов")
    )
    return keyboard

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in admins:
        bot.send_message(message.chat.id, "Привет, админ! Выберите действие:", reply_markup=admin_keyboard())
    else:
        bot.send_message(message.chat.id, "Вы не администратор.")

# Обработчик кнопки "Добавить администратора"
@bot.message_handler(func=lambda message: message.text == "➕ Добавить администратора")
def add_admin(message):
    if message.from_user.id in admins:
        bot.send_message(message.chat.id, "Введите айди администратора:")
        bot.register_next_step_handler(message, check_user_id)
    else:
        bot.send_message(message.chat.id, "У вас нет прав на использование этой функции.")

# Функция проверки ID и добавления администратора
def check_user_id(message):
    try:
        user_id = int(message.text)
        if user_id not in admins:
            admins.append(user_id)
            add_admin_to_db(user_id)
            bot.send_message(user_id, "Вы стали администратором! Теперь у вас есть все права.")
            bot.send_message(message.chat.id, f"Пользователь с ID {user_id} теперь администратор.")
        else:
            bot.send_message(message.chat.id, "Этот пользователь уже администратор.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный ID.")

# Обработчик кнопки "Добавить группу"
@bot.message_handler(func=lambda message: message.text == "➕ Добавить группу")
def add_group(message):
    if message.from_user.id in admins:
        bot.send_message(message.chat.id, "Введите ID группы для добавления:")
        bot.register_next_step_handler(message, receive_group_id)
    else:
        bot.send_message(message.chat.id, "У вас нет прав на использование этой функции.")

# Обработчик получения ID группы
def receive_group_id(message):
    try:
        group_id = int(message.text)
        add_group_to_db(group_id)
        bot.send_message(message.chat.id, f"Группа с ID {group_id} успешно добавлена!")
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректный ID группы.")

# Обработчик кнопки "Настроить рекламу"
@bot.message_handler(func=lambda message: message.text == "📢 Настроить рекламу")
def setup_ad(message):
    if message.from_user.id in admins:
        bot.send_message(message.chat.id, "Отправьте медиа файл (фото, видео, аудио).")
        bot.register_next_step_handler(message, receive_media)

# Обработчик получения медиа
def receive_media(message):
    if message.content_type in ['photo', 'video', 'audio']:
        current_ad["media"] = message
        bot.send_message(message.chat.id, "Теперь отправьте текст для рекламы.")
        bot.register_next_step_handler(message, receive_text)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте медиа файл.")
        bot.register_next_step_handler(message, receive_media)

# Обработчик получения текста для рекламы
def receive_text(message):
    current_ad["text"] = message.text
    bot.send_message(message.chat.id, "Реклама настроена!")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=admin_keyboard())

    # Сохранение рекламы в базе данных
    save_ad_to_db(message.content_type, message.file_id if message.content_type != 'text' else None, current_ad["text"], [group[0] for group in cursor.execute('SELECT group_id FROM groups').fetchall()])

# Обработчик кнопки "Быстрая отправка"
@bot.message_handler(func=lambda message: message.text == "⚡ Быстрая отправка")
def quick_send(message):
    if message.from_user.id in admins:
        if current_ad["media"] and current_ad["text"]:
            media = current_ad["media"]
            text = current_ad["text"]
            for group_id in [group[0] for group in cursor.execute('SELECT group_id FROM groups').fetchall()]:
                try:
                    if media.content_type == 'photo':
                        bot.send_photo(group_id, media.photo[0].file_id, caption=text)
                    elif media.content_type == 'video':
                        bot.send_video(group_id, media.video.file_id, caption=text)
                    elif media.content_type == 'audio':
                        bot.send_audio(group_id, media.audio.file_id, caption=text)
                except Exception as e:
                    print(f"Ошибка при отправке в группу {group_id}: {e}")
                    continue  # Переходим к следующей группе
            bot.send_message(message.chat.id, "Реклама успешно отправлена!")
        else:
            bot.send_message(message.chat.id, "Реклама не настроена. Пожалуйста, сначала настройте рекламу.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав на использование этой функции.")

# Обработчик кнопки "Удалить рекламу"
@bot.message_handler(func=lambda message: message.text == "🗑️ Удалить рекламу")
def delete_ad(message):
    if message.from_user.id in admins:
        current_ad["media"] = None
        current_ad["text"] = None
        bot.send_message(message.chat.id, "Реклама удалена!")
    else:
        bot.send_message(message.chat.id, "У вас нет прав на использование этой функции.")

# Обработчик кнопки "Время отправки рекламы"
@bot.message_handler(func=lambda message: message.text == "⏰ Время отправки рекламы")
def set_time(message):
    if message.from_user.id in admins:
        bot.send_message(message.chat.id, "Выберите интервал времени:", reply_markup=time_keyboard())
    else:
        bot.send_message(message.chat.id, "У вас нет прав на использование этой функции.")

# Обработчик выбора времени отправки рекламы
@bot.message_handler(func=lambda message: message.text in ["1 час", "2 часа", "3 часа", "4 часа", "5 часов"])
def set_time_interval(message):
    if message.from_user.id in admins:
        time_interval = message.text
        bot.send_message(message.chat.id, f"Реклама будет отправляться каждые {time_interval}.")
        interval_in_hours = int(time_interval.split()[0])
        threading.Thread(target=send_ad_periodically, args=(interval_in_hours,)).start()
    else:
        bot.send_message(message.chat.id, "У вас нет прав на использование этой функции.")

# Функция для отправки рекламы периодически
def send_ad_periodically(interval_in_hours):
    while bot_faol:
        if current_ad["media"] and current_ad["text"]:
            media = current_ad["media"]
            text = current_ad["text"]
            for group_id in [group[0] for group in cursor.execute('SELECT group_id FROM groups').fetchall()]:
                try:
                    if media.content_type == 'photo':
                        bot.send_photo(group_id, media.photo[0].file_id, caption=text)
                    elif media.content_type == 'video':
                        bot.send_video(group_id, media.video.file_id, caption=text)
                    elif media.content_type == 'audio':
                        bot.send_audio(group_id, media.audio.file_id, caption=text)
                except Exception as e:
                    print(f"Ошибка при отправке в группу {group_id}: {e}")
                    continue  # Переходим к следующей группе
        time.sleep(interval_in_hours * 3600)  # Преобразуем в секунды

# Запуск бота
bot.polling(none_stop=True)
