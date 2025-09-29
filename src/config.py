import json
import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY_FILE = 'secret_key.txt'
STATE_FILE = "goofish_state.json"
RESULT_FILE = "result.json"
IMAGE_SAVE_DIR = "images"
TASKS_FILE = "tasks.json"

os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

# --- API URL Patterns ---
API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search"
DETAIL_API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail"

# --- User ---
WEB_USERNAME = os.getenv("WEB_USERNAME", 'admin')
WEB_PASSWORD = os.getenv("WEB_PASSWORD", 'admin')
# SECRET_KEY = os.getenv("SECRET_KEY")

# --- Environment Variables ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
OPENAI_PROXY_URL = os.getenv("OPENAI_PROXY_URL")
OPENAI_EXTRA_BODY = os.getenv("OPENAI_EXTRA_BODY")
NTFY_TOPIC_URL = os.getenv("NTFY_TOPIC_URL")
GOTIFY_URL = os.getenv("GOTIFY_URL")
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN")
BARK_URL = os.getenv("BARK_URL")
WX_BOT_URL = os.getenv("WX_BOT_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_METHOD = os.getenv("WEBHOOK_METHOD", "POST").upper()
WEBHOOK_HEADERS = os.getenv("WEBHOOK_HEADERS")
WEBHOOK_CONTENT_TYPE = os.getenv("WEBHOOK_CONTENT_TYPE", "JSON").upper()
WEBHOOK_QUERY_PARAMETERS = os.getenv("WEBHOOK_QUERY_PARAMETERS")
WEBHOOK_BODY = os.getenv("WEBHOOK_BODY")
PCURL_TO_MOBILE = os.getenv("PCURL_TO_MOBILE", "false").lower() == "true"
RUN_HEADLESS = os.getenv("RUN_HEADLESS", "true").lower() != "false"
USE_EDGE = os.getenv("LOGIN_IS_EDGE", "false").lower() == "true"
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
AI_DEBUG_MODE = os.getenv("AI_DEBUG_MODE", "false").lower() == "true"
SKIP_AI_ANALYSIS = os.getenv("SKIP_AI_ANALYSIS", "false").lower() == "true"
SERVER_PORT = 8000
MAX_CONCURRENT_TASKS = 3

try:
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    if OPENAI_EXTRA_BODY:
        OPENAI_EXTRA_BODY = json.loads(OPENAI_EXTRA_BODY)
except ValueError as e:
    print("ERROR:", e)

if not all([OPENAI_BASE_URL, OPENAI_MODEL_NAME]):
    print("警告：未在 .env 文件中完整设置 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。AI相关功能可能无法使用。")
    SKIP_AI_ANALYSIS = True


def get_envs():
    return {
        "OPENAI_BASE_URL": OPENAI_BASE_URL,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "OPENAI_MODEL_NAME": OPENAI_MODEL_NAME,
        "OPENAI_PROXY_URL": OPENAI_PROXY_URL,
    }


def set_envs(updates: dict, env_file=".env"):
    for key, value in updates.items():
        os.environ[key] = value

    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    env_dict = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            env_dict[k] = v

    env_dict.update(updates)

    with open(env_file, "w", encoding="utf-8") as f:
        for k, v in env_dict.items():
            f.write(f"{k}={v}\n")
