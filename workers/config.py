import os

redis_url = os.getenv("REDIS_URL", "redis://:200898@localhost:6379")
log_level = os.getenv("LOG_LEVEL", "DEBUG")

# MySQL config
mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_user = os.getenv("MYSQL_USER", "root")
mysql_password = os.getenv("MYSQL_PASSWORD", "password")
mysql_database = os.getenv("MYSQL_DATABASE", "tasks_db")

# API config
api_url = os.getenv("API_URL", "http://localhost:8989")

# Worker config
report_interval = int(os.getenv("REPORT_INTERVAL", "5"))
poll_interval = int(os.getenv("POLL_INTERVAL", "1"))

# Media config
media_path = os.getenv("MEDIA_PATH", os.path.expanduser("~/assets/"))
upload_base_url = os.getenv("UPLOAD_BASE_URL", "http://localhost:8989")
max_upload_size = int(os.getenv("MAX_UPLOAD_SIZE", "524288000"))  # 500MB default


# Task types
queue_list = ["test", "whisper", "index-tts", "voxcpm"]


def get_queue_for_task_type(task_type):
    if task_type == "test":
        return "tasks:test"
    elif task_type == "whisper":
        return "tasks:whisper"
    elif task_type == "index-tts":
        return "tasks:index-tts"
    elif task_type == "voxcpm":
        return "tasks:voxcpm"
    elif task_type:
        return "tasks:" + task_type
    else:
        return "tasks:all"
