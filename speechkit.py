import requests
import http
import logging

from config import FOLDER_ID, LANG, VOICE, EMOTION, SPEED, URL_TTS, URL_STT, TOPIC
from utils import get_creds


def text_to_speech(message):
    token = get_creds()
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'text': message,
        'lang': LANG,
        'voice': VOICE,
        'emotion': EMOTION,
        'speed': SPEED,
        'folderId': FOLDER_ID,
    }
    url = URL_TTS

    response = requests.post(url=url, headers=headers, data=data)
    if response.status_code == http.HTTPStatus.OK:
        return True, response.content
    else:
        logging.error('Что-то пошло не так при запросе к tts')
        return False, 'Что-то пошло не так'


def speech_to_text(data):
    token = get_creds()

    params = "&".join([
        f"topic={TOPIC}",
        f"folderId={FOLDER_ID}",
        f"lang={LANG}"
    ])

    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.post(
        f"{URL_STT}{params}",
        headers=headers,
        data=data
    )

    decoded_data = response.json()

    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")
    else:
        return False, "При запросе в SpeechKit возникла ошибка"