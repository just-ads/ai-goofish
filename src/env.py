import os
from dotenv import load_dotenv

from src.utils.logger import logger

load_dotenv()

WEB_USERNAME = os.getenv("WEB_USERNAME", 'admin')
WEB_PASSWORD = os.getenv("WEB_PASSWORD", 'admin')
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
SECRET_KEY_FILE = 'secret_key.txt'
STATE_FILE = "goofish_state.json"
RESULT_FILE = "result.json"
IMAGE_SAVE_DIR = "images"
TASKS_FILE = "tasks.json"
SERVER_PORT = 8000
MAX_CONCURRENT_TASKS = 3

try:
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
except Exception as e:
    logger.error("配置加载过程中发生错误: {}", e)
