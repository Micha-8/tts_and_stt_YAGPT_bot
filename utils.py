import requests
import logging
import time
import json
from config import METADATA_URL, HEADERS_FOR_TOKEN, TOKEN_PATH
from telebot.types import ReplyKeyboardMarkup


def create_keyboard(buttons: list[str]) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


def create_new_token():
    url = METADATA_URL
    headers = HEADERS_FOR_TOKEN
    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()  # вытаскиваем из ответа iam_token
            # добавляем время истечения iam_token к текущему времени
            token_data['expires_at'] = time.time() + token_data['expires_in']
            # записываем iam_token в файл
            with open(TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
            logging.info("Получен новый iam_token")
        else:
            logging.error(f"Ошибка получения iam_token. Статус код: {response.status_code}")
    except Exception as e:
        logging.error(f"Ошибка получения iam_token: {e}")


# чтение iam_token и folder_id из файла
def get_creds():
    try:
        with open(TOKEN_PATH, "r") as f:
            token_data = json.loads(f.read(), strict=False)

        if time.time() >= token_data['expires_in']:
            logging.info("Срок годности iam_token истёк")
            create_new_token()

    except:
        create_new_token()

    with open(TOKEN_PATH, 'r') as f:
        file_data = json.load(f)
        AIM_TOKEN = file_data["access_token"]

    return AIM_TOKEN
