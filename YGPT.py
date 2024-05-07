import requests
import logging
import http
from config import FOLDER_ID, TEMPERATURE, MODEL_NAME, MAX_MODEL_TOKENS, GPT_URL, COUNT_GPT_URL, LOGS_PATH
from utils import get_creds

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS_PATH, level=logging.ERROR,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")


def count_tokens_in_dialogue(messages: list) -> int:
    headers = {
        'Authorization': f'Bearer {get_creds()}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{MODEL_NAME}/latest",
        "maxTokens": MAX_MODEL_TOKENS,
        "messages": []
    }

    for row in messages:  # Меняет ключ "content" на "text" в словарях списка для корректного запроса
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )

    return len(
        requests.post(
            url=COUNT_GPT_URL,
            json=data,
            headers=headers
        ).json()["tokens"]
    )


def ask_gpt(messages) -> (bool, str):
    url = f"{GPT_URL}"
    headers = {
        "Authorization": f"Bearer {get_creds()}",
        "Content-Type": "application/json"
    }
    data = {

        "modelUri": f"gpt://{FOLDER_ID}/{MODEL_NAME}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": TEMPERATURE,
            "maxTokens": f"{MAX_MODEL_TOKENS}"
        },
        "messages": messages
    }

    try:
        response = requests.post(url=url, headers=headers, json=data)
        if response.status_code != http.HTTPStatus.OK:
            logging.debug(f'Response {response.json()} Status code: {response.status_code} Message {response.text}')
            result = f'Status code: {response.status_code}. смотри в логи'
            return False, result
        result = response.json()["choices"][0]["message"]["content"]
        logging.info(f'Request: {response.request.url}\n'
                     f'Response {response.status_code}\n'
                     f'Response Body {response.text}\n'
                     f'Processed Result: {result}')
    except Exception as e:
        logging.error(f'Am unexpected error occures: {e}')
        result = 'Произошла ошибка смотри в логах'
        return False, result

    return True, result
