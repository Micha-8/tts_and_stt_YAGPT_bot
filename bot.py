import telebot
from telebot.types import Message
import math

from speechkit import speech_to_text, text_to_speech
from YGPT import ask_gpt, count_tokens_in_dialogue
from config import MAX_USERS, MAX_SESSIONS, MAX_USER_STT_BLOCKS, WARNING_STT_BLOCKS, MAX_SECONDS_FOR_AUDIO, \
    SECONDS_PER_ONE_BLOCK, MAX_TEXT_LENGTH, MAX_MODEL_TOKENS, MAX_TOKENS_PER_SESSION, MAX_SYMBOLS_PER_USER, BOT_TOKEN, \
    WARNING_SYMBOLS_PER_USER
from info import commands
from utils import create_keyboard
import db

bot = telebot.TeleBot(BOT_TOKEN)

db.create_db()
db.create_table()

help_commands_send = '\n'.join(commands.values())


@bot.message_handler(commands=['start'])
def start(message: Message):
    if not db.is_user_in_db(message.from_user.id):
        all_users = db.get_all_users_data()
        if len(all_users) < MAX_USERS:
            db.add_new_user(message.from_user.id)
        else:
            bot.send_message(
                message.from_user.id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return
    bot.send_message(message.from_user.id, "Привет! Я могу сгенерировать пост для соцсетей по словестному описанию.",
                     reply_markup=create_keyboard(['/start', '/help', '/voice_task', '/text_task']))


@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, f'<b>Список команд:</b>\n'
                                      f'{help_commands_send}',
                     parse_mode='HTML',
                     reply_markup=create_keyboard(['/start', '/help', '/voice_task', '/text_task'])
                     )


