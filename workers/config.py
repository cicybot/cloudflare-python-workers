import os

redis_url = os.getenv("REDIS_URL", "redis://:200898@localhost:6379")
log_level = os.getenv("LOG_LEVEL", "INFO")

# MySQL config
mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_user = os.getenv("MYSQL_USER", "root")
mysql_password = os.getenv("MYSQL_PASSWORD", "password")
mysql_database = os.getenv("MYSQL_DATABASE", "tasks_db")

# API config
api_url = os.getenv("API_URL", "http://localhost:8989")
