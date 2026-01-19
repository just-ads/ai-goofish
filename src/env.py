import os
from dotenv import load_dotenv

from src.utils.logger import logger

load_dotenv('data/.env')

# 数据储存配置
SECRET_KEY_FILE = 'data/secret_key.txt'
STATE_FILE = "data/goofish_state.json"
TASKS_FILE = "data/tasks.json"
APP_CONFIG_FILE = "data/app.config"
AI_CONFIG_FILE = "data/ai.config"
NOTIFIER_CONFIG_FILE = "data/notifier.config"
IMAGE_SAVE_DIR = "data/images"
RESULT_DIR = "data/results"

# 服务器配置
WEB_USERNAME = os.getenv("WEB_USERNAME", 'admin')
WEB_PASSWORD = os.getenv("WEB_PASSWORD", 'admin')
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
SERVER_PORT = 8000
MAX_CONCURRENT_TASKS = 3

try:
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
except Exception as e:
    logger.error("配置加载过程中发生错误: {}", e)