@bot.message_handler(commands=['voice_task'])
def start_voice_task(message: Message):
    if not db.is_user_in_db(message.from_user.id):
        all_users = db.get_all_users_data()
        if len(all_users) < MAX_USERS:
            db.add_new_user(message.from_user.id)
        else:
            bot.send_message(
                message.from_user.id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return

    blocks = db.get_user_data(message.from_user.id)["stt_blocks"]
    if blocks > MAX_USER_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя закончились аудио блоки, ты не сможешь воспользоваться ботом')
        return

    if blocks > WARNING_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя осталось меньше 3 блоков аудио')

    sessions = db.get_user_data(message.from_user.id)["sessions"]
    if sessions > MAX_SESSIONS:
        bot.send_message(message.from_user.id, "Ты потратил все свои сессии, ты не сможешь воспользоваться ботом")
        return
    db.update_row(message.from_user.id, 'sessions', sessions + 1)
    db.update_row(message.from_user.id, "tokens", MAX_TOKENS_PER_SESSION)

    bot.send_message(message.from_user.id, "Отправь вопрос в виде аудио сообщения")
    bot.register_next_step_handler(message, handle_voice)


def handle_voice(message: Message):
    if not message.voice:
        bot.send_message(message.from_user.id, 'Пришли пожалуйста аудио', reply_to_message_id=message.id)
        return

    user_blocks = db.get_user_data(message.from_user.id)["stt_blocks"]
    duration = message.voice.duration

    message_audio_blocks = math.ceil(duration / SECONDS_PER_ONE_BLOCK)
    user_blocks += message_audio_blocks

    if duration > MAX_SECONDS_FOR_AUDIO:
        bot.send_message(message.from_user.id, f"Сообщение не должно быть дольше {MAX_SECONDS_FOR_AUDIO} секунд")
        return

    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    status, text = speech_to_text(file)
    if not status:
        bot.send_message(message.chat.id, text)
        return

    if len(text.split()) > MAX_TEXT_LENGTH:
        bot.send_message(message.chat.id, f"Сообщение не должно содержать больше {MAX_TEXT_LENGTH} слов")
        return

    db.update_row(message.from_user.id, 'message', text)

    messages = [
        {"role": "system", "content": "Ты помощник по различным темам, тебе задали вопрос. "
                                      "Ответь на него максимально понятно"},
        {"role": "user", "content": text}
    ]
    user_tokens = db.get_user_data(message.chat.id)["tokens"]
    tokens_messages = count_tokens_in_dialogue(messages)

    if tokens_messages + MAX_MODEL_TOKENS <= user_tokens:
        status, gpt_answer = ask_gpt(messages)
        if not status:
            bot.send_message(message.chat.id, "Не получилось ответить. Попробуй записать другое описание.")
            bot.send_message(message.chat.id, f"{gpt_answer}")
            return

        symbols = db.get_user_data(message.from_user.id)["tts_symbols"]
        message_symbols = len(message.text)
        symbols += message_symbols

        db.update_row(message.from_user.id, 'tts_symbols', symbols)

        if symbols > MAX_SYMBOLS_PER_USER:
            bot.send_message(message.from_user.id, 'У тебя закончились символы, ты не сможешь воспользоваться ботом')
            return

        status, content = text_to_speech(gpt_answer)
        if status:
            bot.send_voice(message.from_user.id, content,
                           reply_markup=create_keyboard(['/start', '/help', '/voice_task', '/text_task']))
        else:
            bot.send_message(message.from_user.id, content)


@bot.message_handler(commands=['text_task'])
def start_text_task(message: Message):
    if not db.is_user_in_db(message.from_user.id):
        all_users = db.get_all_users_data()
        if len(all_users) < MAX_USERS:
            db.add_new_user(message.from_user.id)
        else:
            bot.send_message(
                message.from_user.id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return

    sessions = db.get_user_data(message.from_user.id)["sessions"]
    if sessions > MAX_SESSIONS:
        bot.send_message(message.from_user.id, "Ты потратил все свои сессии, ты не сможешь воспользоваться ботом")
        return
    db.update_row(message.from_user.id, 'sessions', sessions + 1)
    db.update_row(message.from_user.id, "tokens", MAX_TOKENS_PER_SESSION)
    bot.register_next_step_handler(message, text_question)


def text_question(message: Message):
    db.update_row(message.from_user.id, "tokens", MAX_TOKENS_PER_SESSION)
    user_tokens = db.get_user_data(message.from_user.id)["tokens"]

    messages = [
        {"role": "system", "content": "Ты помощник по различным темам, тебе задали вопрос. "
                                      "Ответь на него максимально понятно"},
        {"role": "user", "content": message.text}
    ]
    tokens_messages = count_tokens_in_dialogue(messages)

    if tokens_messages + MAX_MODEL_TOKENS <= user_tokens:
        status, gpt_answer = ask_gpt(messages)
        if not status:
            bot.send_message(message.chat.id, "Не получилось ответить. Попробуй записать другое описание.")
            bot.send_message(message.chat.id, f"{gpt_answer}")
            return

        user_tokens -= count_tokens_in_dialogue([{"role": "assistant", "content": gpt_answer}])
        db.update_row(message.from_user.id, "tokens", user_tokens)

        bot.send_message(message.from_user.id, gpt_answer,
                         reply_markup=create_keyboard(['/start', '/help', '/voice_task', '/text_task'])\
                         )


@bot.message_handler(commands=["tts"])
def start_tts(message: Message):
    symbols = db.get_user_data(message.from_user.id)["tts_symbols"]
    if symbols > MAX_SYMBOLS_PER_USER:
        bot.send_message(message.from_user.id, 'У тебя закончились символы, ты не сможешь воспользоваться ботом')
        return
    if symbols > WARNING_SYMBOLS_PER_USER:
        bot.send_message(message.from_user.id, 'У тебя осталось меньше 200 символов')

    if not db.is_user_in_db(message.from_user.id):
        if len(db.get_all_users_data()) < MAX_USERS:
            db.add_new_user(message.from_user.id)
        else:
            bot.send_message(
                message.from_user.id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return

    bot.send_message(
        message.from_user.id,
        f"<b>Привет, {message.from_user.first_name}!</b>\n"
        f"Я вижу ты готов озвучить свой текст\n",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, tts_func)


def tts_func(message: Message):
    if message.content_type == 'text':
        symbols = db.get_user_data(message.from_user.id)["tts_symbols"]
        message_symbols = len(message.text)
        symbols += message_symbols

        db.update_row(message.from_user.id, 'message', message.text)
        db.update_row(message.from_user.id, 'tts_symbols', symbols)

        if symbols > MAX_SYMBOLS_PER_USER:
            bot.send_message(message.from_user.id, 'У тебя закончились символы, ты не сможешь воспользоваться ботом')
            return

        status, content = text_to_speech(message.text)
        if status:
            bot.send_voice(message.from_user.id, content, reply_to_message_id=message.id)
        else:
            bot.send_message(message.from_user.id, content)
    else:
        bot.send_message(message.from_user.id, 'Пришли пожалуйста текст', reply_to_message_id=message.id)


@bot.message_handler(commands=["stt"])
def start_stt(message: Message):
    blocks = db.get_user_data(message.from_user.id)["stt_blocks"]
    if blocks > MAX_USER_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя закончились аудио блоки, ты не сможешь воспользоваться ботом')
        return
    if blocks > WARNING_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя осталось меньше 3 блоков аудио')

    if not db.is_user_in_db(message.from_user.id):
        if len(db.get_all_users_data()) < MAX_USERS:
            db.add_new_user(message.from_user.id)
        else:
            bot.send_message(
                message.from_user.id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return

    bot.send_message(
        message.from_user.id,
        f"<b>Привет, {message.from_user.first_name}!</b>\n"
        f"Я вижу ты готов разобрать аудио\n",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, stt_func)


def stt_func(message: Message):
    if not message.voice:
        bot.send_message(message.from_user.id, 'Пришли пожалуйста аудио', reply_to_message_id=message.id)
        return

    user_blocks = db.get_user_data(message.from_user.id)["stt_blocks"]
    duration = message.voice.duration

    message_audio_blocks = math.ceil(duration / SECONDS_PER_ONE_BLOCK)
    user_blocks += message_audio_blocks

    if duration >= MAX_SECONDS_FOR_AUDIO:
        bot.send_message(message.from_user.id, 'Пришли аудио короче 30 секунд')
        return

    if user_blocks >= MAX_USER_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя закончились аудио блоки, ты не сможешь воспользоваться ботом')
        return

    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)

    status, text = speech_to_text(file)

    if status:
        db.update_row(message.from_user.id, 'stt_blocks', user_blocks)
        db.update_row(message.from_user.id, 'message', text)

        bot.send_message(message.from_user.id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(message.from_user.id, text)  # Эти функции просят по тз для отладки


# проект небольшой и не особо чем-то выделяется просто под конец года времени не особо много(но вроде все тз выполнено)

bot.polling()
