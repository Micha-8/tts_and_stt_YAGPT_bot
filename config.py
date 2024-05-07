import os

from dotenv import load_dotenv

load_dotenv()

METADATA_URL = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"

HEADERS_FOR_TOKEN = {"Metadata-Flavor": "Google"}

URL_STT = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?'

URL_TTS = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

COUNT_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion"

LOGS_PATH = "logs/logs.txt"

TOKEN_PATH = 'token.txt'

TOPIC = 'general'

LANG = 'ru-RU'

VOICE = 'marina'

EMOTION = 'friendly'

SPEED = '1.0'

DB_NAME = "db.sqlite"

DB_TABLE_USERS_NAME = "users_info"

MODEL_NAME = "yandexgpt-lite"

TEMPERATURE = 0.4

MAX_MODEL_TOKENS = 200

MAX_SESSIONS = 20

MAX_TOKENS_PER_SESSION = 1000

MAX_USERS = 4

MAX_USER_STT_BLOCKS = 11

WARNING_STT_BLOCKS = 8

MAX_SECONDS_FOR_AUDIO = 30

SECONDS_PER_ONE_BLOCK = 15

MAX_TEXT_LENGTH = 100

MAX_SYMBOLS_PER_USER = 30000

WARNING_SYMBOLS_PER_USER = 800

FOLDER_ID = os.getenv("folder_id")

ADMINS = os.getenv("admin_id")

BOT_TOKEN = os.getenv("token")